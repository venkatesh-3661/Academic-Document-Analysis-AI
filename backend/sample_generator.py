"""
Sample Academic Document Corpus Generator
Creates realistic academic documents across PDF, DOCX, and TXT formats
with genuine conflicting regulations, syllabi, and administrative notices.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


def generate_sample_corpus(output_dir: str):
    """Generate all sample documents in the specified directory."""
    os.makedirs(output_dir, exist_ok=True)

    create_syllabus_docx(os.path.join(output_dir, "CS101_Data_Structures_and_Algorithms_Syllabus_2024.docx"))
    create_regulations_2023_pdf(os.path.join(output_dir, "Academic_Regulations_Handbook_2023.pdf"))
    create_regulations_update_2024_docx(os.path.join(output_dir, "Academic_Regulations_Update_Circular_2024_2025.docx"))
    create_midterm_notice_pdf(os.path.join(output_dir, "Notice_Midterm_Examinations_Fall_2024.pdf"))
    create_fee_extension_txt(os.path.join(output_dir, "Notice_Semester_Fee_Deadline_Extension_Nov_2024.txt"))

    print(f"[SampleGenerator] Successfully created all 5 sample academic documents in: {output_dir}")


def create_syllabus_docx(file_path: str):
    """Generate DOCX syllabus for CS101."""
    doc = docx.Document()

    title = doc.add_heading("CS101: Data Structures and Algorithms", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub = doc.add_paragraph("Department of Computer Science & Engineering | Academic Year 2024-2025")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("Course Credits: 4 (Lecture: 3 hrs/week, Tutorial/Lab: 2 hrs/week) | Prerequisites: CS100 Programming in C/C++")

    doc.add_heading("Course Objectives", level=1)
    doc.add_paragraph(
        "To provide students with a comprehensive foundation in fundamental abstract data types, dynamic data structures, "
        "and algorithmic complexity analysis. Students will master linear and non-linear data structures, graph traversals, and sorting techniques."
    )

    doc.add_heading("Unit 1: Linear Data Structures", level=1)
    doc.add_paragraph(
        "Introduction to Algorithm Analysis: Asymptotic notations (Big-O, Omega, Theta), time and space complexity tradeoffs. "
        "Linear Lists: Arrays and Dynamic Memory Allocation. Singly linked lists, doubly linked lists, and circular linked lists. "
        "Stacks: Array and linked representations, stack applications (infix to postfix conversion, balanced parenthesis evaluation). "
        "Queues: FIFO queues, circular queues, double-ended queues (deque), and priority queues."
    )

    doc.add_heading("Unit 2: Hierarchical Data Structures - Trees", level=1)
    doc.add_paragraph(
        "Basic Tree concepts: Terminology, representations, and binary trees. "
        "Binary Tree traversals: Pre-order, in-order, post-order, and level-order. "
        "Binary Search Trees (BST): Insertion, deletion, search, and min/max operations. "
        "Balanced Trees: AVL tree rotations and balance factor maintenance, Red-Black tree principles. "
        "Heaps: Min-heap, max-heap, priority queue implementation using binary heaps, and Heap Sort."
    )

    doc.add_heading("Unit 3: Graph Algorithms & Advanced Data Structures", level=1)
    doc.add_paragraph(
        "Graph Representations: Adjacency matrix and adjacency lists. "
        "Graph Traversals: Breadth-First Search (BFS) and Depth-First Search (DFS) with complexity analysis. "
        "Topological Sorting for Directed Acyclic Graphs (DAGs). "
        "Minimum Spanning Trees: Kruskal's algorithm (Disjoint Set Union) and Prim's greedy algorithm. "
        "Shortest Path Algorithms: Single-source shortest path using Dijkstra's algorithm and Bellman-Ford algorithm; All-pairs shortest path with Floyd-Warshall."
    )

    doc.add_heading("Unit 4: Sorting, Searching, and Hashing", level=1)
    doc.add_paragraph(
        "Searching Techniques: Linear search, binary search, and interpolation search. "
        "Sorting Algorithms: Quick Sort with randomized pivot selection, Merge Sort, Radix Sort. "
        "Hashing: Hash functions, collision resolution strategies (separate chaining, open addressing: linear probing, quadratic probing, double hashing)."
    )

    doc.add_heading("Prescribed Textbooks and References", level=1)
    doc.add_paragraph(
        "1. Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, and Clifford Stein. 'Introduction to Algorithms' (CLRS), 3rd/4th Edition, MIT Press.\n"
        "2. Mark Allen Weiss. 'Data Structures and Algorithm Analysis in C++', 4th Edition, Pearson Education.\n"
        "3. Robert Sedgewick and Kevin Wayne. 'Algorithms', 4th Edition, Addison-Wesley Professional."
    )

    doc.add_heading("Grading and Course Assessment Breakdown", level=1)
    table = doc.add_table(rows=1, cols=3)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Assessment Component"
    hdr_cells[1].text = "Weightage"
    hdr_cells[2].text = "Schedule"

    items = [
        ("Continuous Quizzes (3 Best of 4)", "15%", "Bi-weekly"),
        ("Programming Lab Assignments", "10%", "Weekly Submissions"),
        ("Midterm Examination", "25%", "8th Week of Semester"),
        ("End-Semester Final Examination", "50%", "End of Semester (16th Week)")
    ]
    for comp, wt, sch in items:
        row = table.add_row().cells
        row[0].text = comp
        row[1].text = wt
        row[2].text = sch

    doc.save(file_path)


def create_regulations_2023_pdf(file_path: str):
    """Generate multi-page PDF for Academic Regulations Handbook 2023."""
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1,
        spaceAfter=14
    )
    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1E40AF'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=8
    )

    story = []

    # PAGE 1: Preamble & Structure
    story.append(Paragraph("UNIVERSITY ACADEMIC REGULATIONS HANDBOOK", title_style))
    story.append(Paragraph("<b>Academic Year: 2023-2024</b> | Approved by Academic Council Ordinance No. AC/2023/04", ParagraphStyle('Sub', parent=body_style, alignment=1, textColor=colors.HexColor('#4B5563'))))
    story.append(Spacer(1, 15))
    story.append(Paragraph("Section 1: General Academic Structure", h2_style))
    story.append(Paragraph(
        "1.1. These regulations shall govern all undergraduate and postgraduate engineering and computing programs for students enrolled in the 2023-2024 academic cycle. "
        "A student shall be eligible for the award of Bachelor of Technology (B.Tech) degree if they earn a minimum aggregate of 160 academic credits.",
        body_style
    ))
    story.append(Paragraph("Section 2: Registration and Credit Distribution", h2_style))
    story.append(Paragraph(
        "2.1. Every full-time registered student must register for a minimum of 18 credits and a maximum of 26 credits per semester. "
        "Late course registration is permissible up to five working days from commencement of classes upon payment of an administrative surcharge.",
        body_style
    ))
    story.append(PageBreak())

    # PAGE 2: Attendance Regulations (2023 Version)
    story.append(Paragraph("Section 4.2: Attendance Regulations (2023 Framework)", h2_style))
    story.append(Paragraph(
        "4.2.1. <b>Minimum Attendance Requirement</b>: Every candidate must secure a minimum of <b>75% attendance</b> in aggregate across all lectures, practicals, and tutorial sessions in every enrolled subject to qualify for the end-semester examinations.",
        body_style
    ))
    story.append(Paragraph(
        "4.2.2. <b>Condonation of Shortage</b>: The Academic Dean may grant condonation of attendance shortage to a student whose attendance falls between <b>65% and 75%</b>, strictly on medical grounds supported by a valid certificate issued by a registered medical practitioner.",
        body_style
    ))
    story.append(Paragraph(
        "4.2.3. <b>Condonation Fee</b>: An application for condonation must be accompanied by payment of a prescribed condonation fee of <b>INR 500</b> per course/semester to the college accounts section.",
        body_style
    ))
    story.append(Paragraph(
        "4.2.4. <b>Detention</b>: Candidates who record attendance lower than <b>65%</b> under any circumstance are strictly ineligible for condonation and shall be detained, requiring re-registration in the subsequent academic session.",
        body_style
    ))
    story.append(PageBreak())

    # PAGE 3: Examination Regulations & Passing Criteria
    story.append(Paragraph("Section 6.1: Examination Regulations & Passing Criteria", h2_style))
    story.append(Paragraph(
        "6.1.1. <b>Passing Standard in Theory Courses</b>: A student shall be declared to have passed a theory course only if they satisfy both of the following mandatory conditions:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Condition A (End-Semester Exam)</b>: Secure not less than <b>40% marks</b> in the End-Semester Examination.<br/>"
        "• <b>Condition B (Overall Aggregate)</b>: Secure not less than <b>50% marks</b> in the aggregate (Continuous Assessment marks + End-Semester Examination marks combined).",
        body_style
    ))
    story.append(Paragraph(
        "6.1.2. <b>Grading Scale & Grade Point Averages</b>:<br/>"
        "Letter grades are awarded based on total normalized marks:<br/>"
        "- Grade 'S' (90-100%): 10 Grade Points (Outstanding)<br/>"
        "- Grade 'A' (80-89%): 9 Grade Points (Excellent)<br/>"
        "- Grade 'B' (70-79%): 8 Grade Points (Very Good)<br/>"
        "- Grade 'C' (60-69%): 7 Grade Points (Good)<br/>"
        "- Grade 'D' (55-59%): 6 Grade Points (Fair)<br/>"
        "- Grade 'E' (50-54%): 5 Grade Points (Pass)<br/>"
        "- Grade 'F' (&lt;50% aggregate or &lt;40% end-sem): 0 Grade Points (Fail/Re-appear)",
        body_style
    ))
    story.append(Paragraph(
        "6.1.3. <b>Re-evaluation</b>: Students may apply for re-evaluation of answer scripts within 10 days of results declaration with a non-refundable scrutiny fee.",
        body_style
    ))

    doc.build(story)


def create_regulations_update_2024_docx(file_path: str):
    """Generate DOCX for Academic Regulations Update Circular 2024-2025."""
    doc = docx.Document()

    h = doc.add_heading("ACADEMIC COUNCIL NOTIFICATION & REGULATORY AMENDMENT", level=0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER

    meta_p = doc.add_paragraph("Circular Ref: AC/REG/2024/78-B | Date of Notification: July 15, 2024 | Effective: Academic Year 2024-2025 Onwards")
    meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("Issued by: Office of the Academic Dean & Registrar | Applicable to: All B.Tech and M.Tech Students")

    doc.add_heading("Preamble & Superseding Clause", level=1)
    doc.add_paragraph(
        "In exercise of powers conferred under Academic Statute Article 12, the Academic Council has approved revisions to the "
        "Academic Regulations Handbook. The provisions herein SUPERSEDE Section 4.2 and Section 5.1 of the 2023 Handbook with immediate effect for the 2024-2025 academic session."
    )

    doc.add_heading("Section 1: Revised Attendance Policy (Supersedes 2023 Section 4.2)", level=1)
    doc.add_paragraph(
        "1.1. <b>Mandatory Minimum Attendance</b>: In order to ensure rigorous scholarly engagement, the minimum attendance threshold is hereby revised to <b>80% attendance</b> across all instructional contact periods (lectures, tutorials, and laboratories).",
    )
    doc.add_paragraph(
        "1.2. <b>Condonation Guidelines & Restrictions</b>: Condonation of attendance shortage may be granted by the Vice Chancellor strictly on verified medical grounds or approved sports/academic representation, ONLY for students possessing attendance <b>between 70% and 79%</b>. "
        "No condonation shall be entertained without prior recommendation from the College Medical Board.",
    )
    doc.add_paragraph(
        "1.3. <b>Revised Condonation Fee</b>: The condonation fee is revised to <b>INR 1,500</b> per semester (superseding the earlier fee of INR 500).",
    )
    doc.add_paragraph(
        "1.4. <b>Strict Detention Threshold</b>: Any student possessing less than <b>70% attendance</b> shall be summarily detained and barred from writing semester examinations without exception.",
    )

    doc.add_heading("Section 2: Revised Assessment Weights (Supersedes 2023 Internal Ratios)", level=1)
    doc.add_paragraph(
        "2.1. Continuous Internal Assessment (CIA) weightage is enhanced from 30% to <b>40%</b> of the course total.\n"
        "2.2. The End-Semester Final Examination weightage is established at <b>60%</b>.\n"
        "2.3. Minimum passing score of 40% in end-semester examination and 50% aggregate remains in effect."
    )

    doc.save(file_path)


def create_midterm_notice_pdf(file_path: str):
    """Generate PDF for Midterm Examination Notice Fall 2024."""
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading1'],
        fontSize=15,
        leading=19,
        textColor=colors.HexColor('#0F172A'),
        alignment=1,
        spaceAfter=12
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=8
    )

    story = [
        Paragraph("OFFICE OF THE CONTROLLER OF EXAMINATIONS", header_style),
        Paragraph("<b>EXAMINATION NOTIFICATION: FALL SEMESTER MIDTERM EXAMINATIONS 2024</b>", ParagraphStyle('Sub', parent=body_style, alignment=1, textColor=colors.HexColor('#B91C1C'))),
        Paragraph("Ref No: COE/MID/2024/09 | Date of Issue: <b>October 5, 2024</b> | Academic Year: 2024-2025", ParagraphStyle('Meta', parent=body_style, alignment=1)),
        Spacer(1, 15),
        Paragraph("<b>1. Midterm Examination Schedule:</b>", ParagraphStyle('BoldH', parent=body_style, fontName='Helvetica-Bold')),
        Paragraph("The Fall 2024 Midterm Examinations for all second, third, and fourth-year B.Tech students will commence on <b>October 21, 2024</b> and conclude on <b>October 28, 2024</b>. Daily sessions will be conducted in Morning (09:30 AM - 11:30 AM) and Afternoon (02:00 PM - 04:00 PM) slots.", body_style),
        Paragraph("<b>2. Hall Ticket Release and Clearance:</b>", ParagraphStyle('BoldH', parent=body_style, fontName='Helvetica-Bold')),
        Paragraph("Hall tickets will be made available for download on the student ERP portal from <b>October 14, 2024</b> (05:00 PM onwards).", body_style),
        Paragraph("<b>Mandatory Clearances for Hall Ticket Generation:</b><br/>"
                  "a) Satisfactory attendance record (minimum 80% as per Circular AC/REG/2024/78-B).<br/>"
                  "b) Zero pending tuition, hostel, or examination fee arrears.<br/>"
                  "c) No disciplinary holds recorded with the Proctorial Board.", body_style),
        Paragraph("<b>3. Examination Regulations & Prohibited Devices:</b>", ParagraphStyle('BoldH', parent=body_style, fontName='Helvetica-Bold')),
        Paragraph("Students must carry a printed physical hall ticket along with their official University Identity Card. "
                  "Smartphones, smartwatches, programmable calculators, Bluetooth earpieces, and unauthorized reference sheets are strictly prohibited inside examination halls. Possession of prohibited devices will result in immediate disqualification under malpractice ordinance Article 9.", body_style),
        Spacer(1, 15),
        Paragraph("Sd/-<br/><b>Dr. K. S. Ramanujam</b><br/>Controller of Examinations", ParagraphStyle('Sign', parent=body_style, alignment=2))
    ]

    doc.build(story)


def create_fee_extension_txt(file_path: str):
    """Generate TXT for Semester Fee Deadline Extension Notice."""
    content = """OFFICE OF THE DEAN OF ACADEMIC AFFAIRS
