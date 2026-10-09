"""
Response Validation and Grounding Verification Module
Verifies that factual claims in the generated answer are supported
by retrieved documents. Detects hallucinations, verifies numerical/date
facts, and flags missing or conflicting information.
"""

import re
from typing import List, Dict, Any


class ResponseValidator:
    """Verifies factual claims in generated answers against retrieved context chunks."""

    def __init__(self, verification_threshold: float = 0.50):
        self.verification_threshold = verification_threshold

    def validate(
        self,
        query: str,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]],
        conflict_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate answer against retrieved chunks, returning grounding metrics and claim breakdown."""
        # 1. Check if the answer explicitly stated information is missing
        is_safe_decline = (
            "information not found" in answer.lower()
            or "do not contain information" in answer.lower()
            or "no relevant policies" in answer.lower()
        )

        if is_safe_decline or not retrieved_chunks:
            return {
                "groundedness_score": 100,
                "confidence_level": "High (Faithful Refusal)",
                "status": "SAFE_DECLINE",
                "summary": "Agent accurately identified that the requested information is absent from the academic repository.",
                "total_claims": 1,
                "verified_claims_count": 1,
                "claim_evaluations": [{
                    "claim_text": "Topic is not covered in uploaded academic documents.",
                    "status": "VERIFIED_DECLINE",
                    "confidence": 1.0,
                    "matched_source": "Repository Guardrail",
                    "matched_quote": "Safely declined to hallucinate non-existent information."
                }],
                "conflict_acknowledged": conflict_report.get("has_conflict", False),
                "hallucination_detected": False
            }

        # 2. Extract factual propositions / claims from the answer
        claims = self._extract_claims(answer)
        if not claims:
            claims = [answer.strip()[:200]]

        # Prepare context texts
        context_corpus = [
            {
                "doc": c.get("document_name", "Unknown"),
                "page": c.get("page_number", 1),
                "text": c.get("text", "")
            }
            for c in retrieved_chunks
        ]

        # 3. Verify each claim against context
        claim_evaluations = []
        verified_count = 0
        partially_verified_count = 0

        for claim in claims:
            best_match = self._verify_single_claim(claim, context_corpus)
            claim_evaluations.append(best_match)

            if best_match["status"] == "VERIFIED":
                verified_count += 1
            elif best_match["status"] == "PARTIALLY_SUPPORTED":
                partially_verified_count += 1

        total_claims = len(claim_evaluations)
        raw_score = (verified_count + 0.6 * partially_verified_count) / max(total_claims, 1)
        groundedness_score = int(round(raw_score * 100))
        groundedness_score = min(100, max(0, groundedness_score))

        if groundedness_score >= 85:
            conf_level = "High Groundedness"
            status = "VERIFIED"
        elif groundedness_score >= 60:
            conf_level = "Moderate Groundedness"
            status = "PARTIALLY_VERIFIED"
        else:
            conf_level = "Low / Potential Hallucination"
            status = "ATTENTION_REQUIRED"

        # Check for ungrounded numbers or dates (high risk hallucination check)
        unsupported_entities = self._detect_hallucinated_entities(answer, context_corpus)

        return {
            "groundedness_score": groundedness_score,
            "confidence_level": conf_level,
            "status": status,
            "summary": (
                f"Validated {verified_count} of {total_claims} factual claims with direct textual evidence."
                + (" Notice: Active conflict resolution applied." if conflict_report.get("has_conflict") else "")
            ),
            "total_claims": total_claims,
            "verified_claims_count": verified_count,
            "partially_verified_count": partially_verified_count,
            "claim_evaluations": claim_evaluations,
            "conflict_acknowledged": conflict_report.get("has_conflict", False),
            "hallucination_detected": len(unsupported_entities) > 0 and groundedness_score < 70,
            "unsupported_entities": unsupported_entities
        }

    def _extract_claims(self, answer: str) -> List[str]:
        """Split answer into distinct factual assertions, filtering out headings and citations."""
        clean_lines = []
        for line in answer.split("\n"):
            line = line.strip()
            # Ignore headers, quotes or citation labels
            if not line or line.startswith("#") or line.startswith(">") or line.startswith("*Citation:"):
                continue
            # Remove leading bullet symbols
            line = re.sub(r"^[-*•\d\.]+\s*", "", line)
            # Remove inline citation brackets [Doc, Page X]
            cleaned = re.sub(r"\[[^\]]+\]", "", line).strip()
            # Split line into sentences
            sentences = re.split(r"(?<=[.!?])\s+", cleaned)
            for s in sentences:
                s = s.strip()
                if len(s) > 20 and not s.lower().startswith("citation:"):
                    clean_lines.append(s)
        return clean_lines

    def _verify_single_claim(self, claim: str, context_corpus: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check if claim words and entities have strong support in any context chunk."""
        claim_norm = re.sub(r"[*_#`\[\]]", " ", claim).strip()
        claim_lower = claim_norm.lower()

        # Extract entities without broken trailing \b on %
        critical_entities = re.findall(
            r"\b\d+%|\binr\s*[\d,]+|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)\b|\bcs\d{3}\b|\b(?:clrs|cormen|weiss)\b",
            claim_lower
        )

        stopwords = {
            "a", "an", "the", "and", "or", "of", "to", "in", "for", "on", "with",
            "at", "by", "from", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "this", "that", "these", "those",
            "student", "students", "must", "shall", "required", "will", "can", "also",
            "active", "requirement", "current", "historical", "policy", "rule", "according", "to"
        }
        tokens = [t for t in re.findall(r"\b[a-z0-9]+\b", claim_lower) if t not in stopwords and len(t) > 2]

        best_score = 0.0
        best_doc = None
        best_page = 1
        best_quote = ""
        entities_found_in_best = False

        for item in context_corpus:
            doc_text = re.sub(r"<[^>]+>", " ", item["text"]).lower()
            if not tokens:
                continue

            matched = [t for t in tokens if t in doc_text]
            token_ratio = len(matched) / len(tokens)

            # Check critical entities
            entities_present = all(ent in doc_text for ent in critical_entities) if critical_entities else True

            score = token_ratio
            if critical_entities and entities_present:
                score += 0.35

            if score > best_score:
                best_score = score
                best_doc = item["doc"]
                best_page = item["page"]
                entities_found_in_best = entities_present
                # Find best quote sentence
                sentences = re.split(r"(?<=[.!?])\s+", item["text"])
                for s in sentences:
                    if any(t in s.lower() for t in matched[:3]):
                        best_quote = s.strip()
                        break
                if not best_quote and sentences:
                    best_quote = sentences[0].strip()

        # Classification
        if critical_entities:
            if entities_found_in_best and best_score >= 0.40:
                status = "VERIFIED"
            elif entities_found_in_best or best_score >= 0.35:
                status = "PARTIALLY_SUPPORTED"
            else:
                status = "UNSUPPORTED"
        else:
            if best_score >= 0.45:
                status = "VERIFIED"
            elif best_score >= 0.25:
                status = "PARTIALLY_SUPPORTED"
            else:
                status = "UNSUPPORTED"

        return {
            "claim_text": claim_norm,
            "status": status,
            "confidence": round(min(1.0, max(0.1, best_score)), 2),
            "matched_source": f"{best_doc} (Page {best_page})" if best_doc else "None",
            "matched_quote": (best_quote[:150] + "...") if len(best_quote) > 150 else best_quote
        }

    def _detect_hallucinated_entities(self, answer: str, context_corpus: List[Dict[str, Any]]) -> List[str]:
        """Detect specific dates or percentages mentioned in answer that do not exist anywhere in retrieved documents."""
        full_context_text = " ".join(item["text"].lower() for item in context_corpus)
        numbers_and_percents = re.findall(r"\b\d+%", answer.lower())
        currency = re.findall(r"\binr\s*[\d,]+", answer.lower())

        hallucinated = []
        for ent in set(numbers_and_percents + currency):
            clean_ent = ent.replace(",", "")
            clean_context = full_context_text.replace(",", "")
            if clean_ent not in clean_context:
                hallucinated.append(ent)
        return hallucinated
