import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

FONTS = {
    'bold': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    'regular': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    'serif_bold': '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'
}

def get_font(font_type, size):
    path = FONTS.get(font_type, FONTS['bold'])
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

width, height = 640, 330
top_h = 52

def create_base():
    img = Image.new('RGB', (width, height), color='#ffffff')
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (width - 1, height - 1)], outline='#881337', width=3)
    
    # Header gradient
    for y in range(3, top_h):
        r = int(171 + (136 - 171) * (y - 3) / top_h)
        g = int(24 + (19 - 24) * (y - 3) / top_h)
        b = int(61 + (55 - 61) * (y - 3) / top_h)
        draw.line([(3, y), (width - 4, y)], fill=(r, g, b))

    draw.rectangle([(3, top_h), (width - 4, top_h + 3)], fill='#fbbf24')
    draw.text((18, 14), 'STUDY TOPPER™', fill='#ffffff', font=get_font('bold', 20))
    draw.text((width - 180, 18), 'WWW.STUDYTOPPER.IN', fill='#fef08a', font=get_font('bold', 12))

    # Inner canvas
    draw.rounded_rectangle([(14, top_h + 12), (width - 15, height - 42)], radius=6, fill='#fcfcfc', outline='#e2e8f0', width=1)

    # Footer
    draw.rectangle([(3, height - 38), (width - 4, height - 4)], fill='#0f172a')
    draw.text((width // 2, height - 21), 'Fastest Sarkari Naukri & Result Updates • Free Mock Tests & PDF', fill='#ffffff', font=get_font('bold', 11), anchor='mm')
    
    return img

demos = []

# Title & Details for demo
title_text = "SSC GD Constable Recruitment 2026"
posts_text = "39,481 Posts"
date_text = "25 September 2026"

# ----------------- DESIGN 1: Dual Rounded Floating Badges (Green & Red) -----------------
img1 = create_base()
d1 = ImageDraw.Draw(img1)
d1.text((width // 2, 85), title_text, fill='#0b213f', font=get_font('bold', 22), anchor='mm')
d1.text((width // 2, 115), "Central Armed Police Forces (BSF, CISF, CRPF, SSB, ITBP, AR, SSF)", fill='#475569', font=get_font('bold', 11), anchor='mm')
# Badges
d1.rounded_rectangle([(35, 155), (305, 195)], radius=6, fill='#046132')
d1.text((170, 175), f"TOTAL POSTS: {posts_text.upper()}", fill='#ffffff', font=get_font('bold', 13), anchor='mm')

d1.rounded_rectangle([(335, 155), (605, 195)], radius=6, fill='#ab183d')
d1.text((470, 175), f"LAST DATE: {date_text.upper()}", fill='#ffffff', font=get_font('bold', 12), anchor='mm')

d1.text((width // 2, 235), "Eligibility: 10th Matric Pass • Apply Online Form Started", fill='#1e293b', font=get_font('bold', 12), anchor='mm')
demos.append(("design_01_dual_floating_badges", img1))


# ----------------- DESIGN 2: Central Ribbon & 3-Column Info Strip -----------------
img2 = create_base()
d2 = ImageDraw.Draw(img2)
d2.text((width // 2, 82), title_text, fill='#0b213f', font=get_font('bold', 21), anchor='mm')
d2.line([(width // 2 - 120, 98), (width // 2 + 120, 98)], fill='#ab183d', width=2)

# 3 Mini Stat Boxes
box_w = 175
gap = 18
start_x = (width - (3 * box_w + 2 * gap)) // 2

# Box 1: Posts
d2.rounded_rectangle([(start_x, 120), (start_x + box_w, 185)], radius=6, fill='#f0fdf4', outline='#86efac', width=1)
d2.text((start_x + box_w // 2, 138), "TOTAL VACANCIES", fill='#166534', font=get_font('bold', 10), anchor='mm')
d2.text((start_x + box_w // 2, 162), posts_text, fill='#046132', font=get_font('bold', 15), anchor='mm')

# Box 2: Qualification
bx2 = start_x + box_w + gap
d2.rounded_rectangle([(bx2, 120), (bx2 + box_w, 185)], radius=6, fill='#eff6ff', outline='#93c5fd', width=1)
d2.text((bx2 + box_w // 2, 138), "QUALIFICATION", fill='#1e40af', font=get_font('bold', 10), anchor='mm')
d2.text((bx2 + box_w // 2, 162), "10th High School", fill='#1d4ed8', font=get_font('bold', 14), anchor='mm')

# Box 3: Last Date
bx3 = bx2 + box_w + gap
d2.rounded_rectangle([(bx3, 120), (bx3 + box_w, 185)], radius=6, fill='#fef2f2', outline='#fca5a5', width=1)
d2.text((bx3 + box_w // 2, 138), "LAST DATE TO APPLY", fill='#991b1b', font=get_font('bold', 10), anchor='mm')
d2.text((bx3 + box_w // 2, 162), "25-09-2026", fill='#b91c1c', font=get_font('bold', 15), anchor='mm')

# Callout below
d2.rounded_rectangle([(160, 205), (480, 238)], radius=16, fill='#0c2340')
d2.text((width // 2, 221), "Check Detailed Notification & Apply Online", fill='#ffffff', font=get_font('bold', 11), anchor='mm')
demos.append(("design_02_3_column_stat_strip", img2))


# ----------------- DESIGN 3: Bold Left-Accent Box with Big Post Count -----------------
img3 = create_base()
d3 = ImageDraw.Draw(img3)
# Left Big Card
d3.rounded_rectangle([(30, 75), (190, 235)], radius=8, fill='#046132')
d3.text((110, 105), "TOTAL", fill='#dcfce7', font=get_font('bold', 13), anchor='mm')
d3.text((110, 140), "39,481", fill='#ffffff', font=get_font('bold', 24), anchor='mm')
d3.text((110, 175), "POSTS", fill='#fef08a', font=get_font('bold', 16), anchor='mm')
d3.text((110, 210), "10th Pass Bharti", fill='#ffffff', font=get_font('bold', 10), anchor='mm')

# Right Content
d3.text((215, 95), title_text, fill='#0b213f', font=get_font('bold', 19))
d3.text((215, 128), "Staff Selection Commission (SSC GD Exam 2026)", fill='#475569', font=get_font('regular', 12))

# Right Last Date Card
d3.rounded_rectangle([(215, 160), (595, 205)], radius=6, fill='#fee2e2', outline='#dc2626', width=1)
d3.text((405, 182), "APPLICATION LAST DATE : 25 SEPTEMBER 2026", fill='#b91c1c', font=get_font('bold', 12), anchor='mm')

d3.text((215, 222), "• Online Form Available • Age: 18-23 Yrs • Fee: Rs. 100/-", fill='#0f172a', font=get_font('bold', 11))
demos.append(("design_03_left_big_number_accent", img3))


# ----------------- DESIGN 4: Top Mini Tag + Gold & Crimson Badges -----------------
img4 = create_base()
d4 = ImageDraw.Draw(img4)
# Mini Top Tag
d4.rounded_rectangle([(width // 2 - 120, 68), (width // 2 + 120, 92)], radius=12, fill='#fef3c7', outline='#d97706', width=1)
d4.text((width // 2, 80), "OFFICIAL NOTIFICATION 2026", fill='#92400e', font=get_font('bold', 10), anchor='mm')

d4.text((width // 2, 120), title_text, fill='#0f172a', font=get_font('bold', 22), anchor='mm')

# Badges Row
d4.rounded_rectangle([(40, 155), (310, 196)], radius=6, fill='#d97706')
d4.text((175, 175), f"TOTAL POSTS : {posts_text.upper()}", fill='#ffffff', font=get_font('bold', 13), anchor='mm')

d4.rounded_rectangle([(330, 155), (600, 196)], radius=6, fill='#b91c1c')
d4.text((465, 175), f"LAST DATE : {date_text.upper()}", fill='#ffffff', font=get_font('bold', 12), anchor='mm')

d4.text((width // 2, 230), "Male & Female Candidates • 10th Pass • Direct Apply Link", fill='#334155', font=get_font('bold', 11), anchor='mm')
demos.append(("design_04_gold_and_crimson_pills", img4))


# ----------------- DESIGN 5: Full Width Horizontal Stacked Bars -----------------
img5 = create_base()
d5 = ImageDraw.Draw(img5)
d5.text((width // 2, 82), title_text, fill='#0b213f', font=get_font('bold', 21), anchor='mm')

# Stack Bar 1: Posts (Navy)
d5.rounded_rectangle([(40, 115), (600, 152)], radius=5, fill='#0c2340')
d5.text((width // 2, 133), f"TOTAL VACANCIES : {posts_text.upper()} (10th PASS)", fill='#ffffff', font=get_font('bold', 13), anchor='mm')

# Stack Bar 2: Last Date (Crimson)
d5.rounded_rectangle([(40, 162), (600, 199)], radius=5, fill='#ab183d')
d5.text((width // 2, 180), f"ONLINE APPLICATION LAST DATE : {date_text.upper()}", fill='#ffffff', font=get_font('bold', 12), anchor='mm')

d5.text((width // 2, 230), "BSF • CISF • CRPF • SSB • ITBP • Assam Rifles • SSF", fill='#475569', font=get_font('bold', 12), anchor='mm')
demos.append(("design_05_stacked_horizontal_bars", img5))


# ----------------- DESIGN 6: Dual-Tone Split Badge & Urgent Date Alert -----------------
img6 = create_base()
d6 = ImageDraw.Draw(img6)
d6.text((width // 2, 85), title_text, fill='#0b213f', font=get_font('bold', 22), anchor='mm')

# Split Badge in Center
badge_w, badge_h = 480, 42
bx = (width - badge_w) // 2
by = 120
d6.rectangle([(bx, by), (bx + badge_w // 2, by + badge_h)], fill='#0c2340')
d6.rectangle([(bx + badge_w // 2, by), (bx + badge_w, by + badge_h)], fill='#046132')
d6.rectangle([(bx, by), (bx + badge_w, by + badge_h)], outline='#000000', width=1)
d6.text((bx + badge_w // 4, by + badge_h // 2), f"TOTAL: {posts_text.upper()}", fill='#ffffff', font=get_font('bold', 12), anchor='mm')
d6.text((bx + 3 * badge_w // 4, by + badge_h // 2), "ELIGIBILITY: 10th PASS", fill='#ffffff', font=get_font('bold', 12), anchor='mm')

# Red Last Date Warning Pill
d6.rounded_rectangle([(80, 180), (560, 218)], radius=6, fill='#dc2626')
d6.text((width // 2, 199), f"LAST DATE TO APPLY : {date_text.upper()} (11:00 PM)", fill='#ffffff', font=get_font('bold', 13), anchor='mm')

d6.text((width // 2, 240), "Apply Online Form, Syllabus & Notification PDF @ studytopper.in", fill='#475569', font=get_font('regular', 11), anchor='mm')
demos.append(("design_06_split_badge_urgent_alert", img6))


# ----------------- DESIGN 7: Sarkari Result Classic Boxed Outlines -----------------
img7 = create_base()
d7 = ImageDraw.Draw(img7)
# Title Box
d7.rounded_rectangle([(30, 68), (610, 108)], radius=5, fill='#f8fafc', outline='#ab183d', width=2)
d7.text((width // 2, 88), title_text, fill='#9f1239', font=get_font('bold', 18), anchor='mm')

# 2 Side by Side Big Boxes
b_w = 265
b_h = 75
d7.rounded_rectangle([(35, 125), (35 + b_w, 125 + b_h)], radius=6, fill='#ffffff', outline='#16a34a', width=2)
d7.text((35 + b_w // 2, 145), "TOTAL VACANCIES", fill='#15803d', font=get_font('bold', 11), anchor='mm')
d7.text((35 + b_w // 2, 175), posts_text, fill='#0f172a', font=get_font('bold', 18), anchor='mm')

d7.rounded_rectangle([(340, 125), (340 + b_w, 125 + b_h)], radius=6, fill='#ffffff', outline='#dc2626', width=2)
d7.text((340 + b_w // 2, 145), "LAST DATE TO APPLY", fill='#b91c1c', font=get_font('bold', 11), anchor='mm')
d7.text((340 + b_w // 2, 175), "25 SEPT 2026", fill='#dc2626', font=get_font('bold', 18), anchor='mm')

d7.text((width // 2, 228), "10th Matric Pass • Age 18-23 Years • Online Apply Available", fill='#334155', font=get_font('bold', 11), anchor='mm')
demos.append(("design_07_classic_boxed_outlines", img7))


# ----------------- DESIGN 8: Large Bold Crimson Headline + Banner Tag -----------------
img8 = create_base()
d8 = ImageDraw.Draw(img8)
d8.text((width // 2, 80), "SSC GD CONSTABLE", fill='#9f1239', font=get_font('bold', 25), anchor='mm')
d8.text((width // 2, 110), "Recruitment 2026 (CAPFs & SSF Examination)", fill='#0f172a', font=get_font('bold', 13), anchor='mm')

# Wide Pill Badge
d8.rounded_rectangle([(30, 142), (610, 192)], radius=25, fill='#0c2340')
d8.text((width // 2, 167), f"★ {posts_text}  |  10th Pass  |  Last Date: {date_text} ★", fill='#fef08a', font=get_font('bold', 13), anchor='mm')

d8.text((width // 2, 222), "Download Notification PDF, Exam Syllabus & Apply Online Form", fill='#475569', font=get_font('bold', 11), anchor='mm')
demos.append(("design_08_bold_headline_wide_pill", img8))


# ----------------- DESIGN 9: 3 Horizontal Pills Matrix -----------------
img9 = create_base()
d9 = ImageDraw.Draw(img9)
d9.text((width // 2, 85), title_text, fill='#0b213f', font=get_font('bold', 22), anchor='mm')
d9.text((width // 2, 115), "Staff Selection Commission Central Armed Police Forces", fill='#64748b', font=get_font('regular', 11), anchor='mm')

# 3 Pills
pw = 175
p_gap = 15
px0 = (width - (3 * pw + 2 * p_gap)) // 2

# Pill 1: Green Posts
d9.rounded_rectangle([(px0, 145), (px0 + pw, 188)], radius=20, fill='#046132')
d9.text((px0 + pw // 2, 166), f"★ {posts_text}", fill='#ffffff', font=get_font('bold', 12), anchor='mm')

# Pill 2: Navy Eligibility
px1 = px0 + pw + p_gap
d9.rounded_rectangle([(px1, 145), (px1 + pw, 188)], radius=20, fill='#0c2340')
d9.text((px1 + pw // 2, 166), "10th Pass Bharti", fill='#ffffff', font=get_font('bold', 12), anchor='mm')

# Pill 3: Red Date
px2 = px1 + pw + p_gap
d9.rounded_rectangle([(px2, 145), (px2 + pw, 188)], radius=20, fill='#ab183d')
d9.text((px2 + pw // 2, 166), "Last Date: 25 Sept", fill='#ffffff', font=get_font('bold', 12), anchor='mm')

d9.text((width // 2, 228), "Verified Notification • Direct Official Portal Link • studytopper.in", fill='#1e293b', font=get_font('bold', 11), anchor='mm')
demos.append(("design_09_three_pill_matrix", img9))


# ----------------- DESIGN 10: Official Hierarchy with Force Ribbon -----------------
img10 = create_base()
d10 = ImageDraw.Draw(img10)

# Top Bar Tag
d10.text((width // 2, 74), "[ CENTRAL GOVT JOB NOTIFICATION 2026 ]", fill='#ab183d', font=get_font('bold', 10), anchor='mm')
d10.text((width // 2, 102), title_text, fill='#0f172a', font=get_font('bold', 21), anchor='mm')

# 2 Major Badges
d10.rounded_rectangle([(40, 130), (300, 172)], radius=6, fill='#046132')
d10.text((170, 151), f"POSTS : {posts_text.upper()}", fill='#ffffff', font=get_font('bold', 13), anchor='mm')

d10.rounded_rectangle([(340, 130), (600, 172)], radius=6, fill='#ab183d')
d10.text((470, 151), f"APPLY BY : {date_text.upper()}", fill='#ffffff', font=get_font('bold', 12), anchor='mm')

# Bottom Force Ribbon Box
d10.rounded_rectangle([(40, 192), (600, 230)], radius=4, fill='#f1f5f9', outline='#cbd5e1', width=1)
d10.text((width // 2, 211), "BSF • CISF • CRPF • SSB • ITBP • Assam Rifles • SSF", fill='#0f172a', font=get_font('bold', 11), anchor='mm')
demos.append(("design_10_official_force_hierarchy", img10))


# Save all 10 designs in both PNG and WebP to project and Downloads
out_dir_local = "/root/sarkari-result-portal/static/images/demo_designs"
out_dir_anti = "/root/Antigravity-Images/demo_designs"
out_dir_dl = "/storage/emulated/0/Download/StudyTopper-Demo-Designs"
out_dir_dl_root = "/storage/emulated/0/Download"

for d in [out_dir_local, out_dir_anti, out_dir_dl]:
    os.makedirs(d, exist_ok=True)

for name, img in demos:
    png_name = f"{name}.png"
    webp_name = f"{name}.webp"
    
    # Save PNG
    img.save(os.path.join(out_dir_local, png_name), "PNG")
    img.save(os.path.join(out_dir_anti, png_name), "PNG")
    img.save(os.path.join(out_dir_dl, png_name), "PNG")
    img.save(os.path.join(out_dir_dl_root, png_name), "PNG")
    
    # Save WebP (<10KB)
    webp_path = os.path.join(out_dir_local, webp_name)
    img.save(webp_path, "WEBP", quality=80, method=6)
    img.save(os.path.join(out_dir_dl, webp_name), "WEBP", quality=80, method=6)
    
    sz_kb = os.path.getsize(webp_path) / 1024.0
    print(f"Generated: {png_name} / {webp_name} ({sz_kb:.2f} KB)")

print("Successfully generated all 10 designs in Download folder!")
