"""
Comprehensive Test Suite for Academic Document Retrieval Agent
Validates:
1. Multi-format Document Processing (PDF, DOCX, TXT)
2. Hybrid Document Retrieval (BM25 + Semantic Cosine Similarity)
3. Source Selection & Recency Multipliers
4. Conflict Resolution (2024 Update superseding 2023 Handbook)
5. RAG Response Generation with inline citations
6. Groundedness & Claim Validation
7. Hallucination Guardrails & Safe Decline of Unanswerable Questions
"""

import os
import sys
import unittest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.document_processor import DocumentProcessor
from backend.retriever import HybridRetriever
from backend.source_selector import SourceSelector
from backend.rag_engine import RAGEngine
from backend.validator import ResponseValidator
from backend.sample_generator import generate_sample_corpus


class TestAcademicDocumentRetrievalAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Prepare sample documents and initialize retrieval pipeline."""
        cls.sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sample_documents"))
        if not os.path.exists(cls.sample_dir) or len(os.listdir(cls.sample_dir)) < 5:
            generate_sample_corpus(cls.sample_dir)

        cls.processor = DocumentProcessor(chunk_size=850, chunk_overlap=150)
        cls.retriever = HybridRetriever(semantic_weight=0.55, top_k=5)
        cls.selector = SourceSelector()
        cls.rag_engine = RAGEngine()
        cls.validator = ResponseValidator()

        # Ingest and index all sample documents
        cls.all_chunks = []
        cls.documents = []
        for file_name in sorted(os.listdir(cls.sample_dir)):
            file_path = os.path.join(cls.sample_dir, file_name)
            if os.path.isfile(file_path):
                processed = cls.processor.process_file(file_path)
                cls.documents.append(processed["metadata"])
                cls.all_chunks.extend(processed["chunks"])

        cls.retriever.index_chunks(cls.all_chunks)

    def test_01_document_processing_formats(self):
        """Test extraction across PDF, DOCX, and TXT files."""
        formats = {d["format"] for d in self.documents}
        self.assertIn("PDF", formats, "PDF documents must be processed.")
        self.assertIn("DOCX", formats, "DOCX documents must be processed.")
        self.assertIn("TXT", formats, "TXT documents must be processed.")
        self.assertGreaterEqual(len(self.all_chunks), 15, "Chunking should generate granular chunks.")

        # Verify page numbers and metadata preservation
        pdf_chunk = next(c for c in self.all_chunks if c["document_name"].endswith(".pdf"))
        self.assertIn("page_number", pdf_chunk)
        self.assertGreaterEqual(pdf_chunk["page_number"], 1)
        self.assertTrue(pdf_chunk["doc_type"] in ["Academic Regulation", "Academic Notice", "Syllabus"])

    def test_02_hybrid_retrieval_syllabus(self):
        """Test hybrid retrieval on syllabus topics and textbooks."""
        query = "What are the reference textbooks and topics for Unit 3 in Data Structures?"
        retrieved = self.retriever.retrieve(query, top_k=5)

        self.assertGreater(len(retrieved), 0, "Retrieval should return relevant chunks.")
        top_doc = retrieved[0]["document_name"]
        self.assertIn("CS101", top_doc, "Top chunk for syllabus should be CS101.")

        top_metrics = retrieved[0]["retrieval_metrics"]
        self.assertGreater(top_metrics["hybrid_score"], 0.30)
        self.assertGreater(top_metrics["bm25_score"], 0.0)

    def test_03_attendance_conflict_detection_and_resolution(self):
        """Test that conflicting attendance regulations (75% vs 80%) are detected and resolved."""
        query = "What is the minimum attendance required to appear for exams and can it be condoned?"
        retrieved = self.retriever.retrieve(query, top_k=5)
        ranked_chunks, conflict_report = self.selector.evaluate_and_rank_sources(retrieved, query)

        # Conflict must be flagged
        self.assertTrue(conflict_report["has_conflict"], "Conflict between 75% and 80% attendance must be detected.")
        conflict = conflict_report["conflicts"][0]
        self.assertIn("Attendance", conflict["topic"])
        self.assertIn("Update", conflict["chosen_document"])

        # Top ranked chunk must be the 2024 update
        top_chunk = ranked_chunks[0]
        self.assertIn("2024", top_chunk["document_name"])

        # Generate answer and verify conflict notice
        response = self.rag_engine.generate_response(query, ranked_chunks, conflict_report)
        self.assertIn("80%", response["answer"], "Answer must communicate the active 80% requirement.")
        self.assertIn("INR 1,500", response["answer"], "Answer must state the active INR 1,500 condonation fee.")

    def test_04_passing_criteria_and_regulations(self):
        """Test passing criteria retrieval and response validation."""
        query = "What is the passing criteria and minimum marks required in the end semester examination?"
        retrieved = self.retriever.retrieve(query, top_k=5)
        ranked_chunks, conflict_report = self.selector.evaluate_and_rank_sources(retrieved, query)
        response = self.rag_engine.generate_response(query, ranked_chunks, conflict_report)
        validation = self.validator.validate(query, response["answer"], ranked_chunks, conflict_report)

        self.assertIn("40%", response["answer"], "Should state 40% end semester pass criteria.")
        self.assertIn("50%", response["answer"], "Should state 50% aggregate pass criteria.")
        self.assertGreaterEqual(validation["groundedness_score"], 70, "Groundedness should be high.")
        self.assertFalse(validation["hallucination_detected"])

    def test_05_deadline_and_notice_retrieval(self):
        """Test retrieval for midterm exam schedule and semester fee extension."""
        query = "When is the midterm examination hall ticket release date and semester fee deadline?"
        retrieved = self.retriever.retrieve(query, top_k=5)
        ranked_chunks, conflict_report = self.selector.evaluate_and_rank_sources(retrieved, query)
        response = self.rag_engine.generate_response(query, ranked_chunks, conflict_report)
        validation = self.validator.validate(query, response["answer"], ranked_chunks, conflict_report)

        self.assertIn("October 14, 2024", response["answer"], "Must mention hall ticket release date.")
        self.assertIn("November 15, 2024", response["answer"], "Must mention extended fee deadline.")
        self.assertEqual(validation["status"], "VERIFIED")

    def test_06_unanswerable_query_safe_decline(self):
        """Test that questions outside academic corpus are safely declined without hallucinations."""
        query = "What is the campus swimming pool schedule on Sundays?"
        retrieved = self.retriever.retrieve(query, top_k=5)
        ranked_chunks, conflict_report = self.selector.evaluate_and_rank_sources(retrieved, query)
        response = self.rag_engine.generate_response(query, ranked_chunks, conflict_report)
        validation = self.validator.validate(query, response["answer"], ranked_chunks, conflict_report)

        self.assertTrue(response["is_out_of_corpus"])
        self.assertEqual(validation["status"], "SAFE_DECLINE")
        self.assertEqual(validation["groundedness_score"], 100)
        self.assertFalse(validation["hallucination_detected"])
        self.assertIn("Information Not Found", response["answer"])


if __name__ == "__main__":
    unittest.main()
