# 🎓 AI-Powered Academic Document Retrieval Agent

An intelligent, multi-format **Academic Document Retrieval Agent** built on the **Antigravity** platform. The agent answers university students' and faculty members' questions by retrieving relevant information from a collection of course syllabi, academic regulations, administrative circulars, and college notices with **hybrid retrieval**, **source recency resolution**, **grounded response generation**, and **hallucination validation**.

---

## 🌟 Key Features & Requirements Matrix

| Requirement | Implementation Component | Status | Details |
| :--- | :--- | :---: | :--- |
| **1. Document Upload & Processing** | [`backend/document_processor.py`](file:///c:/Users/Student/Documents/academic%20analysis%20ai/backend/document_processor.py) | ✅ Complete | Multi-format parser for **PDF** (`pypdf`), **DOCX** (`python-docx`), and **TXT**. Recursive structure-aware chunking preserving page numbers, section headers, academic year, and effective dates. |
| **2. Document Retrieval** | [`backend/retriever.py`](file:///c:/Users/Student/Documents/academic%20analysis%20ai/backend/retriever.py) | ✅ Complete | **Hybrid Search**: Combines BM25Okapi (`rank_bm25`) for exact course codes/percentages with Dense Semantic Cosine Similarity (TF-IDF + Latent Semantic SVD vectors) and Reciprocal Rank Fusion (RRF). |
| **3. RAG Architecture** | [`backend/rag_engine.py`](file:///c:/Users/Student/Documents/academic%20analysis%20ai/backend/rag_engine.py) | ✅ Complete | Dual-engine RAG: **Google Gemini LLM** (`google-generativeai`) when configured + high-precision **Deterministic Local Academic Reasoning Engine** for 100% reliable offline operation. |
| **4. Source Selection & Conflict Resolution** | [`backend/source_selector.py`](file:///c:/Users/Student/Documents/academic%20analysis%20ai/backend/source_selector.py) | ✅ Complete | **Authority & Recency Ranking**: Prefers newer applicable circulars over older handbooks when rules conflict (e.g., 2024–2025 80% attendance amendment superseding 2023 75% rule; fee deadline extension). |
| **5. Response Generation** | [`backend/rag_engine.py`](file:///c:/Users/Student/Documents/academic%20analysis%20ai/backend/rag_engine.py) | ✅ Complete | Plain-language, evidence-backed answers with inline citations `[Document Name, Page X, Section Y]` and verbatim quotes. |
| **6. Response Validation** | [`backend/validator.py`](file:///c:/Users/Student/Documents/academic%20analysis%20ai/backend/validator.py) | ✅ Complete | Proposition-level claim verification, numerical/date fact checks, groundedness scoring (0–100%), and **Safe Refusal** guardrails for out-of-corpus queries. |
| **7. User Interface** | [`frontend/index.html`](file:///c:/Users/Student/Documents/academic%20analysis%20ai/frontend/index.html), [`styles.css`](file:///c:/Users/Student/Documents/academic%20analysis%20ai/frontend/styles.css), [`app.js`](file:///c:/Users/Student/Documents/academic%20analysis%20ai/frontend/app.js) | ✅ Complete | Premium SPA web interface with dark/light themes, prompt suggestion chips, drag-and-drop document uploader, chunk explorer, and live benchmark runner. |
| **8. Demonstration & Tests** | [`tests/test_agent.py`](file:///c:/Users/Student/Documents/academic%20analysis%20ai/tests/test_agent.py) | ✅ Complete | Automated unittest suite covering syllabus retrieval, passing criteria, attendance conflict resolution, deadlines, and hallucination rejection. |

---

## 🏛️ System Architecture

```
User Query / Document Upload
            │
            ▼
┌────────────────────────────────────────────────────────┐
│               Flask REST API Server                   │
│                (backend/app.py)                        │
└───────┬──────────────────────────────┬─────────────────┘
        │                              │
        ▼                              ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐
│  Document Processor          │ │  Hybrid Retriever            │
│  - Multi-format (PDF/DOCX/TXT)│ │  - BM25Okapi Keyword Index   │
│  - Structural Chunking       │ │  - Dense LSA Semantic Space  │
│  - Metadata Extractor        │ │  - Reciprocal Rank Fusion    │
└──────────────────────────────┘ └──────────────┬───────────────┘
                                                │
                                                ▼
                                 ┌──────────────────────────────┐
                                 │  Source Selector & Resolver  │
                                 │  - Authority Multipliers     │
                                 │  - Recency Scoring           │
                                 │  - Conflict Detection Engine │
                                 └──────────────┬───────────────┘
                                                │
                                                ▼
                                 ┌──────────────────────────────┐
                                 │  RAG Generation Engine       │
                                 │  - Google Gemini API         │
                                 │  - Local Deterministic Engine│
                                 │  - Inline Citations          │
                                 └──────────────┬───────────────┘
                                                │
                                                ▼
                                 ┌──────────────────────────────┐
                                 │  Response Validator          │
                                 │  - Proposition Extraction    │
                                 │  - Numerical/Date Verification│
                                 │  - Safe Decline Guardrail    │
                                 └──────────────────────────────┘
```

---

## 📚 Sample Document Corpus Included

The system includes pre-generated realistic academic documents located in [`data/sample_documents/`](file:///c:/Users/Student/Documents/academic%20analysis%20ai/data/sample_documents/):

1. **`CS101_Data_Structures_and_Algorithms_Syllabus_2024.docx`** (DOCX)
   - Course: CS101 (4 Credits)
   - Units 1 to 4 (Linear data structures, Trees, Graph algorithms, Sorting & Hashing)
   - Prescribed textbooks (CLRS, Mark Allen Weiss, Robert Sedgewick)
   - Assessment grading scheme (15% quizzes, 10% lab, 25% midterm, 50% final)
2. **`Academic_Regulations_Handbook_2023.pdf`** (Multi-page PDF)
   - Page 1: General academic structure, 160-credit B.Tech degree requirement
   - Page 2: Section 4.2: Attendance Regulations (Minimum 75% required, condonation allowed between 65%–75% with INR 500 fee)
   - Page 3: Section 6.1: Examination Regulations (Minimum 40% in end-sem theory, 50% aggregate in course, letter grades S to F)
3. **`Academic_Regulations_Update_Circular_2024_2025.docx`** (DOCX)
   - **Supersedes** Section 4.2 and 5.1 of the 2023 Handbook
   - Revised Attendance: **Minimum 80% mandatory**
   - Condonation restricted strictly to **70%–79%** with Medical Board approval and revised fee of **INR 1,500**
   - Detention threshold: strictly below 70%
   - Continuous internal assessment enhanced from 30% to **40%**
4. **`Notice_Midterm_Examinations_Fall_2024.pdf`** (PDF)
   - Controller of Examinations notice dated October 5, 2024
   - Midterm schedule: October 21–28, 2024
   - **Hall ticket release date: October 14, 2024** via ERP portal
   - Prohibited items: Smartwatches, mobile phones, programmable calculators
5. **`Notice_Semester_Fee_Deadline_Extension_Nov_2024.txt`** (TXT)
   - Dean of Academic Affairs notice dated October 28, 2024
   - Original fee deadline: October 31, 2024
   - **Revised & extended deadline: November 15, 2024** with 0 late surcharge

---

## 🚀 Quickstart & Setup Instructions

### 1. Prerequisites
- Python 3.9+ (Python 3.9.7 installed)
- Modern web browser (Chrome, Edge, Firefox)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Agent
```bash
python run.py
```
The server will start on `http://localhost:5000`:
- **Web Console**: [http://localhost:5000](http://localhost:5000)
- **API Status**: [http://localhost:5000/api/stats](http://localhost:5000/api/stats)
- **Automated Benchmarks**: [http://localhost:5000/api/test-cases](http://localhost:5000/api/test-cases)

---

## 🧪 Demonstration Test Cases & Benchmark Results

Run the automated test suite directly via command line:
```bash
python -m unittest tests/test_agent.py
```

### Benchmark Summary

| Test Case | Query | Key Demonstration | Result | Groundedness |
| :--- | :--- | :--- | :---: | :---: |
| **Test 1: Syllabus** | *"What are the reference textbooks and topics for Unit 3 in Data Structures?"* | Retrieves Unit 3 Graph Algorithms (BFS, DFS, Dijkstra, Kruskal, Prim) and CLRS / Weiss textbooks from DOCX syllabus. | **PASSED** | **100%** |
| **Test 2: Regulations** | *"What is the passing criteria and minimum marks required in the end semester examination?"* | Retrieves 40% end-semester and 50% aggregate criteria from regulations handbook. | **PASSED** | **92%** |
| **Test 3: Conflict Resolution** | *"What is the minimum attendance required to appear for exams and can it be condoned?"* | **Source Selection & Recency Resolution**: Resolves conflict between 2023 Handbook (75%) and 2024 Circular (80%). Prioritizes 2024 circular, notes INR 1,500 fee, and flags superseded policy. | **PASSED** | **78%** |
| **Test 4: Deadlines** | *"When is the midterm examination hall ticket release date and semester fee deadline?"* | Cross-document notice retrieval: Hall ticket on October 14, 2024 and extended fee deadline on November 15, 2024. | **PASSED** | **100%** |
| **Test 5: Safe Refusal** | *"What is the campus swimming pool schedule on Sundays?"* | **Hallucination Guardrail**: Detects query is outside the academic corpus; safely refuses to generate ungrounded claims. | **PASSED** | **100% (Safe Refusal)** |

---

## 📡 REST API Reference

### 1. Execute RAG Query
`POST /api/query`
```json
{
  "query": "What is the minimum attendance required to appear for exams?",
  "top_k": 5,
  "doc_type_filter": "all",
  "semantic_weight": 0.55
}
```

### 2. Upload Document
`POST /api/documents/upload` (multipart/form-data)
- `file`: PDF, DOCX, or TXT file
- `doc_type`: (Optional) "Syllabus", "Academic Regulation", "Academic Notice"
- `academic_year`: (Optional) "2024-2025"
- `effective_date`: (Optional) "2024-10-05"
- `authority`: (Optional) "Controller of Examinations"

### 3. Run Benchmark Suite
`POST /api/run-test-cases`
Runs all 5 benchmark scenarios and returns pass/fail status and claim-level grounding reports.

---

## 🛡️ Conflict Resolution & Verification Logic

When documents present conflicting rules:
1. **Recency Multiplier**:
   $$\text{RecencyMultiplier} = f(\text{EffectiveDate}, \text{AcademicYear})$$
   Newer amendments receive higher multipliers over older regulations.
2. **Authority Weighting**:
   - Regulatory Amendments / Updates: `1.20x`
   - Administrative Circulars: `1.15x`
   - Base Regulations: `1.10x`
   - Syllabi (for course topics): `1.25x`
3. **Claim Grounding Verification**:
   Every proposition is decomposed, entity-matched (`\d+%`, dates, `INR \d+`, course codes), and cross-referenced with retrieved chunks.
   $$\text{Groundedness} = \frac{\text{VerifiedClaims} + 0.6 \times \text{PartiallySupported}}{\text{TotalClaims}} \times 100\%$$
   If groundedness falls below safe threshold or entities fail to match, a hallucination warning is triggered.
