"""
Demo PDF Generator for AI-Powered Campus Helpdesk Assistant.
Generates an official-looking synthetic university policy PDF in data/demo/
with visible 'DEMO DATA – NOT OFFICIAL UNIVERSITY POLICY' headers/watermarks on every page,
deliberate policy conflicts (e.g. Section 4.2 vs Section 9.1 late fees),
an unrelated topic (Cafeteria Green Composting), and departmental directories.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfgen import canvas

DEMO_DIR = Path(__file__).resolve().parent
OUTPUT_PDF = DEMO_DIR / "university_policy_demo.pdf"


class NumberedCanvas(canvas.Canvas):
    """Adds persistent demo warning header and page numbers to every page."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        
        # Top Persistent Banner: DEMO DATA NOTICE
        self.setFillColor(colors.HexColor("#DC2626"))
        self.rect(36, 755, 540, 20, fill=True, stroke=False)
        self.setFillColor(colors.white)
        self.setFont("Helvetica-Bold", 8)
        self.drawCentredString(306, 761, "DEMO DATA – NOT OFFICIAL UNIVERSITY POLICY (FOR TESTING & EVALUATION ONLY)")

        # University Header
        self.setFillColor(colors.HexColor("#0B1F3A"))
        self.setFont("Helvetica-Bold", 9)
        self.drawString(36, 740, "APEX METROPOLITAN UNIVERSITY | ACADEMIC POLICIES HANDBOOK")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.75)
        self.line(36, 735, 576, 735)

        # Bottom Footer
        self.line(36, 45, 576, 45)
        self.setFillColor(colors.HexColor("#64748B"))
        self.setFont("Helvetica", 8)
        self.drawString(36, 32, "Apex Metropolitan University · Official Registrar Archive · Ref: AMU-POL-2026")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 32, page_str)
        
        self.restoreState()


