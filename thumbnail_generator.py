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
    Creates a clean, text-less base template banner with StudyTopper branding frame.
    """
    img = Image.new('RGB', (width, height), color='#ffffff')
    draw = ImageDraw.Draw(img)

    # Outer border
    draw.rectangle([(0, 0), (width - 1, height - 1)], outline='#ab183d', width=3)

    # Top Header Bar (Red #ab183d)
    top_bar_h = 50
    draw.rectangle([(3, 3), (width - 4, top_bar_h)], fill='#ab183d')

    # Top Header Text (STUDY TOPPER)
    font_brand = get_font('bold', 20)
    font_sub = get_font('bold', 12)
    draw.text((18, 13), "STUDY TOPPER™", fill="#ffffff", font=font_brand)
    draw.text((width - 180, 17), "WWW.STUDYTOPPER.IN", fill="#fef08a", font=font_sub)

    # Decorative dividing stripe (Yellow/Gold)
    draw.rectangle([(3, top_bar_h), (width - 4, top_bar_h + 3)], fill='#eab308')

    # Center card background
    draw.rectangle([(12, top_bar_h + 10), (width - 13, height - 42)], fill='#f8fafc', outline='#e2e8f0', width=1)

    # Bottom Footer Bar (Navy #0c2340)
    draw.rectangle([(3, height - 38), (width - 4, height - 4)], fill='#0c2340')

    # Footer Text
    font_foot = get_font('bold', 11)
    draw.text((width // 2, height - 21), "Official Recruitment Notice • Online Application • Fast Updates", fill="#ffffff", font=font_foot, anchor="mm")

    return img

def generate_post_thumbnail(
    title: str,
    total_posts: str = "",
    category_badge: str = "Online Form 2026",
    output_path: str = None,
    width: int = 640,
    height: int = 330,
    max_size_kb: int = 10
) -> str:
    """
    Generates a dynamic post thumbnail in WebP format (<10KB) with custom title, posts badge, and branding.
    """
    img = create_base_template(width, height)
    draw = ImageDraw.Draw(img)

    # 1. Clean and wrap title
    clean_title = title.strip()
    wrapped_lines = textwrap.wrap(clean_title, width=32)
    if len(wrapped_lines) > 3:
        wrapped_lines = wrapped_lines[:3]
        wrapped_lines[2] = wrapped_lines[2][:28] + "..."

    # Title font sizing based on line count
    if len(wrapped_lines) == 1:
        title_font_size = 23
        line_spacing = 30
        start_y = 95
    elif len(wrapped_lines) == 2:
        title_font_size = 20
        line_spacing = 26
        start_y = 82
    else:
        title_font_size = 17
        line_spacing = 22
        start_y = 72

    title_font = get_font('bold', title_font_size)

    # Draw Title (Navy #0b213f)
    for i, line in enumerate(wrapped_lines):
        y_pos = start_y + (i * line_spacing)
        draw.text((width // 2, y_pos), line, fill='#0b213f', font=title_font, anchor='mm')

    # 2. Badges Section
    badges_y = 195 if len(wrapped_lines) <= 2 else 205
    badge_font = get_font('bold', 12)

    # Badge 1: Total Posts
    if total_posts:
        posts_text = f"Total Posts: {total_posts}".upper()
    else:
        posts_text = "OFFICIAL NOTIFICATION"
    
    draw.rounded_rectangle([(30, badges_y), (300, badges_y + 32)], radius=4, fill='#046132')
    draw.text((165, badges_y + 16), posts_text, fill='#ffffff', font=badge_font, anchor='mm')

    # Badge 2: Category / Status Badge
    cat_text = category_badge.strip().upper()
    draw.rounded_rectangle([(330, badges_y), (610, badges_y + 32)], radius=4, fill='#9f1239')
    draw.text((470, badges_y + 16), cat_text, fill='#ffffff', font=badge_font, anchor='mm')

    # 3. Subtitle / Call-to-action line
    cta_y = badges_y + 48
    cta_font = get_font('bold', 11)
    draw.text((width // 2, cta_y), "Check Eligibility Criteria, Age Limit, Syllabus & Apply Online", fill='#475569', font=cta_font, anchor='mm')

    # Ensure output directory exists
    if output_path is None:
        os.makedirs('/root/sarkari-result-portal/static/thumbnails', exist_ok=True)
        output_path = '/root/sarkari-result-portal/static/thumbnails/default.webp'
    else:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Save as WebP with optimized compression to ensure < 10KB
    quality = 80
    while quality >= 30:
        img.save(output_path, 'WEBP', quality=quality, method=6)
        size_kb = os.path.getsize(output_path) / 1024.0
        if size_kb <= max_size_kb:
            break
        quality -= 5

    # If still above max size, reduce colors
    if os.path.getsize(output_path) / 1024.0 > max_size_kb:
        img.convert('P', palette=Image.ADAPTIVE, colors=128).save(output_path, 'WEBP', quality=65)

    return output_path

if __name__ == '__main__':
    # Save clean base template
    base_img = create_base_template()
    base_img.save('/root/sarkari-result-portal/static/images/studytopper_banner_base.webp', 'WEBP', quality=80)

    # Test generation
    out = generate_post_thumbnail(
        title="SSC GD Constable Recruitment 2026",
        total_posts="39,481 Posts",
        category_badge="10th Pass Online Form",
        output_path="/root/sarkari-result-portal/static/thumbnails/ssc-gd-constable-2026.webp"
    )
    sz = os.path.getsize(out) / 1024.0
    print(f"Generated test thumbnail: {out} ({sz:.2f} KB)")
