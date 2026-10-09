"""
Document Processor Module
Handles text extraction from PDF, DOCX, and TXT files,
structure-aware chunking, and metadata extraction.
"""

import os
import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx
except ImportError:
    docx = None


class DocumentProcessor:
    """Processes academic documents (PDF, DOCX, TXT) into structured chunks with rich metadata."""

    def __init__(self, chunk_size: int = 850, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_file(
        self,
        file_path: str,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract text, infer metadata, and split into chunks."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        ext = os.path.splitext(file_name)[1].lower()

        pages_data = []
        if ext == ".pdf":
            pages_data = self._extract_pdf(file_path)
        elif ext == ".docx":
            pages_data = self._extract_docx(file_path)
        elif ext in [".txt", ".md"]:
            pages_data = self._extract_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Supported formats are .pdf, .docx, .txt")

        full_text = "\n\n".join(p["text"] for p in pages_data)
        inferred_meta = self._infer_metadata(file_name, full_text)

        metadata = {
            "doc_id": str(uuid.uuid4())[:8],
            "document_name": file_name,
            "file_path": file_path,
            "format": ext[1:].upper(),
            "total_pages": len(pages_data),
            "doc_type": inferred_meta["doc_type"],
            "academic_year": inferred_meta["academic_year"],
            "effective_date": inferred_meta["effective_date"],
            "authority": inferred_meta["authority"],
            "title": inferred_meta["title"],
            "uploaded_at": datetime.now().isoformat(),
        }

        # Apply user-provided custom metadata overrides if any
        if custom_metadata:
            for k, v in custom_metadata.items():
                if v is not None and str(v).strip():
                    metadata[k] = v

        # Structure-aware chunking preserving page numbers and section headers
        chunks = self._chunk_pages(pages_data, metadata)

        return {
            "metadata": metadata,
            "pages": pages_data,
            "chunks": chunks,
            "total_chunks": len(chunks),
        }

    def _extract_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract text page-by-page from PDF."""
        if not pypdf:
            raise ImportError("pypdf is required to process PDF files.")

        pages_data = []
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            total = len(reader.pages)
            for idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                pages_data.append({
                    "page_number": idx + 1,
                    "text": text.strip(),
                    "section_title": self._guess_section_title(text)
                })
        return pages_data

    def _extract_docx(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from DOCX preserving headings, tables, and section hierarchy."""
        if not docx:
            raise ImportError("python-docx is required to process DOCX files.")

        doc = docx.Document(file_path)
        current_section = "General"
        collected_paragraphs = []
        pages_data = []
        page_num = 1
        word_count = 0

        for p in doc.paragraphs:
            text = re.sub(r"<[^>]+>", " ", p.text).strip()
            if not text:
                continue

            if p.style and ("Heading" in p.style.name or "Title" in p.style.name):
                current_section = text

            collected_paragraphs.append({
                "text": text,
                "section": current_section
            })
            word_count += len(text.split())

            # Approximate logical page boundary every ~350-400 words
            if word_count > 350:
                page_text = "\n\n".join(item["text"] for item in collected_paragraphs)
                pages_data.append({
                    "page_number": page_num,
                    "text": page_text,
                    "section_title": collected_paragraphs[0]["section"]
                })
                collected_paragraphs = []
                word_count = 0
                page_num += 1

        # Process tables if any
        for table in doc.tables:
            table_rows = []
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    table_rows.append(row_text)
            if table_rows:
                table_str = "[TABLE]\n" + "\n".join(table_rows) + "\n[/TABLE]"
                collected_paragraphs.append({
                    "text": table_str,
                    "section": current_section
                })

        if collected_paragraphs or not pages_data:
            page_text = "\n\n".join(item["text"] for item in collected_paragraphs)
            pages_data.append({
                "page_number": page_num,
                "text": page_text,
                "section_title": collected_paragraphs[0]["section"] if collected_paragraphs else current_section
            })

        return pages_data

    def _extract_txt(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract plain text, breaking into logical pages based on page/section markers or word limits."""
        content = ""
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        # Split on explicit page breaks if present
        if "--- PAGE BREAK ---" in content or "\f" in content:
            raw_pages = re.split(r"(?:--- PAGE BREAK ---|\f)", content)
            pages_data = []
            for idx, p_text in enumerate(raw_pages):
                if p_text.strip():
                    pages_data.append({
                        "page_number": idx + 1,
                        "text": p_text.strip(),
                        "section_title": self._guess_section_title(p_text)
                    })
            if pages_data:
                return pages_data

        # Otherwise divide by logical paragraph/word size (~400 words per virtual page)
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        pages_data = []
        current_page = []
        current_words = 0
        page_num = 1

        for para in paragraphs:
            current_page.append(para)
            current_words += len(para.split())
            if current_words >= 350:
                pages_data.append({
                    "page_number": page_num,
                    "text": "\n\n".join(current_page),
                    "section_title": self._guess_section_title(current_page[0])
                })
                current_page = []
                current_words = 0
                page_num += 1

        if current_page or not pages_data:
            pages_data.append({
                "page_number": page_num,
                "text": "\n\n".join(current_page) if current_page else content.strip(),
                "section_title": self._guess_section_title(current_page[0]) if current_page else "Document Body"
            })

        return pages_data

    def _guess_section_title(self, text: str) -> str:
        """Find a leading heading or section title."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            return "General"
        first_line = lines[0]
        if len(first_line) < 80 and not first_line.endswith("."):
            return first_line
        # Look for Section/Unit/Article keywords
        match = re.search(r"(Unit\s+\d+|Section\s+\d+|Article\s+\d+|Regulation\s+\d+|Notice|Circular|Policy):?\s*([^\n\.\,]+)", text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
        return first_line[:60] + "..." if len(first_line) > 60 else first_line

    def _infer_metadata(self, file_name: str, text: str) -> Dict[str, Any]:
        """Extract document type, academic year, effective date, authority, and title."""
        lower_name = file_name.lower()
        lower_text = text[:2000].lower()

        # Doc Type classification
        if any(w in lower_name or w in lower_text for w in ["syllabus", "curriculum", "course outline", "unit 1", "unit 2", "textbook"]):
            doc_type = "Syllabus"
        elif any(w in lower_name or w in lower_text for w in ["regulation", "regulations", "ordinance", "handbook", "grading system", "rule"]):
            doc_type = "Academic Regulation"
        elif any(w in lower_name or w in lower_text for w in ["notice", "circular", "announcement", "notification", "schedule"]):
            doc_type = "Academic Notice"
        elif any(w in lower_name or w in lower_text for w in ["policy", "guideline", "code of conduct"]):
            doc_type = "Policy"
        else:
            doc_type = "General Academic Document"

        # Clean HTML artifacts if present
        clean_text = re.sub(r"<[^>]+>", " ", text)
        clean_name = re.sub(r"<[^>]+>", " ", file_name)

        # Academic Year extraction (e.g. 2024-2025, 2024-25, 2023-2024)
        year_match = re.search(r"\b(202\d)[\s/–-]+(202\d)\b", clean_text[:3000] + " " + clean_name)
        if year_match:
            academic_year = f"{year_match.group(1)}-{year_match.group(2)}"
        else:
            short_match = re.search(r"\b(202\d)[\s/–-](\d{2})\b", clean_text[:3000] + " " + clean_name)
            if short_match and int(short_match.group(2)) == (int(short_match.group(1)) % 100) + 1:
                academic_year = f"{short_match.group(1)}-20{short_match.group(2)}"
            else:
                single_year = re.search(r"\b(202[0-9])\b", clean_name + " " + clean_text[:1500])
                academic_year = f"{single_year.group(1)}-{int(single_year.group(1))+1}" if single_year else "2024-2025"

        # Date extraction (e.g., "October 5, 2024", "15 July 2024", "2024-10-05")
        date_patterns = [
            r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+20\d{2})\b",
            r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+20\d{2})\b",
            r"\b(20\d{2}-\d{2}-\d{2})\b"
        ]
        effective_date = None
        for pat in date_patterns:
            d_match = re.search(pat, text[:3000], re.IGNORECASE)
            if d_match:
                effective_date = d_match.group(1).strip()
                break

        if not effective_date:
            # Fallback to year extracted
            year_num = re.search(r"\b(202[0-9])\b", file_name + " " + text[:1000])
            effective_date = f"{year_num.group(1)}-01-01" if year_num else datetime.now().strftime("%Y-%m-%d")

        # Authority extraction
        authority = "Academic Council"
        if "controller of examinations" in lower_text or "examination branch" in lower_text:
            authority = "Office of the Controller of Examinations"
        elif "dean of academic affairs" in lower_text or "academic dean" in lower_text:
            authority = "Dean of Academic Affairs"
        elif "registrar" in lower_text:
            authority = "Office of the Registrar"
        elif "department of" in lower_text:
            dept_match = re.search(r"department of ([a-zA-Z\s]+)", lower_text)
            if dept_match:
                authority = f"Department of {dept_match.group(1).title().strip()}"
        elif doc_type == "Syllabus":
            authority = "Board of Studies"

        title = os.path.splitext(file_name)[0].replace("_", " ").title()

        return {
            "doc_type": doc_type,
            "academic_year": academic_year,
            "effective_date": effective_date,
            "authority": authority,
            "title": title
        }

    def _chunk_pages(
        self,
        pages_data: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks, tracking page numbers and headings."""
        all_chunks = []
        chunk_idx = 0

        for page in pages_data:
            page_num = page["page_number"]
            page_text = page["text"]
            section_title = page.get("section_title", "General")

            if not page_text:
                continue

            # Split text on paragraph boundaries first
            raw_paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]
            if not raw_paragraphs:
                raw_paragraphs = [page_text]

            current_chunk = ""
            current_section = section_title

            for para in raw_paragraphs:
                # Detect inline section heading
                if len(para) < 70 and any(h in para.lower() for h in ["unit", "section", "article", "rule", "schedule", "passing", "attendance", "grading", "penalty"]):
                    current_section = para

                # If adding para exceeds chunk size, split or emit
                if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                    current_chunk = (current_chunk + "\n\n" + para).strip()
                else:
                    if current_chunk:
                        chunk_id = f"{metadata['doc_id']}_p{page_num}_c{chunk_idx}"
                        all_chunks.append({
                            "chunk_id": chunk_id,
                            "doc_id": metadata["doc_id"],
                            "document_name": metadata["document_name"],
                            "doc_type": metadata["doc_type"],
                            "academic_year": metadata["academic_year"],
                            "effective_date": metadata["effective_date"],
                            "authority": metadata["authority"],
                            "page_number": page_num,
                            "section_title": current_section,
                            "text": current_chunk,
                            "char_count": len(current_chunk),
                            "word_count": len(current_chunk.split()),
                        })
                        chunk_idx += 1

                    # If paragraph itself is larger than chunk size, split into sub-sentences
                    if len(para) > self.chunk_size:
                        sub_chunks = self._split_large_text(para, self.chunk_size, self.chunk_overlap)
                        for sc in sub_chunks[:-1]:
                            chunk_id = f"{metadata['doc_id']}_p{page_num}_c{chunk_idx}"
                            all_chunks.append({
                                "chunk_id": chunk_id,
                                "doc_id": metadata["doc_id"],
                                "document_name": metadata["document_name"],
                                "doc_type": metadata["doc_type"],
                                "academic_year": metadata["academic_year"],
                                "effective_date": metadata["effective_date"],
                                "authority": metadata["authority"],
                                "page_number": page_num,
                                "section_title": current_section,
                                "text": sc,
                                "char_count": len(sc),
                                "word_count": len(sc.split()),
                            })
                            chunk_idx += 1
                        current_chunk = sub_chunks[-1]
                    else:
                        current_chunk = para

            if current_chunk:
                chunk_id = f"{metadata['doc_id']}_p{page_num}_c{chunk_idx}"
                all_chunks.append({
                    "chunk_id": chunk_id,
                    "doc_id": metadata["doc_id"],
                    "document_name": metadata["document_name"],
                    "doc_type": metadata["doc_type"],
                    "academic_year": metadata["academic_year"],
                    "effective_date": metadata["effective_date"],
                    "authority": metadata["authority"],
                    "page_number": page_num,
                    "section_title": current_section,
                    "text": current_chunk,
                    "char_count": len(current_chunk),
                    "word_count": len(current_chunk.split()),
                })
                chunk_idx += 1

        return all_chunks

    def _split_large_text(self, text: str, max_size: int, overlap: int) -> List[str]:
        """Split oversized text on sentence boundaries with overlap."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        result = []
        buf = ""

        for s in sentences:
            if len(buf) + len(s) + 1 <= max_size:
                buf = (buf + " " + s).strip()
            else:
                if buf:
                    result.append(buf)
                    # Keep tail of buffer for overlap
                    overlap_point = max(0, len(buf) - overlap)
                    buf = buf[overlap_point:].strip() + " " + s
                else:
                    # Single massive sentence
                    for i in range(0, len(s), max_size - overlap):
                        result.append(s[i:i + max_size])
                    buf = ""
        if buf.strip():
            result.append(buf.strip())
        return result if result else [text]
