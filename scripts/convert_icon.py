"""
Convert PNG to ICO for Windows executable icon
"""
from PIL import Image
import os

def convert_png_to_ico(png_path, ico_path):
    """Convert PNG image to ICO format with multiple sizes"""
    try:
        # Open the PNG file
        img = Image.open(png_path)

        # Ensure RGBA mode
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Create multiple sizes for better quality
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        icon_images = []

        for size in sizes:
            resized = img.resize(size, Image.Resampling.LANCZOS)
            icon_images.append(resized)

        # Save as ICO with multiple sizes
        icon_images[0].save(
            ico_path,
            format='ICO',
            sizes=sizes
        )

        print(f"[OK] Successfully converted {png_path} to {ico_path}")
        return True

    except Exception as e:
        print(f"[ERROR] Error converting icon: {str(e)}")
        return False

if __name__ == "__main__":
    # Get the project root directory (parent of scripts folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    png_file = os.path.join(project_root, "assets", "icons", "App_Logo.png")
    ico_file = os.path.join(project_root, "assets", "icons", "App_Logo.ico")

    if os.path.exists(png_file):
        convert_png_to_ico(png_file, ico_file)
    else:
        print(f"[ERROR] {png_file} not found!")
