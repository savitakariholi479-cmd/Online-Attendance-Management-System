import os
import qrcode
from PIL import Image, ImageDraw, ImageFont
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'presentation_assets')
os.makedirs(ASSETS_DIR, exist_ok=True)

# Try loading nice Windows fonts
def get_font(size, bold=False):
    font_path = "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"
    if not os.path.exists(font_path):
        font_path = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()

# ----------------- Visual Generators ----------------- #

def create_hero_visual():
    img = Image.new('RGB', (1000, 700), color='#0f172a')
    draw = ImageDraw.Draw(img)

    # Background gradient glow
    for r in range(250, 0, -5):
        alpha = int((1 - r / 250) * 40)
        draw.ellipse([500 - r, 350 - r, 500 + r, 350 + r], fill=(37, 99, 235))

    # Center QR card
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data("SMARTATTEND_ONLINE_ATTENDANCE_SYSTEM_DEMO")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1e293b", back_color="#ffffff").convert('RGB')
    qr_w, qr_h = qr_img.size

    # Card background
    card_x, card_y = 300, 150
    card_w, card_h = 400, 420
    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=24, fill='#ffffff', outline='#3b82f6', width=4)

    # Paste QR in card
    img.paste(qr_img, (card_x + (card_w - qr_w) // 2, card_y + 40))

    # Text in card
    font_bold = get_font(22, bold=True)
    font_sub = get_font(14)
    draw.text((card_x + 200, card_y + qr_h + 55), "CS301: LIVE LECTURE", fill='#0f172a', font=font_bold, anchor="mm")
    draw.text((card_x + 200, card_y + qr_h + 85), "Scan to Record Attendance", fill='#2563eb', font=font_sub, anchor="mm")

    # Floating Badge 1 (Top Left)
    draw.rounded_rectangle([120, 180, 290, 240], radius=16, fill='#1e293b', outline='#10b981', width=2)
    draw.text((205, 210), "✓ Anti-Proxy Secured", fill='#34d399', font=get_font(15, bold=True), anchor="mm")

    # Floating Badge 2 (Bottom Right)
    draw.rounded_rectangle([710, 430, 900, 500], radius=16, fill='#1e293b', outline='#38bdf8', width=2)
    draw.text((805, 455), "88.5% Real-Time", fill='#ffffff', font=get_font(15, bold=True), anchor="mm")
    draw.text((805, 478), "Percentage Tracking", fill='#38bdf8', font=get_font(12), anchor="mm")

    path = os.path.join(ASSETS_DIR, 'hero_visual.png')
    img.save(path)
    return path

def create_comparison_visual():
    img = Image.new('RGB', (1000, 650), color='#f8fafc')
    draw = ImageDraw.Draw(img)

    f_title = get_font(22, bold=True)
    f_body = get_font(15)
    f_badge = get_font(14, bold=True)

    # Left Card: Traditional System
    draw.rounded_rectangle([60, 60, 470, 580], radius=20, fill='#ffffff', outline='#fecdd3', width=2)
    draw.rounded_rectangle([90, 90, 440, 140], radius=12, fill='#ffe4e6')
    draw.text((265, 115), "Traditional Paper Roll-Call", fill='#e11d48', font=f_title, anchor="mm")

    points_old = [
        "❌ Wastes 10-15 mins of every lecture",
        "❌ High risk of proxy attendance (friends sign)",
        "❌ Manual calculation of percentages",
        "❌ Human errors and misplaced attendance sheets",
        "❌ Zero real-time visibility for students",
        "❌ Last-minute shortage surprises before exams"
    ]
    y = 180
    for p in points_old:
        draw.text((90, y), p, fill='#475569', font=f_body)
        y += 65

    # Right Card: SmartAttend System
    draw.rounded_rectangle([530, 60, 940, 580], radius=20, fill='#ffffff', outline='#bbf7d0', width=2)
    draw.rounded_rectangle([560, 90, 910, 140], radius=12, fill='#dcfce7')
    draw.text((735, 115), "SmartAttend QR System", fill='#15803d', font=f_title, anchor="mm")

    points_new = [
        "✅ Attendance marked in under 5 seconds",
        "✅ Dynamic encrypted QR codes (No proxies)",
        "✅ 100% automated real-time percentage %",
        "✅ Instant low-attendance shortage alerts (<75%)",
        "✅ Complete student self-service dashboard",
        "✅ One-click CSV/Excel export for admin"
    ]
    y = 180
    for p in points_new:
        draw.text((560, y), p, fill='#1e293b', font=f_body)
        y += 65

    path = os.path.join(ASSETS_DIR, 'comparison_visual.png')
    img.save(path)
    return path

def create_architecture_visual():
    img = Image.new('RGB', (1000, 650), color='#ffffff')
    draw = ImageDraw.Draw(img)

    f_box = get_font(16, bold=True)
    f_sub = get_font(12)
    f_arrow = get_font(24, bold=True)

    # 4 Architecture Steps Flow
    steps = [
        ("1. Faculty / Teacher", "Selects Course & Lecture\nGenerates Dynamic QR\nSets Expiration Timer", '#2563eb', '#eff6ff'),
        ("2. Display & Projector", "QR Code on Screen\nAuto-refreshing feed\nBackup Session Code", '#4f46e5', '#eef2ff'),
        ("3. Student Camera Scan", "Camera checks token\nAnti-proxy validation\nSingle-scan enforcement", '#059669', '#ecfdf5'),
        ("4. Real-Time Engine", "Calculates % per subject\nUpdates 75% exam status\nGenerates CSV Reports", '#0284c7', '#f0f9ff')
    ]

    x = 40
    for i, (title, desc, color, bg) in enumerate(steps):
        draw.rounded_rectangle([x, 150, x + 200, 480], radius=18, fill=bg, outline=color, width=3)
        # Header banner
        draw.rounded_rectangle([x, 150, x + 200, 210], radius=18, fill=color)
        draw.text((x + 100, 180), title, fill='#ffffff', font=f_box, anchor="mm")

        # Description text
        lines = desc.split('\n')
        ly = 260
        for l in lines:
            draw.text((x + 100, ly), f"• {l}", fill='#334155', font=f_sub, anchor="mm")
            ly += 45

        # Arrow to next
        if i < 3:
            draw.text((x + 225, 315), "➔", fill='#94a3b8', font=f_arrow, anchor="mm")

        x += 245

    path = os.path.join(ASSETS_DIR, 'architecture_visual.png')
    img.save(path)
    return path

def create_student_gauge_visual():
    img = Image.new('RGB', (1000, 650), color='#ffffff')
    draw = ImageDraw.Draw(img)

    # Big percentage ring
    center = (280, 320)
    radius = 160
    # Background circle
    draw.ellipse([center[0]-radius, center[1]-radius, center[0]+radius, center[1]+radius], outline='#e2e8f0', width=26)
    # Arc (88.5% of 360 = ~318 deg)
    draw.arc([center[0]-radius, center[1]-radius, center[0]+radius, center[1]+radius], start=-90, end=228, fill='#10b981', width=26)

    f_pct = get_font(52, bold=True)
    f_lbl = get_font(18, bold=True)
    f_sub = get_font(14)

    draw.text(center, "88.5%", fill='#0f172a', font=f_pct, anchor="mm")
    draw.text((center[0], center[1] + 50), "Overall Attendance", fill='#64748b', font=f_sub, anchor="mm")

    # Status Pill
    draw.rounded_rectangle([160, 520, 400, 570], radius=25, fill='#dcfce7', outline='#86efac', width=2)
    draw.text((280, 545), "✓ Eligible for Exams (≥75%)", fill='#166534', font=f_lbl, anchor="mm")

    # Right side: Subject Breakdown Cards
    subjects = [
        ("CS301: Data Structures", "9 / 10 Classes", "90.0%", '#10b981'),
        ("CS304: Web Technologies", "5 / 5 Classes", "100.0%", '#10b981'),
        ("MA301: Discrete Maths", "9 / 9 Classes", "100.0%", '#10b981'),
        ("CS302: DBMS (Low Warning)", "3 / 7 Classes", "42.9%", '#ef4444')
    ]

    sy = 100
    for name, counts, pct_str, col in subjects:
        draw.rounded_rectangle([520, sy, 940, sy + 105], radius=16, fill='#f8fafc', outline='#e2e8f0', width=2)
        draw.text((545, sy + 25), name, fill='#0f172a', font=get_font(16, bold=True))
        draw.text((545, sy + 55), counts, fill='#64748b', font=f_sub)
        draw.text((915, sy + 35), pct_str, fill=col, font=get_font(22, bold=True), anchor="rm")
        # mini progress bar
        draw.rounded_rectangle([545, sy + 80, 915, sy + 88], radius=4, fill='#e2e8f0')
        w = int((float(pct_str.replace('%', '')) / 100) * (915 - 545))
        draw.rounded_rectangle([545, sy + 80, 545 + w, sy + 88], radius=4, fill=col)
        sy += 130

    path = os.path.join(ASSETS_DIR, 'student_gauge_visual.png')
    img.save(path)
    return path

def create_security_visual():
    img = Image.new('RGB', (1000, 650), color='#ffffff')
    draw = ImageDraw.Draw(img)

    f_title = get_font(18, bold=True)
    f_body = get_font(14)

    cards = [
        ("🔐 Dynamic Encryption", "Each lecture generates a unique cryptographically signed session token. Screenshots cannot be reused.", 70, 80),
        ("⏳ Time-Bound Expiration", "QRs automatically expire after 5 to 30 minutes, preventing late submissions and remote check-ins.", 530, 80),
        ("🚫 Duplicate Prevention", "Strict database constraints block multiple scans from the same student roll number in a session.", 70, 360),
        ("🛡️ Audit Logging", "Complete timestamp, scan method (QR vs manual), and faculty override history are permanently tracked.", 530, 360)
    ]

    for title, desc, cx, cy in cards:
        draw.rounded_rectangle([cx, cy, cx + 400, cy + 220], radius=18, fill='#f8fafc', outline='#cbd5e1', width=2)
        draw.rounded_rectangle([cx + 20, cy + 20, cx + 380, cy + 70], radius=10, fill='#eff6ff')
        draw.text((cx + 200, cy + 45), title, fill='#1d4ed8', font=f_title, anchor="mm")

        # multiline wrap
        words = desc.split(' ')
        lines = []
        curr = ""
        for w in words:
            if len(curr + " " + w) > 36:
                lines.append(curr)
                curr = w
            else:
                curr += (" " + w if curr else w)
        if curr: lines.append(curr)

        ly = cy + 105
        for l in lines:
            draw.text((cx + 200, ly), l, fill='#475569', font=f_body, anchor="mm")
            ly += 30

    path = os.path.join(ASSETS_DIR, 'security_visual.png')
    img.save(path)
    return path

def create_reports_visual():
    img = Image.new('RGB', (1000, 650), color='#ffffff')
    draw = ImageDraw.Draw(img)

    f_kpi_num = get_font(32, bold=True)
    f_kpi_lbl = get_font(13)

    # 3 Top KPI Badges
    kpis = [
        ("12", "Total Lectures Conducted", '#2563eb', 60),
        ("82.4%", "Average Class Attendance", '#10b981', 370),
        ("2 Students", "Attendance Shortage (<75%)", '#ef4444', 680)
    ]

    for num, lbl, col, kx in kpis:
        draw.rounded_rectangle([kx, 40, kx + 260, 140], radius=16, fill='#f8fafc', outline='#e2e8f0', width=2)
        draw.text((kx + 130, 75), num, fill=col, font=f_kpi_num, anchor="mm")
        draw.text((kx + 130, 115), lbl, fill='#64748b', font=f_kpi_lbl, anchor="mm")

    # Table Simulation
    draw.rounded_rectangle([60, 170, 940, 590], radius=16, fill='#ffffff', outline='#cbd5e1', width=2)
    draw.rounded_rectangle([60, 170, 940, 220], radius=16, fill='#1e293b')
    draw.text((120, 195), "Roll No", fill='#ffffff', font=get_font(14, bold=True))
    draw.text((260, 195), "Student Name", fill='#ffffff', font=get_font(14, bold=True))
    draw.text((480, 195), "Attended / Total", fill='#ffffff', font=get_font(14, bold=True))
    draw.text((680, 195), "Percentage", fill='#ffffff', font=get_font(14, bold=True))
    draw.text((830, 195), "Status", fill='#ffffff', font=get_font(14, bold=True))

    rows = [
        ("2024CS01", "Aarav Sharma", "11 / 12", "91.7%", "Eligible", '#10b981'),
        ("2024CS02", "Ananya Patel", "7 / 12", "58.3%", "Shortage", '#ef4444'),
        ("2024CS03", "Maaz Khan", "12 / 12", "100.0%", "Eligible", '#10b981'),
        ("2024CS04", "Rohan Gupta", "10 / 12", "83.3%", "Eligible", '#10b981'),
        ("2024CS05", "Priya Nair", "12 / 12", "100.0%", "Eligible", '#10b981'),
        ("2024CS06", "Kabir Singh", "8 / 12", "66.7%", "Shortage", '#ef4444')
    ]

    ry = 245
    for r in rows:
        draw.text((120, ry), r[0], fill='#0f172a', font=get_font(14))
        draw.text((260, ry), r[1], fill='#334155', font=get_font(14, bold=True))
        draw.text((500, ry), r[2], fill='#64748b', font=get_font(14))
        draw.text((700, ry), r[3], fill=r[5], font=get_font(14, bold=True))

        # Status badge
        badge_bg = '#dcfce7' if r[4] == 'Eligible' else '#fee2e2'
        draw.rounded_rectangle([820, ry - 6, 915, ry + 22], radius=6, fill=badge_bg)
        draw.text((867, ry + 8), r[4], fill=r[5], font=get_font(12, bold=True), anchor="mm")

        draw.line([60, ry + 35, 940, ry + 35], fill='#f1f5f9', width=1)
        ry += 55

    path = os.path.join(ASSETS_DIR, 'reports_visual.png')
    img.save(path)
    return path

def hex_to_rgb(h):
    h = h.lstrip('#')
    return RGBColor(*(int(h[i:i+2], 16) for i in (0, 2, 4)))

# ----------------- PowerPoint Builder ----------------- #

def build_presentation():
    prs = pptx.Presentation()
    # 16:9 Widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Pre-generate visual assets
    print("Generating visual diagrams & photos...")
    hero_img = create_hero_visual()
    comp_img = create_comparison_visual()
    arch_img = create_architecture_visual()
    gauge_img = create_student_gauge_visual()
    sec_img = create_security_visual()
    rep_img = create_reports_visual()

    # Color Palette Definitions
    COLOR_NAVY = RGBColor(15, 23, 42)     # #0f172a
    COLOR_BLUE = RGBColor(37, 99, 235)    # #2563eb
    COLOR_DARK_BLUE = RGBColor(30, 58, 138)
    COLOR_GRAY = RGBColor(71, 85, 105)    # #475569
    COLOR_LIGHT = RGBColor(248, 250, 252)
    COLOR_WHITE = RGBColor(255, 255, 255)
    COLOR_GREEN = RGBColor(16, 185, 129)

    # Helper to add standard content slide header
    def add_header(slide, title_text, category_text="ONLINE ATTENDANCE MANAGEMENT SYSTEM"):
        # Category tag
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.4))
        tf_cat = cat_box.text_frame
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = COLOR_BLUE

        # Title
        t_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.5), Inches(0.8))
        tf_t = t_box.text_frame
        p_t = tf_t.paragraphs[0]
        p_t.text = title_text
        p_t.font.size = Pt(26)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_NAVY

    # ==================== SLIDE 1: TITLE SLIDE ==================== #
    s1 = prs.slides.add_slide(blank_layout)
    # Dark background shape
    bg = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = COLOR_NAVY
    bg.line.fill.background()

    # Title box
    t1 = s1.shapes.add_textbox(Inches(0.9), Inches(1.8), Inches(6.5), Inches(3.8))
    tf1 = t1.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "SMARTATTEND"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = RGBColor(56, 189, 248) # Sky blue tag

    p = tf1.add_paragraph()
    p.text = "Online Attendance Management System"
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_after = Pt(14)

    p = tf1.add_paragraph()
    p.text = "A modern web application featuring Dynamic QR Code Scanning, Automated Attendance Percentage Tracking, and Exam Eligibility Monitoring."
    p.font.size = Pt(16)
    p.font.color.rgb = RGBColor(203, 213, 225)
    p.space_after = Pt(20)

    p = tf1.add_paragraph()
    p.text = "👨‍🏫 Teacher QR Generation  •  👨‍🎓 Student Camera Scan  •  📊 Real-Time Analytics"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = RGBColor(52, 211, 153)

    # Insert Hero image
    s1.shapes.add_picture(hero_img, Inches(7.2), Inches(1.2), width=Inches(5.4))

    # ==================== SLIDE 2: THE PROBLEM STATEMENT ==================== #
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "The Problem: Why Traditional Attendance Fails")

    # Left text description
    tx2 = s2.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(5.8), Inches(5.2))
    tf2 = tx2.text_frame
    tf2.word_wrap = True

    points_s2 = [
        ("Time Inefficiency", "Taking roll-calls manually consumes 10-15 minutes of an hour lecture, reducing actual teaching time by over 20%."),
        ("Buddy Punching & Proxies", "Paper signature sheets and verbal call-outs make it trivial for students to mark attendance for absent friends."),
        ("Error-Prone Percentage Calculation", "Faculty spend hours manually tallying registers at semester end, resulting in computation mistakes."),
        ("Lack of Student Awareness", "Students have zero real-time visibility into their subject percentage, leading to sudden exam debarment notices.")
    ]

    for title, desc in points_s2:
        p1 = tf2.add_paragraph()
        p1.text = f"• {title}"
        p1.font.bold = True
        p1.font.size = Pt(16)
        p1.font.color.rgb = COLOR_NAVY
        p2 = tf2.add_paragraph()
        p2.text = f"   {desc}"
        p2.font.size = Pt(13)
        p2.font.color.rgb = COLOR_GRAY
        p2.space_after = Pt(12)

    s2.shapes.add_picture(comp_img, Inches(6.8), Inches(1.5), width=Inches(5.8))

    # ==================== SLIDE 3: SYSTEM ARCHITECTURE ==================== #
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "System Workflow & End-to-End Architecture")

    # Top summary
    tx3 = s3.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.8), Inches(0.8))
    tf3 = tx3.text_frame
    tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "SmartAttend replaces manual workflows with a 4-step dynamic QR cycle backed by secure session tokens and an automated SQLite calculation engine."
    p.font.size = Pt(15)
    p.font.color.rgb = COLOR_GRAY

    s3.shapes.add_picture(arch_img, Inches(0.8), Inches(2.2), width=Inches(11.7))

    # ==================== SLIDE 4: TEACHER PORTAL ==================== #
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "Faculty Portal: Dynamic QR Generation & Live Monitor")

    tx4 = s4.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(5.8), Inches(5.2))
    tf4 = tx4.text_frame
    tf4.word_wrap = True

    pts4 = [
        ("Dynamic QR Code Generation", "Instructors select subject and lecture topic, generating high-resolution QR codes encoded with secure UUID tokens."),
        ("Validity Timer & Auto Expiry", "Set custom session lifespan (5m, 15m, 30m, 1h). The system automatically disables attendance when the timer expires."),
        ("Fullscreen Projector Mode", "Designed specifically for classroom smartboards and projector screens with high-contrast, scalable display."),
        ("Live Turnout & Manual Override", "Live attendee feed auto-updates every 3 seconds. Faculty can also manually mark or adjust status (Present/Absent).")
    ]

    for title, desc in pts4:
        p1 = tf4.add_paragraph()
        p1.text = f"• {title}"
        p1.font.bold = True
        p1.font.size = Pt(16)
        p1.font.color.rgb = COLOR_NAVY
        p2 = tf4.add_paragraph()
        p2.text = f"   {desc}"
        p2.font.size = Pt(13)
        p2.font.color.rgb = COLOR_GRAY
        p2.space_after = Pt(12)

    s4.shapes.add_picture(hero_img, Inches(6.8), Inches(1.6), width=Inches(5.8))

    # ==================== SLIDE 5: STUDENT ATTENDANCE & PERCENTAGE ==================== #
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Student Dashboard: Attendance Percentage Tracking")

    tx5 = s5.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(5.8), Inches(5.2))
    tf5 = tx5.text_frame
    tf5.word_wrap = True

    pts5 = [
        ("Animated Percentage Gauge", "Overall attendance percentage calculated with a color-coded radial meter (Green ≥ 75%, Red < 75%)."),
        ("Exam Eligibility Status", "Displays clear status: 'Eligible for Exams' or 'Attendance Shortage Warning' based on university criteria."),
        ("Actionable Shortage Forecast", "Automatically tells students exactly how many consecutive upcoming classes they need to reach 75%."),
        ("Subject-Wise Breakdown", "Individual progress bars and attended/missed lecture counts for every course enrolled.")
    ]

    for title, desc in pts5:
        p1 = tf5.add_paragraph()
        p1.text = f"• {title}"
        p1.font.bold = True
        p1.font.size = Pt(16)
        p1.font.color.rgb = COLOR_NAVY
        p2 = tf5.add_paragraph()
        p2.text = f"   {desc}"
        p2.font.size = Pt(13)
        p2.font.color.rgb = COLOR_GRAY
        p2.space_after = Pt(12)

    s5.shapes.add_picture(gauge_img, Inches(6.8), Inches(1.6), width=Inches(5.8))

    # ==================== SLIDE 6: QR SCANNER & AUDIO CONFETTI ==================== #
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "Camera QR Scanner & Student Check-in Experience")

    tx6 = s6.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(5.8), Inches(5.2))
    tf6 = tx6.text_frame
    tf6.word_wrap = True

    pts6 = [
        ("Integrated Camera Scanner", "Powered by HTML5-QRCode with camera toggle (Front & Back camera) for smartphones, tablets, and laptops."),
        ("Web Audio API Chime & Confetti", "Instant celebratory audio confirmation and particle confetti feedback when attendance is successfully recorded."),
        ("Zero-Proxy Enforcement", "Duplicate scans from the same student account are immediately blocked with previous check-in timestamp."),
        ("Hardware-Free Fallbacks", "Includes manual 6-character session code entry and photo upload for students with damaged webcams.")
    ]

    for title, desc in pts6:
        p1 = tf6.add_paragraph()
        p1.text = f"• {title}"
        p1.font.bold = True
        p1.font.size = Pt(16)
        p1.font.color.rgb = COLOR_NAVY
        p2 = tf6.add_paragraph()
        p2.text = f"   {desc}"
        p2.font.size = Pt(13)
        p2.font.color.rgb = COLOR_GRAY
        p2.space_after = Pt(12)

    s6.shapes.add_picture(sec_img, Inches(6.8), Inches(1.6), width=Inches(5.8))

    # ==================== SLIDE 7: SECURITY & ANTI-PROXY ==================== #
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "Anti-Proxy Protection & Security Mechanisms")

    tx7 = s7.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(5.8), Inches(5.2))
    tf7 = tx7.text_frame
    tf7.word_wrap = True

    pts7 = [
        ("Dynamic Encrypted Tokens", "Tokens are cryptographically generated per session, making static photo sharing completely ineffective."),
        ("Strict Database Constraints", "SQLite table unique index on (session_id, student_id) prevents double-dipping at the database level."),
        ("Course Enrollment Validation", "Only students officially registered in the specific subject can record attendance."),
        ("Transparent Audit Logs", "All check-ins record exact timestamps and marking method (QR scan vs instructor manual override).")
    ]

    for title, desc in pts7:
        p1 = tf7.add_paragraph()
        p1.text = f"• {title}"
        p1.font.bold = True
        p1.font.size = Pt(16)
        p1.font.color.rgb = COLOR_NAVY
        p2 = tf7.add_paragraph()
        p2.text = f"   {desc}"
        p2.font.size = Pt(13)
        p2.font.color.rgb = COLOR_GRAY
        p2.space_after = Pt(12)

    s7.shapes.add_picture(sec_img, Inches(6.8), Inches(1.6), width=Inches(5.8))

    # ==================== SLIDE 8: REPORTS & CSV EXPORT ==================== #
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Administrative Analytics & CSV/Excel Export")

    tx8 = s8.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(5.8), Inches(5.2))
    tf8 = tx8.text_frame
    tf8.word_wrap = True

    pts8 = [
        ("Course-Wide Attendance Turnout", "High-level KPI metrics calculating total lectures, class average percentage, and students at risk."),
        ("Automated Shortage Detection", "Instantly flags any student below the 75% university requirement with red shortage badges."),
        ("One-Click Excel / CSV Export", "Generates official university spreadsheet reports with student roll numbers, names, attended, and eligibility."),
        ("Student Management System", "Faculty can add new students, edit roll numbers, and map courses with automatic roster propagation.")
    ]

    for title, desc in pts8:
        p1 = tf8.add_paragraph()
        p1.text = f"• {title}"
        p1.font.bold = True
        p1.font.size = Pt(16)
        p1.font.color.rgb = COLOR_NAVY
        p2 = tf8.add_paragraph()
        p2.text = f"   {desc}"
        p2.font.size = Pt(13)
        p2.font.color.rgb = COLOR_GRAY
        p2.space_after = Pt(12)

    s8.shapes.add_picture(rep_img, Inches(6.8), Inches(1.6), width=Inches(5.8))

    # ==================== SLIDE 9: TECH STACK ==================== #
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Technology Stack & Technical Implementation")

    # 4 Cards Layout
    tech_cards = [
        ("Backend Server", "Python 3.12 & Flask", "Lightweight, reliable REST API architecture handling session tokens, attendance calculations, and dynamic CSV streams.", '#2563eb', Inches(0.8), Inches(1.8)),
        ("Relational Database", "SQLite 3 Engine", "Zero-configuration SQL database with ACID compliance, relational foreign keys, and unique constraint enforcement.", '#059669', Inches(6.8), Inches(1.8)),
        ("Frontend & Styling", "Tailwind CSS & FontAwesome", "Responsive glassmorphism UI, accessible typography, SVG radial percentage ring, and mobile camera support.", '#4f46e5', Inches(0.8), Inches(4.4)),
        ("QR & Multimedia APIs", "HTML5-QRCode & Web Audio", "Browser-native webcam QR code scanner paired with synthesized double-tone audio feedback and Canvas confetti.", '#0284c7', Inches(6.8), Inches(4.4))
    ]

    for title, subtitle, desc, col, x, y in tech_cards:
        card = s9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(5.7), Inches(2.3))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_WHITE
        card.line.color.rgb = RGBColor(226, 232, 240)
        card.line.width = Pt(1.5)

        tx = s9.shapes.add_textbox(x + Inches(0.2), y + Inches(0.15), Inches(5.3), Inches(2.0))
        tf = tx.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title.upper()
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = hex_to_rgb(col)

        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(18)
        p2.font.bold = True
        p2.font.color.rgb = COLOR_NAVY
        p2.space_after = Pt(6)

        p3 = tf.add_paragraph()
        p3.text = desc
        p3.font.size = Pt(12)
        p3.font.color.rgb = COLOR_GRAY

    # ==================== SLIDE 10: CONCLUSION & FUTURE SCOPE ==================== #
    s10 = prs.slides.add_slide(blank_layout)
    bg10 = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg10.fill.solid()
    bg10.fill.fore_color.rgb = COLOR_NAVY
    bg10.line.fill.background()

    tx10 = s10.shapes.add_textbox(Inches(1.0), Inches(1.0), Inches(11.333), Inches(5.5))
    tf10 = tx10.text_frame
    tf10.word_wrap = True

    p = tf10.paragraphs[0]
    p.text = "CONCLUSION & FUTURE ENHANCEMENTS"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = RGBColor(56, 189, 248)

    p = tf10.add_paragraph()
    p.text = "Modernizing Classroom Attendance Management"
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_after = Pt(20)

    conclusions = [
        ("Saves 10-15 Minutes Per Lecture:", "Eliminates tedious manual roll-calls, giving valuable instructional time back to educators."),
        ("100% Accurate Percentage Tracking:", "Zero calculation errors, instant shortage alerts, and fully automated eligibility checks."),
        ("Future Roadmap - Geolocation Fencing:", "Enforcing GPS coordinates so students can only scan when physically inside the classroom."),
        ("Future Roadmap - Automated Parent Alerts:", "Automated WhatsApp and email notifications triggered when attendance drops below 75%.")
    ]

    for title, desc in conclusions:
        p = tf10.add_paragraph()
        p.text = f"★ {title} "
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = RGBColor(52, 211, 153)
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = RGBColor(226, 232, 240)
        p.space_after = Pt(12)

    # Thank you footer
    p = tf10.add_paragraph()
    p.text = "\nThank You! Questions & Discussion."
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = RGBColor(147, 197, 253)

    output_path = os.path.join(os.path.dirname(__file__), 'SmartAttend_Attendance_System_Presentation.pptx')
    prs.save(output_path)
    print(f"Presentation saved successfully at: {output_path}")
    return output_path

if __name__ == '__main__':
    build_presentation()
