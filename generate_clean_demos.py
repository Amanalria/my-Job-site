import os
from PIL import Image, ImageDraw, ImageFont

FONTS = {
    'bold': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    'regular': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    'serif_bold': '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf',
    'serif_regular': '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'
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

    # Inner subtle canvas border
    draw.rounded_rectangle([(14, top_h + 12), (width - 15, height - 42)], radius=6, fill='#fcfcfc', outline='#e2e8f0', width=1)

    # Footer
    draw.rectangle([(3, height - 38), (width - 4, height - 4)], fill='#0f172a')
    draw.text((width // 2, height - 21), 'Fastest Sarkari Naukri & Result Updates • Free Mock Tests & PDF', fill='#ffffff', font=get_font('bold', 11), anchor='mm')
    
    return img

demos = []

# ==================== CLEAN DESIGN 1 ====================
# Deep Navy Big Title + Green Posts & Red Date (Single Line)
img1 = create_base()
d1 = ImageDraw.Draw(img1)
d1.text((width // 2, 115), "SSC GD Constable Recruitment 2026", fill='#0b213f', font=get_font('bold', 25), anchor='mm')
d1.text((width // 2, 165), "Total Posts : 39,481 Posts   |   Last Date : 25 Sept 2026", fill='#b91c1c', font=get_font('bold', 18), anchor='mm')
d1.text((width // 2, 210), "Eligibility : 10th Matric Pass • 100% Free Job Alerts", fill='#475569', font=get_font('bold', 12), anchor='mm')
demos.append(("clean_design_01_navy_title_single_line_meta", img1))


# ==================== CLEAN DESIGN 2 ====================
# Crimson Big Title + Stacked 2-Line Meta (Posts in Navy, Date in Red)
img2 = create_base()
d2 = ImageDraw.Draw(img2)
d2.text((width // 2, 105), "SSC GD Constable Recruitment 2026", fill='#9f1239', font=get_font('bold', 25), anchor='mm')
d2.text((width // 2, 155), "Total Vacancies : 39,481 Posts (10th Pass)", fill='#0f172a', font=get_font('bold', 19), anchor='mm')
d2.text((width // 2, 195), "Online Application Last Date : 25 September 2026", fill='#dc2626', font=get_font('bold', 18), anchor='mm')
demos.append(("clean_design_02_crimson_title_stacked_meta", img2))


# ==================== CLEAN DESIGN 3 ====================
# All-Caps Navy Title + Bullet Separators (Green & Red)
img3 = create_base()
d3 = ImageDraw.Draw(img3)
d3.text((width // 2, 110), "SSC GD CONSTABLE RECRUITMENT 2026", fill='#0c2340', font=get_font('bold', 23), anchor='mm')
d3.text((width // 2, 160), "• Total Posts : 39,481 • Last Date : 25-09-2026 •", fill='#046132', font=get_font('bold', 18), anchor='mm')
d3.text((width // 2, 205), "Male & Female Candidates • 10th Pass • Direct Apply Link", fill='#334155', font=get_font('bold', 12), anchor='mm')
demos.append(("clean_design_03_all_caps_bullet_style", img3))


# ==================== CLEAN DESIGN 4 ====================
# 2-Line Extra Bold Title + Clean Large Red Date
img4 = create_base()
d4 = ImageDraw.Draw(img4)
d4.text((width // 2, 95), "SSC GD Constable 2026", fill='#991b1b', font=get_font('bold', 28), anchor='mm')
d4.text((width // 2, 140), "39,481 Vacancies Online Form", fill='#0b213f', font=get_font('bold', 21), anchor='mm')
d4.text((width // 2, 190), "Application Last Date : 25 September 2026", fill='#dc2626', font=get_font('bold', 18), anchor='mm')
demos.append(("clean_design_04_twoline_big_title_clean_date", img4))


# ==================== CLEAN DESIGN 5 ====================
# Elegant Serif Government Authority Style
img5 = create_base()
d5 = ImageDraw.Draw(img5)
d5.text((width // 2, 110), "SSC GD Constable Recruitment 2026", fill='#05055f', font=get_font('serif_bold', 26), anchor='mm')
d5.text((width // 2, 160), "Total Posts : 39,481   •   Last Date : 25/09/2026", fill='#990000', font=get_font('serif_bold', 19), anchor='mm')
d5.text((width // 2, 205), "BSF • CISF • CRPF • SSB • ITBP • Assam Rifles • SSF", fill='#334155', font=get_font('bold', 12), anchor='mm')
demos.append(("clean_design_05_serif_authority_clean", img5))


# ==================== CLEAN DESIGN 6 ====================
# Left Aligned Clean Modern Typography with Stars
img6 = create_base()
d6 = ImageDraw.Draw(img6)
d6.text((45, 90), "SSC GD Constable Recruitment 2026", fill='#0f172a', font=get_font('bold', 24))
d6.text((45, 140), "★ Total Posts : 39,481 Posts (10th Pass)", fill='#15803d', font=get_font('bold', 18))
d6.text((45, 180), "★ Application Last Date : 25 September 2026", fill='#b91c1c', font=get_font('bold', 18))
d6.text((45, 218), "• Online Application Started @ studytopper.in", fill='#64748b', font=get_font('bold', 12))
demos.append(("clean_design_06_left_aligned_clean_stars", img6))


# ==================== CLEAN DESIGN 7 ====================
# High Contrast Black & Crimson
img7 = create_base()
d7 = ImageDraw.Draw(img7)
d7.text((width // 2, 100), "SSC GD Constable 2026", fill='#000000', font=get_font('bold', 30), anchor='mm')
d7.text((width // 2, 150), "Total Posts : 39,481 Posts", fill='#046132', font=get_font('bold', 20), anchor='mm')
d7.text((width // 2, 195), "Last Date to Apply : 25 September 2026", fill='#cd0808', font=get_font('bold', 19), anchor='mm')
demos.append(("clean_design_07_high_contrast_black_crimson", img7))


# ==================== CLEAN DESIGN 8 ====================
# Center Triple Key Info Line
img8 = create_base()
d8 = ImageDraw.Draw(img8)
d8.text((width // 2, 110), "SSC GD Constable Recruitment 2026", fill='#0b213f', font=get_font('bold', 25), anchor='mm')
d8.text((width // 2, 160), "39,481 Posts   ★   10th Pass   ★   Last Date : 25-09-2026", fill='#831843', font=get_font('bold', 17), anchor='mm')
d8.text((width // 2, 205), "Central Armed Police Forces • Apply Online Available", fill='#475569', font=get_font('bold', 12), anchor='mm')
demos.append(("clean_design_08_triple_star_info_line", img8))


# ==================== CLEAN DESIGN 9 ====================
# Big Navy Title + Highlighted Multi-Color Bold Numbers
img9 = create_base()
d9 = ImageDraw.Draw(img9)
d9.text((width // 2, 105), "SSC GD Constable Online Form 2026", fill='#0c2340', font=get_font('bold', 24), anchor='mm')
d9.text((width // 2, 155), "Total Vacancies : 39,481 Posts", fill='#16a34a', font=get_font('bold', 19), anchor='mm')
d9.text((width // 2, 195), "Last Date : 25 September 2026 (11:00 PM)", fill='#dc2626', font=get_font('bold', 18), anchor='mm')
demos.append(("clean_design_09_vibrant_numbers_clean", img9))


# ==================== CLEAN DESIGN 10 ====================
# Pure Minimalist 2-Line Hierarchy
img10 = create_base()
d10 = ImageDraw.Draw(img10)
d10.text((width // 2, 105), "SSC GD Constable Recruitment 2026", fill='#9f1239', font=get_font('bold', 25), anchor='mm')
d10.text((width // 2, 155), "Total Posts : 39,481 Posts", fill='#0f172a', font=get_font('bold', 20), anchor='mm')
d10.text((width // 2, 195), "Online Form Last Date : 25 September 2026", fill='#dc2626', font=get_font('bold', 19), anchor='mm')
demos.append(("clean_design_10_pure_minimalist_2line", img10))


# Save all 10 clean designs in both PNG and WebP
out_dir_local = "/root/sarkari-result-portal/static/images/clean_designs"
out_dir_anti = "/root/Antigravity-Images/clean_designs"
out_dir_dl = "/storage/emulated/0/Download/StudyTopper-Clean-Designs"
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
    img.save(webp_path, "WEBP", quality=75, method=6)
    img.save(os.path.join(out_dir_dl, webp_name), "WEBP", quality=75, method=6)
    
    sz_kb = os.path.getsize(webp_path) / 1024.0
    print(f"Generated clean: {png_name} / {webp_name} ({sz_kb:.2f} KB)")

print("Successfully generated all 10 clean box-free designs in Download folder!")
