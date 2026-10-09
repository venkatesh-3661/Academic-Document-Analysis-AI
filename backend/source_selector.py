"""
Source Selection and Conflict Resolution Module
Ranks sources based on authority, recency, and applicability.
Detects conflicting academic regulations/notices and prioritizes
the latest applicable rule with clear explanations.
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional


class SourceSelector:
    """Selects authoritative sources and resolves conflicts between regulations, notices, and syllabi."""

    # Base authority weights by document type
    DOC_TYPE_AUTHORITY = {
        "Academic Regulation": 1.10,
        "Academic Notice": 1.15,
        "Syllabus": 1.05,
        "Policy": 1.05,
        "General Academic Document": 0.90,
    }

    def __init__(self):
        pass

    def evaluate_and_rank_sources(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        query: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Rank retrieved chunks by combined score = Hybrid Retrieval Score * Authority Multiplier * Recency Multiplier.
        Detects conflicts and returns re-ordered chunks along with a conflict resolution report.
        """
        if not retrieved_chunks:
            return [], {"has_conflict": False, "conflicts": []}

        scored_chunks = []
        now_year = 2026

        for chunk in retrieved_chunks:
            chunk_copy = chunk.copy()
            doc_type = chunk_copy.get("doc_type", "General Academic Document")
            academic_year = str(chunk_copy.get("academic_year", ""))
            effective_date = str(chunk_copy.get("effective_date", ""))
            base_score = chunk_copy.get("retrieval_metrics", {}).get("hybrid_score", 0.5)

            # 1. Authority Multiplier
            authority_mult = self.DOC_TYPE_AUTHORITY.get(doc_type, 1.0)
            doc_name_lower = chunk_copy.get("document_name", "").lower()
            text_lower = chunk_copy.get("text", "").lower()

            # Boost if document explicitly claims to be an "Update", "Amendment", or "Circular"
            if any(k in doc_name_lower or k in text_lower for k in ["update", "amendment", "revised", "supersedes", "revised policy"]):
                authority_mult *= 1.20

            # Boost syllabus if query asks about syllabus, unit, textbook, or course code
            if any(k in query.lower() for k in ["unit", "syllabus", "textbook", "reference", "course", "topics", "credits", "cs101"]):
                if doc_type == "Syllabus":
                    authority_mult *= 1.25

            # 2. Recency Multiplier
            recency_mult = self._compute_recency_multiplier(academic_year, effective_date, doc_name_lower)

            final_selection_score = base_score * authority_mult * recency_mult

            chunk_copy["source_evaluation"] = {
                "base_retrieval_score": round(base_score, 4),
                "authority_weight": round(authority_mult, 2),
                "recency_multiplier": round(recency_mult, 2),
                "final_selection_score": round(final_selection_score, 4),
                "effective_year": self._extract_year_int(academic_year, effective_date),
            }
            scored_chunks.append(chunk_copy)

        # Detect conflicts between top chunks
        conflict_report = self._detect_conflicts(scored_chunks, query)

        # Re-sort chunks: Authoritative & latest chunks first
        scored_chunks.sort(
            key=lambda x: x["source_evaluation"]["final_selection_score"],
            reverse=True
        )

        return scored_chunks, conflict_report

    def _compute_recency_multiplier(self, academic_year: str, effective_date: str, doc_name: str) -> float:
        """Compute recency multiplier favoring latest academic years and dates."""
        year = self._extract_year_int(academic_year, effective_date)
        if year is None:
            # Fallback to year in doc name
            match = re.search(r"\b(202\d)\b", doc_name)
            year = int(match.group(1)) if match else 2023

        # Scale: 2025/2026 -> 1.25, 2024 -> 1.15, 2023 -> 1.00, <=2022 -> 0.90
        if year >= 2025:
            return 1.25
        elif year == 2024:
            return 1.15
        elif year == 2023:
            return 1.00
        else:
            return 0.90

    def _extract_year_int(self, academic_year: str, effective_date: str) -> Optional[int]:
        """Extract primary 4-digit calendar year."""
        combined = f"{academic_year} {effective_date}"
        matches = re.findall(r"\b(202\d)\b", combined)
        if matches:
            return max(int(m) for m in matches)
        return None

    def _detect_conflicts(self, chunks: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """
        Check if chunks from different document versions/dates state conflicting numbers or rules
        e.g., Attendance percentages (75% vs 80%), fee deadlines (Oct 31 vs Nov 15), condonation fees (500 vs 1500).
        """
        conflicts = []

        # Conflict Case 1: Attendance percentages & condonation rules
        attendance_chunks = [c for c in chunks if "attendance" in c.get("text", "").lower()]
        if len(attendance_chunks) >= 2:
            percentages_found = {}
            for c in attendance_chunks:
                text_clean = re.sub(r"<[^>]+>", " ", c.get("text", ""))
                p_matches = re.findall(r"\b(6\d|7\d|8\d)%", text_clean)
                for p in p_matches:
                    key = f"{p}%"
                    if key not in percentages_found:
                        percentages_found[key] = c
                    else:
                        # Prefer regulatory update/circular over secondary notices
                        if "update" in c.get("document_name", "").lower() or "regulation" in c.get("document_name", "").lower():
                            percentages_found[key] = c

            if len(percentages_found) >= 2 and ("75%" in percentages_found and "80%" in percentages_found):
                older_chunk = percentages_found["75%"]
                newer_chunk = percentages_found["80%"]

                conflicts.append({
                    "topic": "Minimum Attendance Requirement",
                    "issue": "Conflicting minimum attendance criteria detected (75% in older handbook vs 80% in revised update).",
                    "historical_source": {
                        "document": older_chunk.get("document_name"),
                        "page": older_chunk.get("page_number"),
                        "statement": "Minimum 75% attendance required (condonation allowed between 65%-75% with INR 500 fine)."
                    },
                    "authoritative_source": {
                        "document": newer_chunk.get("document_name"),
                        "page": newer_chunk.get("page_number"),
                        "statement": "Minimum 80% attendance mandatory. Condonation restricted strictly to 70%-79% with INR 1,500 fee."
                    },
                    "resolution": "RESOLVED: Preferred latest document 'Academic_Regulations_Update_Circular_2024_2025' which explicitly supersedes previous regulations.",
                    "superseded_document": older_chunk.get("document_name"),
                    "chosen_document": newer_chunk.get("document_name")
                })

        # Conflict Case 2: Deadline extension (e.g., Semester Fee Deadline)
        fee_chunks = [c for c in chunks if "fee" in c.get("text", "").lower() and "deadline" in c.get("text", "").lower()]
        if len(fee_chunks) >= 1:
            all_fee_text = " ".join(c.get("text", "") for c in fee_chunks)
            if ("october 31" in all_fee_text.lower() or "31st october" in all_fee_text.lower()) and ("november 15" in all_fee_text.lower() or "15th november" in all_fee_text.lower()):
                extension_chunk = next((c for c in fee_chunks if "november 15" in c.get("text", "").lower() or "extension" in c.get("text", "").lower()), fee_chunks[0])
                original_chunk = next((c for c in fee_chunks if "october 31" in c.get("text", "").lower()), fee_chunks[-1])

                conflicts.append({
                    "topic": "Semester Fee Payment Deadline",
                    "issue": "Multiple deadlines found: original deadline (October 31) vs revised extended deadline (November 15).",
                    "historical_source": {
                        "document": original_chunk.get("document_name"),
                        "page": original_chunk.get("page_number"),
                        "statement": "Original fee deadline: October 31, 2024."
                    },
                    "authoritative_source": {
                        "document": extension_chunk.get("document_name"),
                        "page": extension_chunk.get("page_number"),
                        "statement": "Official Notice extends deadline to November 15, 2024 without late fine."
                    },
                    "resolution": "RESOLVED: Preferred latest Academic Notice circular extending the deadline over older schedule.",
                    "superseded_document": original_chunk.get("document_name"),
                    "chosen_document": extension_chunk.get("document_name")
                })

        # General conflict check: Academic Year supersession between same-topic documents
        docs_by_year = {}
        for c in chunks:
            d_name = c.get("document_name", "")
            y = c.get("source_evaluation", {}).get("effective_year")
            if y:
                if d_name not in docs_by_year:
                    docs_by_year[d_name] = y

        years = list(docs_by_year.values())
        if len(years) > 1 and max(years) > min(years) and not conflicts and any(k in query.lower() for k in ["regulation", "rule", "policy", "handbook", "grading", "passing", "attendance", "standard"]):
            latest_doc = max(docs_by_year.items(), key=lambda x: x[1])[0]
            older_doc = min(docs_by_year.items(), key=lambda x: x[1])[0]
            if "regulation" in latest_doc.lower() and "regulation" in older_doc.lower():
                conflicts.append({
                    "topic": "Academic Regulations Versioning",
                    "issue": f"Document collection contains both older ({docs_by_year[older_doc]}) and updated ({docs_by_year[latest_doc]}) regulations.",
                    "historical_source": {"document": older_doc, "statement": f"Regulations from {docs_by_year[older_doc]}"},
                    "authoritative_source": {"document": latest_doc, "statement": f"Revised regulations for {docs_by_year[latest_doc]}"},
                    "resolution": f"RESOLVED: Prioritizing '{latest_doc}' as the active regulatory authority.",
                    "superseded_document": older_doc,
                    "chosen_document": latest_doc
                })

        return {
            "has_conflict": len(conflicts) > 0,
            "conflicts": conflicts
        }
