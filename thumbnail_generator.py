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

def create_base_template(width=640, height=330):
    """
    Official StudyTopper Template 5 (Gradient Burgundy + Gold Stripe + Dark Navy Footer).
    """
    img = Image.new('RGB', (width, height), color='#ffffff')
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (width - 1, height - 1)], outline='#881337', width=3)
    
    # Header gradient
    top_h = 52
    for y in range(3, top_h):
        r = int(171 + (136 - 171) * (y - 3) / top_h)
        g = int(24 + (19 - 24) * (y - 3) / top_h)
        b = int(61 + (55 - 61) * (y - 3) / top_h)
        draw.line([(3, y), (width - 4, y)], fill=(r, g, b))

    # Gold accent stripe
    draw.rectangle([(3, top_h), (width - 4, top_h + 3)], fill='#fbbf24')
    
    # Header text
    draw.text((18, 14), 'STUDY TOPPER™', fill='#ffffff', font=get_font('bold', 20))
    draw.text((width - 180, 18), 'WWW.STUDYTOPPER.IN', fill='#fef08a', font=get_font('bold', 12))

    # Inner subtle canvas border
    draw.rounded_rectangle([(14, top_h + 12), (width - 15, height - 42)], radius=6, fill='#fcfcfc', outline='#e2e8f0', width=1)

    # Footer
    draw.rectangle([(3, height - 38), (width - 4, height - 4)], fill='#0f172a')
    draw.text((width // 2, height - 21), 'Fastest Sarkari Naukri & Result Updates • Free Mock Tests & PDF', fill='#ffffff', font=get_font('bold', 11), anchor='mm')
    
    return img

def generate_post_thumbnail(
    title: str,
    total_posts: str = "",
    last_date: str = "",
    qualification: str = "10th / 12th Pass",
    output_path: str = None,
    width: int = 640,
    height: int = 330,
    max_size_kb: float = 9.8
) -> str:
    """
    Generates official Clean Design 1 WebP thumbnail (<10KB) without bulky boxes.
    Big Navy Title + Single Line Posts & Last Date Meta.
    """
    img = create_base_template(width, height)
    draw = ImageDraw.Draw(img)

    # 1. Clean Title and wrap if long
    clean_title = title.strip()
    # Remove redundant board name from front if already too long
    lines = textwrap.wrap(clean_title, width=32)
    if len(lines) > 2:
        lines = lines[:2]
        lines[1] = lines[1][:28] + "..."

    # Title Sizing & Positioning
    if len(lines) == 1:
        title_font_size = 25
        title_y = 115
        line_spacing = 0
    else:
        title_font_size = 22
        title_y = 98
        line_spacing = 26

    title_font = get_font('bold', title_font_size)
    for i, line in enumerate(lines):
        y = title_y + (i * line_spacing)
        draw.text((width // 2, y), line, fill='#0b213f', font=title_font, anchor='mm')

    # 2. Meta Line (Posts & Last Date in Red/Crimson, No Boxes)
    meta_y = 165 if len(lines) == 1 else 172
    
    meta_parts = []
    if total_posts:
        posts_str = str(total_posts).strip()
        if not posts_str.lower().endswith("posts") and not posts_str.lower().endswith("post"):
            posts_str += " Posts"
        meta_parts.append(f"Total Posts : {posts_str}")
    else:
        meta_parts.append("Official Notification")

    if last_date:
        meta_parts.append(f"Last Date : {last_date.strip()}")
    else:
        meta_parts.append("Online Form Active")

    meta_text = "   |   ".join(meta_parts)
    meta_font = get_font('bold', 18 if len(meta_text) < 45 else 16)
    draw.text((width // 2, meta_y), meta_text, fill='#b91c1c', font=meta_font, anchor='mm')

    # 3. Subtitle / Eligibility line
    sub_y = meta_y + 45
    sub_text = f"Eligibility : {qualification} • 100% Free Job Alerts" if qualification else "Download Notification PDF, Check Eligibility & Apply Online"
    sub_font = get_font('bold', 12)
    draw.text((width // 2, sub_y), sub_text, fill='#475569', font=sub_font, anchor='mm')

    # Ensure output path
    if output_path is None:
        os.makedirs('/root/sarkari-result-portal/static/thumbnails', exist_ok=True)
        output_path = '/root/sarkari-result-portal/static/thumbnails/default.webp'
    else:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Save WebP with optimization strictly < 10KB
    q = 65
    while q >= 20:
        img.save(output_path, 'WEBP', quality=q, method=6)
        size_kb = os.path.getsize(output_path) / 1024.0
        if size_kb <= max_size_kb:
            break
        q -= 5

    # Fallback to 128 adaptive colors if needed
    if os.path.getsize(output_path) / 1024.0 > max_size_kb:
        img.convert('P', palette=Image.ADAPTIVE, colors=128).save(output_path, 'WEBP', quality=50)

    return output_path

if __name__ == '__main__':
    # Test generation for SSC GD
    out = generate_post_thumbnail(
        title="SSC GD Constable Recruitment 2026",
        total_posts="39,481",
        last_date="25 Sept 2026",
        qualification="10th Matric Pass",
        output_path="/root/sarkari-result-portal/static/thumbnails/ssc-gd-constable-2026.webp"
    )
    sz = os.path.getsize(out) / 1024.0
    print(f"Generated clean thumbnail: {out} ({sz:.2f} KB)")