def build_pdf():
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=60,
        bottomMargin=55
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0B1F3A"),
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=14,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )

    callout_style = ParagraphStyle(
        "Callout",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=4,
        spaceAfter=6
    )

    story = []

    # ================= PAGE 1 =================
    story.append(Paragraph("Student Academic Regulations & Campus Code", title_style))
    story.append(Paragraph("Academic Year 2026–2027 · Document Reference: AMU-HANDBOOK-V2", callout_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Section 1: General Academic Standing & Enrollment", h1_style))
    story.append(Paragraph("<b>1.1 Semester Credit Limits:</b> Full-time undergraduate students are required to maintain a minimum of 12 credits and may register for a maximum of 20 credits per semester. Registration beyond 20 credits requires formal dean approval.", body_style))
    
    story.append(Paragraph("<b>1.2 Mandatory Attendance Requirements:</b> Regular and punctual attendance in all scheduled lectures, tutorials, and practical laboratory sessions is compulsory. Every enrolled undergraduate student must maintain a minimum attendance of <b>75%</b> in each registered course to be eligible to sit for the End-Semester Final Examination. Students whose attendance falls between 65% and 74% due to documented medical hospitalization may apply for condonation through the Chief Medical Officer (CMO) and the Dean of Academic Affairs. Students with attendance below 65% receive an automatic 'FA' (Failure due to Attendance) grade and must repeat the course.", body_style))

    story.append(Paragraph("<b>1.3 Grading Scale & Grade Point Average:</b> Academic performance is graded on a 10-point scale: O (Outstanding, 10.0), A+ (Excellent, 9.0), A (Very Good, 8.0), B+ (Good, 7.0), B (Above Average, 6.0), C (Pass, 5.0), and F (Fail, 0.0). A Minimum Cumulative Grade Point Average (CGPA) of 5.00 is required for graduation in all undergraduate bachelor degree programs.", body_style))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Section 2: Examination Procedures & Revaluation", h1_style))
    story.append(Paragraph("<b>2.1 Examination Hall Regulations:</b> Students must display their official University Physical ID Card and Exam Admit Card at the entrance of the examination hall. Electronic devices including smartwatches, mobile phones, and programmable calculators are strictly prohibited.", body_style))
    story.append(Paragraph("<b>2.2 Answer Script Re-evaluation:</b> A student dissatisfied with their evaluated grade may apply for Answer Script Photocopy and Revaluation within 15 calendar days from the date of online result publication. The revaluation application fee is non-refundable at $25 per course subject.", body_style))

    story.append(PageBreak())

    # ================= PAGE 2 =================
    story.append(Paragraph("Section 3: Course Registration Procedures", h1_style))
    story.append(Paragraph("<b>3.1 Regular Course Enrollment:</b> Online course registration opens via the Student Enterprise Portal two weeks prior to the commencement of instructional classes. All core curriculum and departmental elective selections must be submitted and advisor-approved by 5:00 PM on Friday of orientation week.", body_style))

    story.append(Paragraph("Section 4: Course Changes & Registration Fees (Deliberate Conflict Policy A)", h1_style))
    story.append(Paragraph("<b>4.1 Add/Drop Course Period:</b> Students may freely add or drop registered elective courses during the first ten (10) instructional days of the semester without academic transcript penalty.", body_style))
    
    # DELIBERATE CONFLICT CLAUSE 1
    story.append(Paragraph("<b>4.2 Late Course Registration Fee:</b> Any undergraduate or graduate student who fails to complete course enrollment prior to the first day of instruction may register during the late registration window (Days 1 to 5 of the semester). <u>The late course registration fee is strictly $50</u>, payable via the student financial portal or at the Cashier Window in the Administrative Block.", body_style))

    story.append(Paragraph("<b>4.3 Course Withdrawal Deadline:</b> Formal course withdrawal with a 'W' grade on the official transcript is permissible until the end of the eighth (8th) instructional week. Tuition refunds are not granted for course withdrawals executed after Week 3.", body_style))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Section 5: Academic Integrity & Misconduct Sanctions", h1_style))
    story.append(Paragraph("<b>5.1 Plagiarism & AI Usage Standards:</b> All submitted coursework, laboratory project code, and dissertations must represent original student scholarship. Unattributed text, verbatim copying without quotation, or unauthorized generative AI tool output exceeding 15% similarity index will result in a referral to the University Academic Integrity Board. First offenses incur a zero score on the assignment; repeat offenses result in course failure and disciplinary probation.", body_style))

    story.append(PageBreak())

    # ================= PAGE 3 =================
    story.append(Paragraph("Section 6: Campus Facilities & Student Amenities", h1_style))
    story.append(Paragraph("<b>6.1 Central University Library Guidelines:</b> The university library operates Monday through Saturday from 8:00 AM to 10:00 PM during regular instruction, and 24 hours daily during final exam periods. Undergraduate students may borrow up to four (4) catalog volumes for a duration of 14 calendar days. Late book returns incur an overdue fine of $1.00 per day per volume.", body_style))

    # UNRELATED TOPIC
    story.append(Paragraph("Section 7: Campus Sustainability & Cafeteria Green Composting", h1_style))
    story.append(Paragraph("<b>7.1 Organic Waste Separation:</b> Under the Apex Green Campus Initiative 2026, all student dining venues and cafeterias mandate pre-sorting of food waste. Solid organic discards must be deposited into green solar-aerated compost bins located at cafeteria exit gates before 9:00 PM nightly. Single-use plastic drinkware is banned across all campus premises.", body_style))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Section 8: Campus Administrative Directory & Contact Points", h1_style))
    story.append(Paragraph("Students requiring specialized administrative assistance should contact the following designated campus departments:", body_style))

    directory_data = [
        ["Department / Office", "Location", "Operating Hours", "Contact Email"],
        ["Office of Academic Affairs", "Admin Block, Rm 104", "Mon–Fri, 9:00 AM – 5:00 PM", "academics@amu.edu"],
        ["Accounts & Student Finance", "Admin Block, Rm 102", "Mon–Fri, 9:30 AM – 4:00 PM", "accounts@amu.edu"],
        ["Controller of Examinations", "Exam Complex, Ground Floor", "Mon–Fri, 10:00 AM – 4:30 PM", "examdesk@amu.edu"],
        ["Central University Library", "Knowledge Tower, Level 1", "Mon–Sat, 8:00 AM – 10:00 PM", "library@amu.edu"],
        ["Hostel & Student Housing", "Student Activity Center Rm 201", "Mon–Fri, 9:00 AM – 6:00 PM", "housing@amu.edu"],
        ["Campus IT Services", "Tech Annex, Rm 204", "Mon–Sat, 8:30 AM – 7:00 PM", "itsupport@amu.edu"],
    ]

    t = Table(directory_data, colWidths=[130, 130, 130, 140])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0B1F3A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t)

    story.append(PageBreak())

    # ================= PAGE 4 =================
    story.append(Paragraph("Section 9: Supplementary Academic Bylaws & Special Notices", h1_style))
    
    # DELIBERATE CONFLICT CLAUSE 2
    story.append(Paragraph("<b>9.1 Supplementary Notice on Registration Penalties (Deliberate Conflict Policy B):</b>", h2_style))
    story.append(Paragraph("<b>Important Late Enrollment Directive:</b> In accordance with Executive Council Circular EC-2026-44, any enrolled student who registers for courses after the published schedule or attends lectures prior to formal enrollment approval <u>shall be assessed an institutional late registration fee of $100</u>. This fee must be remitted directly to the Bursar's Office before examination hall ticket issuance.", body_style))
    story.append(Paragraph("<i>[Note for QA Evaluation: Section 9.1 deliberately contradicts Section 4.2 regarding the late registration fee amount ($100 vs $50). The AI system must flag this conflict rather than guessing.]</i>", callout_style))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>9.2 Residential Life & Hostel Regulations:</b>", h2_style))
    story.append(Paragraph("Hostel residents must adhere to campus curfew regulations. Main residential gates close at 10:30 PM on Sunday through Thursday, and at 11:30 PM on Fridays and Saturdays. Overnight leave requires digital parent/guardian verification through the Campus Hostel Portal at least 24 hours in advance.", body_style))

    story.append(Paragraph("<b>9.3 Student Grievance Redressal Committee:</b>", h2_style))
    story.append(Paragraph("Any student encountering academic, residential, or discrimination difficulties may submit a formal confidential petition to the University Student Grievance Committee (Office of Student Welfare, SAC Room 302, email: grievance@amu.edu). All appeals are adjudicated within ten (10) academic business days.", body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated demo PDF at: {OUTPUT_PDF}")


if __name__ == "__main__":
    build_pdf()
