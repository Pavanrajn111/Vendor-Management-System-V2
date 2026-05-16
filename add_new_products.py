import sqlite3
from PIL import Image, ImageDraw, ImageFont
import os

# Create uploads directory if needed
uploads_dir = 'static/uploads'
os.makedirs(uploads_dir, exist_ok=True)

# New products to add - format: (vendor_name, product_name, price, image_filename, availability)
new_products = [
    # UrbanKart Supplies - Electronics accessories
    ("UrbanKart Supplies", "Wireless Earbuds Pro Max", "2499", "wireless_earbuds_pro.png", "In Stock"),
    ("UrbanKart Supplies", "USB Power Bank 20000mAh", "1299", "power_bank_20000.png", "In Stock"),
    ("UrbanKart Supplies", "Phone Screen Protector Pack (10)", "349", "screen_protector.png", "In Stock"),
    
    # GreenLeaf Organics - More grocery items
    ("GreenLeaf Organics", "Organic Honey 500g", "599", "organic_honey.png", "In Stock"),
    ("GreenLeaf Organics", "Almond Butter Natural 200g", "449", "almond_butter.png", "In Stock"),
    ("GreenLeaf Organics", "Chia Seeds 200g", "399", "chia_seeds.png", "In Stock"),
    
    # TechNova Solutions - More tech gear
    ("TechNova Solutions", "Mechanical Gaming Keyboard RGB", "3499", "gaming_keyboard.png", "In Stock"),
    ("TechNova Solutions", "4K Webcam 30fps", "4299", "webcam_4k.png", "In Stock"),
    ("TechNova Solutions", "Laptop Cooling Pad Dual Fan", "899", "laptop_cooler.png", "In Stock"),
    
    # BookNest Store - More books
    ("BookNest Store", "Self-Help: Atomic Habits", "399", "atomic_habits.png", "In Stock"),
    ("BookNest Store", "Fiction: The Midnight Library", "350", "midnight_library.png", "In Stock"),
    ("BookNest Store", "Tech Manual: Python for Data Science", "899", "python_datascience.png", "In Stock"),
    
    # AutoZone Parts - More automotive
    ("AutoZone Parts", "Car Air Filter Premium", "450", "air_filter.png", "In Stock"),
    ("AutoZone Parts", "Windshield Cleaner Wiper Blades", "899", "wiper_blades.png", "In Stock"),
    ("AutoZone Parts", "Car Seat Covers (Set of 5)", "2199", "seat_covers.png", "In Stock"),
    
    # Elite Furniture - More furniture
    ("Elite Furniture", "Wooden Bookshelf 5-Shelf", "5499", "bookshelf_wooden.png", "In Stock"),
    ("Elite Furniture", "Dining Table 4-Seater Wooden", "12999", "dining_table.png", "In Stock"),
    
    # FreshMart Groceries - More groceries
    ("FreshMart Groceries", "Whole Wheat Flour 5kg", "399", "wheat_flour.png", "In Stock"),
    ("FreshMart Groceries", "Chilli Powder Premium 100g", "299", "chilli_powder.png", "In Stock"),
    ("FreshMart Groceries", "Turmeric Powder Organic 100g", "249", "turmeric_powder.png", "In Stock"),
    
    # HomeStyle Living - More kitchen items
    ("HomeStyle Living", "Non-Stick Fry Pan 10 inch", "1299", "fry_pan.png", "In Stock"),
    ("HomeStyle Living", "Pressure Cooker 5L Stainless", "2999", "pressure_cooker.png", "In Stock"),
    ("HomeStyle Living", "Ceramic Dinner Set 32 Pieces", "3499", "dinner_set.png", "In Stock"),
    
    # Mobile Planet - More mobile accessories
    ("Mobile Planet", "Wireless Charging Pad Fast", "1299", "wireless_charger.png", "In Stock"),
    ("Mobile Planet", "Phone Stand Adjustable Aluminum", "599", "phone_stand.png", "In Stock"),
    ("Mobile Planet", "Screen Cleaner Spray 150ml", "199", "screen_cleaner.png", "In Stock"),
    
    # Prime Accessories - More accessories
    ("Prime Accessories", "Travel Backpack 30L Waterproof", "2199", "travel_backpack.png", "In Stock"),
    ("Prime Accessories", "Portable Bluetooth Speaker Outdoor", "1899", "bluetooth_speaker.png", "In Stock"),
    
    # Scholar Stationery Co - More stationery
    ("Scholar Stationery Co", "Marker Set 24 Colors", "299", "marker_set.png", "In Stock"),
    ("Scholar Stationery Co", "Highlighter Pack 5 Colors", "149", "highlighter_pack.png", "In Stock"),
    
    # SportX Arena - More sports items
    ("SportX Arena", "Dumbbells Pair 5kg Cast Iron", "999", "dumbbells.png", "In Stock"),
    ("SportX Arena", "Badminton Racket Pair with Shuttles", "1499", "badminton_racket.png", "In Stock"),
    
    # TechNova Electronics - More electronics
    ("TechNova Electronics", "Portable SSD 1TB USB-C", "8999", "portable_ssd.png", "In Stock"),
    ("TechNova Electronics", "Wireless Mouse Ergonomic", "1299", "ergonomic_mouse.png", "In Stock"),
    
    # The Reading Room - More books
    ("The Reading Room", "General Knowledge Guide 2024", "499", "gk_guide.png", "In Stock"),
    
    # Urban Fashion Hub - More fashion
    ("Urban Fashion Hub", "Denim Jeans Slim Fit", "1999", "denim_jeans.png", "In Stock"),
    ("Urban Fashion Hub", "White T-Shirt Cotton Pack 2", "699", "white_tshirt.png", "In Stock"),
    
    # Urban Glow Beauty - More beauty products
    ("Urban Glow Beauty", "Moisturizer Cream 50ml", "749", "moisturizer.png", "In Stock"),
    ("Urban Glow Beauty", "Face Wash Gel 100ml", "349", "face_wash.png", "In Stock"),
    
    # ChefPro Kitchenware - More kitchenware
    ("ChefPro Kitchenware", "Bamboo Cutting Board Set 3", "699", "cutting_board_set.png", "In Stock"),
    ("ChefPro Kitchenware", "Stainless Steel Knife Set 6pc", "1599", "knife_set.png", "In Stock"),
]

