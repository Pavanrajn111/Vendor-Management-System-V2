from PIL import Image, ImageDraw, ImageFont
import os

# Create uploads directory if not exists
uploads_dir = 'static/uploads'
os.makedirs(uploads_dir, exist_ok=True)

# Product categories and colors
products_images = {
    'kadai.png': ('Non-stick Kadai', '#FF6B35'),
    'casserole_set.png': ('Stainless Steel Casserole', '#FF6B35'),
    'study_table.png': ('Study Table', '#8B4513'),
    'office_chair.png': ('Office Chair', '#808080'),
    'basmati_rice.png': ('Basmati Rice 5kg', '#D4AF37'),
    'mustard_oil.png': ('Mustard Oil 1L', '#FFD700'),
    'mixer_grinder.png': ('Mixer Grinder 750W', '#C0C0C0'),
    'induction_cooktop.png': ('Induction Cooktop', '#1C1C1C'),
    'charger_fast.png': ('Fast Charger 25W', '#4285F4'),
    'tempered_glass.png': ('Tempered Glass', '#E8E8E8'),
    'laptop_sleeve.png': ('Laptop Sleeve 15.6', '#8B4513'),
    'usb_hub.png': ('USB-C Hub 7-in-1', '#333333'),
    'gel_pen_set.png': ('Gel Pen Set', '#FF1493'),
    'notebook_spiral.png': ('Spiral Notebook', '#FFE4B5'),
    'cricket_ball.png': ('Cricket Ball', '#DC143C'),
    'yoga_mat.png': ('Yoga Mat 6mm', '#228B22'),
    'headphones_bnc.png': ('Headphones', '#000000'),
    'smartwatch_amoled.png': ('AMOLED Smartwatch', '#1A1A1A'),
    'polity_book.png': ('Indian Polity', '#8B0000'),
    'data_structures.png': ('Data Structures', '#000080'),
    'cotton_hoodie.png': ('Cotton Hoodie', '#2F4F4F'),
    'running_sneakers.png': ('Running Sneakers', '#FF4500'),
    'vitamin_c_serum.png': ('Vitamin C Serum', '#FFD700'),
    'sunscreen_gel.png': ('SPF50 Sunscreen', '#FFA500'),
}

def create_product_image(filename, product_name, bg_color):
    """Create a simple product placeholder image"""
    # Create image with gradient background
    img = Image.new('RGB', (400, 400), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Add border
    border_color = tuple(max(0, int(c[:2], 16) - 50) if isinstance(c, str) else 0 for c in [bg_color[1:3], bg_color[3:5], bg_color[5:7]])
    draw.rectangle([10, 10, 390, 390], outline='white', width=3)
    
    # Add product name text in center
    try:
        # Try to use a default font
        font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Wrap text if needed
    text = product_name
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (400 - text_width) // 2
    y = (400 - text_height) // 2
    
    # Draw text with white color for contrast
    draw.text((x, y), text, fill='white', font=font)
    
    # Save image
    filepath = os.path.join(uploads_dir, filename)
    img.save(filepath)
    print(f"Created: {filepath}")

# Create all images
for filename, (product_name, color) in products_images.items():
    create_product_image(filename, product_name, color)

print("\nAll product images created successfully!")
