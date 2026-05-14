"""Generate icon files from SVG for different platforms.

Requires:
- cairosvg: pip install cairosvg
- Pillow: pip install Pillow

On Windows, cairosvg requires GTK runtime. Alternative: use Inkscape or manual conversion.
"""
import os
import subprocess
import sys

try:
    from PIL import Image
except ImportError:
    print("Installing Pillow...")
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PICS_DIR = os.path.join(PROJECT_ROOT, 'pics')


def generate_png_with_cairosvg(svg_path, output_path, size):
    """Generate PNG using cairosvg."""
    try:
        import cairosvg
        cairosvg.svg2png(url=svg_path, write_to=output_path, output_width=size, output_height=size)
        return True
    except ImportError:
        print("cairosvg not available, trying alternative method...")
        return False


def generate_png_with_inkscape(svg_path, output_path, size):
    """Generate PNG using Inkscape (if available)."""
    inkscape_paths = [
        'inkscape',
        'C:\\Program Files\\Inkscape\\bin\\inkscape.exe',
        'C:\\Program Files (x86)\\Inkscape\\bin\\inkscape.exe',
    ]

    for inkscape in inkscape_paths:
        try:
            subprocess.run([
                inkscape, svg_path,
                '--export-type=png',
                '--export-filename=' + output_path,
                '--export-width=' + str(size),
                '--export-height=' + str(size),
            ], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    return False


def generate_png_from_svg(svg_path, output_path, size):
    """Generate PNG from SVG using available method."""
    svg_path = os.path.abspath(svg_path)
    output_path = os.path.abspath(output_path)

    # Try cairosvg first
    if generate_png_with_cairosvg(svg_path, output_path, size):
        print(f"Generated {output_path} using cairosvg")
        return True

    # Try Inkscape
    if generate_png_with_inkscape(svg_path, output_path, size):
        print(f"Generated {output_path} using Inkscape")
        return True

    print(f"WARNING: Could not generate {output_path}")
    print("Install cairosvg (pip install cairosvg) or Inkscape to generate PNG from SVG")
    return False


def resize_png_to_size(input_path, output_path, size):
    """Resize existing PNG to specific size using Pillow."""
    with Image.open(input_path) as img:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(output_path, 'PNG')
    print(f"Resized to {output_path}")


def generate_ico(png_paths, ico_path):
    """Generate multi-size ICO file from PNGs using Pillow."""
    images = []
    for png_path in png_paths:
        if os.path.exists(png_path):
            # Open and copy image to avoid file handle issues
            with Image.open(png_path) as img:
                # Convert to RGBA if needed
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                # Copy image to avoid file handle issues
                images.append(img.copy())

    if images:
        # Save as ICO with multiple sizes
        images[0].save(
            ico_path,
            format='ICO',
            sizes=[(img.width, img.height) for img in images],
            append_images=images[1:] if len(images) > 1 else []
        )
        print(f"Generated {ico_path} with {len(images)} sizes")
        return True
    else:
        print(f"ERROR: No PNG files available for ICO generation")
        return False


def create_placeholder_png(output_path, size, color='#004C98'):
    """Create a simple placeholder PNG if SVG conversion fails."""
    # Create a simple blue square icon as placeholder
    img = Image.new('RGBA', (size, size), (0, 76, 152, 255))  # #004C98

    # Add a white document shape in center
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)

    # Document shape
    doc_size = int(size * 0.4)
    doc_x = int(size * 0.15)
    doc_y = int(size * 0.15)
    draw.rectangle(
        [doc_x, doc_y, doc_x + doc_size, doc_y + int(doc_size * 1.25)],
        fill=(255, 255, 255, 230)
    )

    # Lines on document
    line_y_start = doc_y + int(doc_size * 0.3)
    line_spacing = int(doc_size * 0.15)
    for i in range(3):
        y = line_y_start + i * line_spacing
        draw.rectangle(
            [doc_x + int(doc_size * 0.1), y, doc_x + int(doc_size * 0.7), y + int(size * 0.02)],
            fill=(0, 76, 152, 180)
        )

    img.save(output_path, 'PNG')
    print(f"Created placeholder {output_path}")


def main():
    """Generate all icon files."""
    svg_path = os.path.join(PICS_DIR, 'icon.svg')

    if not os.path.exists(svg_path):
        print(f"ERROR: SVG source not found: {svg_path}")
        return False

    # Generate PNG sizes: 256, 64, 48, 32, 16
    sizes = [256, 64, 48, 32, 16]
    png_paths = []

    # Generate largest PNG from SVG
    largest_png = os.path.join(PICS_DIR, f'icon_{sizes[0]}.png')
    success = generate_png_from_svg(svg_path, largest_png, sizes[0])

    if not success:
        # Create placeholder if SVG conversion failed
        create_placeholder_png(largest_png, sizes[0])

    # Resize to smaller sizes
    for size in sizes[1:]:
        png_path = os.path.join(PICS_DIR, f'icon_{size}.png')
        resize_png_to_size(largest_png, png_path, size)
        png_paths.append(png_path)

    # Add largest PNG to list for ICO
    png_paths.insert(0, largest_png)

    # Generate ICO for Windows
    ico_path = os.path.join(PICS_DIR, 'icon.ico')
    generate_ico(png_paths, ico_path)

    # Copy 64px as default PNG for Linux
    default_png = os.path.join(PICS_DIR, 'icon.png')
    if os.path.exists(os.path.join(PICS_DIR, 'icon_64.png')):
        import shutil
        shutil.copy(os.path.join(PICS_DIR, 'icon_64.png'), default_png)
        print(f"Created default PNG: {default_png}")

    print("\nIcon generation complete!")
    print(f"  - Windows ICO: {ico_path}")
    print(f"  - Linux PNG: {default_png}")
    return True


if __name__ == '__main__':
    main()