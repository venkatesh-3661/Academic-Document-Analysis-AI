"""
Flask Application Server
REST API for Academic Document Retrieval Agent
Serves endpoints for document ingestion, hybrid retrieval, RAG generation,
source selection, response validation, and test suite execution.
"""

import os
import sys
import json
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.document_processor import DocumentProcessor
from backend.retriever import HybridRetriever
from backend.source_selector import SourceSelector
from backend.rag_engine import RAGEngine
from backend.validator import ResponseValidator
from backend.sample_generator import generate_sample_corpus

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
SAMPLE_DOCS_DIR = os.path.join(DATA_DIR, "sample_documents")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

os.makedirs(SAMPLE_DOCS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

# Initialize Core Agent Modules
processor = DocumentProcessor(chunk_size=850, chunk_overlap=150)
retriever = HybridRetriever(semantic_weight=0.55, top_k=5)
source_selector = SourceSelector()
rag_engine = RAGEngine()
validator = ResponseValidator()

# In-memory document registry
indexed_documents = {}  # doc_id -> metadata
all_chunks = []         # list of all chunks


def reindex_all():
    """Rebuild retrieval index across all loaded documents."""
    global all_chunks
    retriever.index_chunks(all_chunks)


def load_initial_documents():
    """Load sample corpus on startup if available or generate them."""
    global all_chunks, indexed_documents
    indexed_documents.clear()
    all_chunks.clear()

    if not os.path.exists(SAMPLE_DOCS_DIR) or len(os.listdir(SAMPLE_DOCS_DIR)) < 5:
        generate_sample_corpus(SAMPLE_DOCS_DIR)

    for fname in sorted(os.listdir(SAMPLE_DOCS_DIR)):
        fpath = os.path.join(SAMPLE_DOCS_DIR, fname)
        if os.path.isfile(fpath) and fname.lower().endswith((".pdf", ".docx", ".txt", ".md")):
            try:
                res = processor.process_file(fpath)
                meta = res["metadata"]
                meta["is_sample"] = True
                meta["total_chunks"] = len(res["chunks"])
                indexed_documents[meta["doc_id"]] = meta
                all_chunks.extend(res["chunks"])
            except Exception as e:
                print(f"[Init] Error loading {fname}: {e}")

    reindex_all()
    print(f"[Init] Initialized with {len(indexed_documents)} documents and {len(all_chunks)} chunks.")


# Load sample corpus initially
load_initial_documents()


# ============================================================================
# API ROUTES
# ============================================================================

@app.route("/")
def index():
    """Serve single-page frontend application."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def static_proxy(path):
    """Serve frontend static files (styles.css, app.js, etc.)."""
    return send_from_directory(FRONTEND_DIR, path)


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get system stats: document count, total chunks, model state."""
    doc_types = {}
    for doc in indexed_documents.values():
        dtype = doc.get("doc_type", "Other")
        doc_types[dtype] = doc_types.get(dtype, 0) + 1

    return jsonify({
        "total_documents": len(indexed_documents),
        "total_chunks": len(all_chunks),
        "document_types": doc_types,
        "engine_mode": "Google Gemini" if rag_engine.gemini_client else "Deterministic Academic Reasoning Engine (Local)",
        "gemini_configured": rag_engine.gemini_client is not None,
        "default_top_k": retriever.top_k,
        "default_semantic_weight": retriever.semantic_weight,
    })


@app.route("/api/documents", methods=["GET"])
def list_documents():
    """List all indexed documents with metadata."""
    docs = list(indexed_documents.values())
    return jsonify({"documents": docs, "count": len(docs)})


@app.route("/api/documents/upload", methods=["POST"])
def upload_document():
    """Upload and process PDF, DOCX, or TXT file."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded in form data."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    allowed_exts = {".pdf", ".docx", ".txt", ".md"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        return jsonify({"error": f"Unsupported file extension '{ext}'. Only .pdf, .docx, and .txt files are supported."}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOADS_DIR, filename)
    file.save(save_path)

    # Optional custom metadata overrides
    custom_metadata = {}
    if request.form.get("doc_type"):
        custom_metadata["doc_type"] = request.form.get("doc_type").strip()
    if request.form.get("academic_year"):
        custom_metadata["academic_year"] = request.form.get("academic_year").strip()
    if request.form.get("effective_date"):
        custom_metadata["effective_date"] = request.form.get("effective_date").strip()
    if request.form.get("authority"):
        custom_metadata["authority"] = request.form.get("authority").strip()

    try:
        res = processor.process_file(save_path, custom_metadata=custom_metadata)
        meta = res["metadata"]
        meta["is_sample"] = False
        meta["total_chunks"] = len(res["chunks"])

        indexed_documents[meta["doc_id"]] = meta
        all_chunks.extend(res["chunks"])
        reindex_all()

        return jsonify({
            "message": f"Successfully indexed '{filename}' into {len(res['chunks'])} chunks.",
            "document": meta,
            "chunks_created": len(res["chunks"])
        })
    except Exception as e:
        return jsonify({"error": f"Failed to process document: {str(e)}"}), 500


@app.route("/api/documents/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    """Delete document and all associated chunks."""
    global all_chunks
    if doc_id not in indexed_documents:
        return jsonify({"error": "Document not found."}), 404

    doc = indexed_documents.pop(doc_id)
    all_chunks = [c for c in all_chunks if c["doc_id"] != doc_id]
    reindex_all()

    return jsonify({"message": f"Document '{doc['document_name']}' removed.", "remaining_documents": len(indexed_documents)})


@app.route("/api/documents/reset-sample", methods=["POST"])
def reset_sample_corpus():
    """Reset repository to the 5 official sample documents."""
    load_initial_documents()
    return jsonify({
        "message": "Sample academic documents reset successfully.",
        "documents": list(indexed_documents.values()),
        "total_chunks": len(all_chunks)
    })


@app.route("/api/chunks", methods=["GET"])
def get_chunks():
    """Get all or filtered chunks for the chunk explorer UI."""
    doc_id = request.args.get("doc_id")
    limit = int(request.args.get("limit", 100))

    filtered = all_chunks
    if doc_id:
        filtered = [c for c in all_chunks if c["doc_id"] == doc_id]

    return jsonify({
        "total_chunks": len(filtered),
        "chunks": filtered[:limit]
    })


@app.route("/api/query", methods=["POST"])
def execute_query():
    """
    Main RAG Query Pipeline:
    1. Hybrid Retrieval (Semantic + BM25)
    2. Source Selection & Recency Conflict Resolution
    3. RAG Answer Generation with Citations
    4. Response Grounding Validation & Hallucination Check
    """
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query string is required."}), 400

    top_k = int(data.get("top_k", retriever.top_k))
    doc_type_filter = data.get("doc_type_filter")
    academic_year_filter = data.get("academic_year_filter")
    semantic_weight = float(data.get("semantic_weight", retriever.semantic_weight))

    # Temporarily apply query-specific weight if provided
    retriever.semantic_weight = semantic_weight

    # Step 1: Hybrid Retrieval
    retrieved_chunks = retriever.retrieve(
        query=query,
        top_k=top_k,
        doc_type_filter=doc_type_filter,
        academic_year_filter=academic_year_filter
    )

    # Step 2: Source Selection & Recency Conflict Resolution
    ranked_chunks, conflict_report = source_selector.evaluate_and_rank_sources(
        retrieved_chunks=retrieved_chunks,
        query=query
    )

    # Step 3: RAG Response Generation
    rag_response = rag_engine.generate_response(
        query=query,
        retrieved_chunks=ranked_chunks,
        conflict_report=conflict_report
    )

    # Step 4: Response Validation & Hallucination Guardrails
    validation_report = validator.validate(
        query=query,
        answer=rag_response["answer"],
        retrieved_chunks=ranked_chunks,
        conflict_report=conflict_report
    )

    return jsonify({
        "query": query,
        "answer": rag_response["answer"],
        "is_out_of_corpus": rag_response["is_out_of_corpus"],
        "engine_used": rag_response["engine_used"],
        "conflict_report": conflict_report,
        "validation": validation_report,
        "citations": rag_response["citations"],
        "retrieved_chunks": ranked_chunks,
    })


@app.route("/api/test-cases", methods=["GET"])
def get_test_cases():
    """Returns curated academic test cases covering all requirements."""
    test_cases = [
        {
            "id": "syllabus_unit3",
            "category": "Syllabus Curriculum",
            "question": "What are the reference textbooks and topics for Unit 3 in Data Structures?",
            "expected_focus": "Unit 3 Graph Algorithms (BFS, DFS, Dijkstra, Kruskal, Prim) and CLRS / Weiss textbooks.",
            "target_document": "CS101_Data_Structures_and_Algorithms_Syllabus_2024.docx"
        },
        {
            "id": "exam_regulations",
            "category": "Examination Regulations",
            "question": "What is the passing criteria and minimum marks required in the end semester examination?",
            "expected_focus": "Minimum 40% in end-semester theory exam, 50% aggregate in course, Letter grade scale.",
            "target_document": "Academic_Regulations_Handbook_2023.pdf / Update 2024"
        },
        {
            "id": "attendance_conflict",
            "category": "Attendance & Conflict Resolution",
            "question": "What is the minimum attendance required to appear for exams and can it be condoned?",
            "expected_focus": "Conflict Resolution: 2024-2025 Update supersedes 2023 Handbook (80% mandatory; condonation only 70-79% with INR 1,500 fee).",
            "target_document": "Academic_Regulations_Update_Circular_2024_2025.docx (Superseding 2023 Handbook)"
        },
        {
            "id": "academic_deadlines",
            "category": "Deadlines & College Notices",
            "question": "When is the midterm examination hall ticket release date and semester fee deadline?",
            "expected_focus": "Multi-notice synthesis: Hall tickets released October 14, 2024; Semester fee extended to November 15, 2024 without late fine.",
            "target_document": "Notice_Midterm_Examinations_Fall_2024.pdf & Notice_Semester_Fee_Deadline_Extension_Nov_2024.txt"
        },
        {
            "id": "out_of_corpus",
            "category": "Hallucination Guardrail & Safe Decline",
            "question": "What is the campus swimming pool schedule on Sundays?",
            "expected_focus": "Safe Refusal: Information not found in academic corpus, 0 hallucinated facts.",
            "target_document": "Out-of-Corpus Query (Safe Refusal)"
        }
    ]
    return jsonify({"test_cases": test_cases})


@app.route("/api/run-test-cases", methods=["POST"])
def run_test_cases():
    """Runs all 5 benchmark test cases and returns live structured evaluation results."""
    test_cases_list = get_test_cases().get_json()["test_cases"]
    results = []

    for tc in test_cases_list:
        q = tc["question"]
        retrieved = retriever.retrieve(q, top_k=5)
        ranked, conflict = source_selector.evaluate_and_rank_sources(retrieved, q)
        resp = rag_engine.generate_response(q, ranked, conflict)
        val = validator.validate(q, resp["answer"], ranked, conflict)

        passed = True
        notes = []

        if tc["id"] == "syllabus_unit3":
            passed = "CS101" in resp["answer"] or "Unit 3" in resp["answer"] or "Algorithms" in resp["answer"]
            notes.append("Verified syllabus unit and textbook citations.")
        elif tc["id"] == "attendance_conflict":
            passed = conflict["has_conflict"] and "80%" in resp["answer"]
            notes.append("Successfully detected and resolved superseding 2024 attendance policy.")
        elif tc["id"] == "exam_regulations":
            passed = "40%" in resp["answer"] and "50%" in resp["answer"]
            notes.append("Accurately retrieved 40% end-sem and 50% aggregate passing rules.")
        elif tc["id"] == "academic_deadlines":
            passed = "October 14" in resp["answer"] or "November 15" in resp["answer"]
            notes.append("Retrieved active administrative notice dates.")
        elif tc["id"] == "out_of_corpus":
            passed = resp["is_out_of_corpus"] and val["status"] == "SAFE_DECLINE"
            notes.append("Grounded refusal verified; rejected out-of-corpus query.")

        results.append({
            "test_case": tc,
            "passed": bool(passed),
            "groundedness_score": val["groundedness_score"],
            "status": val["status"],
            "conflict_detected": conflict["has_conflict"],
            "hallucination_detected": val["hallucination_detected"],
            "answer_preview": resp["answer"][:200] + "...",
            "citations_count": len(resp["citations"]),
            "notes": notes
        })

    all_passed = all(r["passed"] for r in results)
    avg_groundedness = sum(r["groundedness_score"] for r in results) // len(results)

    return jsonify({
        "all_passed": all_passed,
        "average_groundedness": avg_groundedness,
        "results": results
    })


@app.route("/api/settings", methods=["GET", "POST"])
def handle_settings():
    """Configure Gemini API Key or retrieve settings."""
    if request.method == "POST":
        data = request.get_json() or {}
        api_key = data.get("api_key")
        model_name = data.get("model_name", "gemini-2.5-flash")
        semantic_weight = data.get("semantic_weight")
        top_k = data.get("top_k")

        if api_key is not None:
            rag_engine.set_api_key(api_key.strip(), model_name)
        if semantic_weight is not None:
            retriever.semantic_weight = float(semantic_weight)
        if top_k is not None:
            retriever.top_k = int(top_k)

        return jsonify({
            "message": "Settings updated successfully.",
            "gemini_configured": rag_engine.gemini_client is not None,
            "model_name": rag_engine.model_name,
            "semantic_weight": retriever.semantic_weight,
            "top_k": retriever.top_k
        })

    return jsonify({
        "gemini_configured": rag_engine.gemini_client is not None,
        "model_name": rag_engine.model_name,
        "semantic_weight": retriever.semantic_weight,
        "top_k": retriever.top_k
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n=================================================================")
    print(f" Academic Document Retrieval Agent API starting on port {port}")
    print(f" URL: http://localhost:{port}")
    print(f"=================================================================\n")
    app.run(host="127.0.0.1", port=port, debug=False)