CIRCULAR / ADMINISTRATIVE NOTICE
Ref: DAA/FEE/NOT/2024/42
Date of Issue: October 28, 2024
Academic Session: Fall Semester 2024-2025

SUBJECT: EXTENSION OF FALL 2024 SEMESTER TUITION FEE DEADLINE

In response to numerous student representations regarding banking network downtime and regional festive holidays during the final week of October, the University Competent Authority has approved an extension of the Fall 2024 semester tuition fee payment deadline.

Key Directives:
1. Original Fee Payment Deadline: October 31, 2024.
2. Revised & Extended Fee Payment Deadline: NOVEMBER 15, 2024 (11:59 PM IST).
3. Waiver of Late Surcharge: No late fine or administrative penalty shall be levied for payments completed on or before November 15, 2024.
4. Consequences of Non-Payment by Revised Date: Students failing to clear their semester dues by November 15, 2024 will face automatic de-registration of end-semester exam registration and withholding of portal grade reports.
5. Payment Mode: All payments must be processed exclusively through the University Online Payment Gateway. Cash and offline challans will not be accepted.

By Order of the Vice Chancellor,
Prof. Meenakshi Sundaram
Dean of Academic Affairs
University Administrative Complex
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    target = os.path.join(os.path.dirname(__file__), "..", "data", "sample_documents")
    generate_sample_corpus(target)