def create_simple_image(filename, product_name):
    """Create simple colored placeholder image"""
    colors = {
        'electronics': '#4169E1', 'grocery': '#228B22', 'furniture': '#8B4513',
        'fashion': '#FF1493', 'beauty': '#FFB6C1', 'book': '#2F4F4F',
        'sports': '#FF6347', 'stationery': '#FFD700', 'kitchenware': '#DC143C',
        'accessories': '#808080', 'auto': '#191970'
    }
    
    # Pick color based on keywords
    color = '#4169E1'
    if any(word in product_name.lower() for word in ['book', 'guide', 'manual', 'library']):
        color = colors['book']
    elif any(word in product_name.lower() for word in ['organic', 'rice', 'tea', 'oil', 'honey', 'flour', 'powder', 'spice']):
        color = colors['grocery']
    elif any(word in product_name.lower() for word in ['table', 'chair', 'shelf', 'bed', 'sofa']):
        color = colors['furniture']
    elif any(word in product_name.lower() for word in ['shirt', 'jeans', 'hoodie', 'shoes', 'sneaker', 'pants']):
        color = colors['fashion']
    elif any(word in product_name.lower() for word in ['serum', 'cream', 'sunscreen', 'moisturizer', 'wash']):
        color = colors['beauty']
    elif any(word in product_name.lower() for word in ['dumbbell', 'yoga', 'ball', 'racket', 'sports']):
        color = colors['sports']
    elif any(word in product_name.lower() for word in ['pen', 'marker', 'notebook', 'highlighter', 'stationery']):
        color = colors['stationery']
    elif any(word in product_name.lower() for word in ['pan', 'cooker', 'grinder', 'kadai', 'knife', 'board', 'fork', 'spoon']):
        color = colors['kitchenware']
    elif any(word in product_name.lower() for word in ['bag', 'backpack', 'sleeve', 'speaker', 'charger', 'stand']):
        color = colors['accessories']
    elif any(word in product_name.lower() for word in ['filter', 'blades', 'covers', 'seat']):
        color = colors['auto']
    
    img = Image.new('RGB', (300, 300), color=color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 290, 290], outline='white', width=2)
    
    try:
        font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    filepath = os.path.join(uploads_dir, filename)
    img.save(filepath)
    return filepath

# Create images and collect data
products_data = []
for vendor, name, price, img_file, availability in new_products:
    create_simple_image(img_file, name)
    products_data.append({
        'vendor': vendor,
        'name': name,
        'price': price,
        'image': f'uploads/{img_file}',
        'availability': availability
    })

# Insert into database
conn = sqlite3.connect('vendor.db')
cursor = conn.cursor()

added_count = 0
for product in products_data:
    try:
        cursor.execute(
            'INSERT INTO products (vendor, name, price, image, availability) VALUES (?, ?, ?, ?, ?)',
            (product['vendor'], product['name'], product['price'], product['image'], product['availability'])
        )
        added_count += 1
        print(f"Added: {product['name']} by {product['vendor']}")
    except Exception as e:
        print(f"Error adding {product['name']}: {e}")

conn.commit()
conn.close()

print(f"\n✓ Successfully added {added_count} new products!")
print(f"✓ Created {added_count} product images!")
