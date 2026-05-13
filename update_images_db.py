import sqlite3

conn = sqlite3.connect('vendor.db')
cursor = conn.cursor()

# Map of product ID to new image filename
image_updates = {
    19: 'headphones_bnc.png',      # Noise-cancelling Bluetooth Headphones
    20: 'smartwatch_amoled.png',   # AMOLED Smartwatch
    21: 'cotton_hoodie.png',       # Cotton Hoodie
    22: 'running_sneakers.png',    # Running Sneakers
    23: 'basmati_rice.png',        # Basmati Rice 5kg
    24: 'mustard_oil.png',         # Cold-pressed Mustard Oil 1L
    25: 'mixer_grinder.png',       # Mixer Grinder 750W
    26: 'induction_cooktop.png',   # Induction Cooktop 2000W
    27: 'laptop_sleeve.png',       # Leather Laptop Sleeve 15.6 inch
    28: 'usb_hub.png',             # USB-C Hub 7-in-1
    29: 'cricket_ball.png',        # Cricket Leather Ball
    30: 'yoga_mat.png',            # Yoga Mat 6mm
    31: 'study_table.png',         # Study Table
    32: 'office_chair.png',        # Ergonomic Office Chair
    33: 'charger_fast.png',        # Fast Charger 25W
    34: 'tempered_glass.png',      # Tempered Glass
    35: 'vitamin_c_serum.png',     # Vitamin C Face Serum
    36: 'sunscreen_gel.png',       # SPF50 Sunscreen Gel
    37: 'polity_book.png',         # Indian Polity
    38: 'data_structures.png',     # Data Structures in Python
    39: 'kadai.png',               # Non-stick Kadai 24cm
    40: 'casserole_set.png',       # Stainless Steel Casserole set
    41: 'gel_pen_set.png',         # Premium Gel Pen set
    42: 'notebook_spiral.png',     # A4 Spiral Notebook
}

# Update database
for product_id, new_image in image_updates.items():
    cursor.execute(
        'UPDATE products SET image = ? WHERE id = ?',
        (f'uploads/{new_image}', product_id)
    )
    print(f"Updated product {product_id}: uploads/{new_image}")

conn.commit()
conn.close()
print("\nAll product images updated successfully!")
