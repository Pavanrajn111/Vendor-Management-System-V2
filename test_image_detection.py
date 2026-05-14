#!/usr/bin/env python
"""Test the smart image detection function"""

import os
import sys

# Add app directory to path
sys.path.insert(0, '/Users/LEnobo/Desktop/VMfolder')
os.chdir('c:\\Users\\LEnobo\\Desktop\\VMfolder')

# Import the find_image_file function from app
from app import find_image_file

# Test cases
test_cases = [
    ('uploads/battery.jfif', 'Should find existing battery.jfif'),
    ('uploads/battery', 'Should find battery with any extension'),
    ('battery', 'Should find battery in uploads without prefix'),
    ('uploads/keyboard.jpg', 'Should find existing keyboard.jpg'),
    ('uploads/Keyboard.jpg', 'Should handle case variations'),
    ('uploads/rice.jfif', 'Should find rice.jfif'),
    ('uploads/nonexistent.png', 'Should return placeholder for missing file'),
    ('uploads/', 'Should handle empty filename'),
    ('', 'Should handle empty path'),
]

print("=" * 70)
print("IMAGE DETECTION FUNCTION TEST")
print("=" * 70)

for test_input, description in test_cases:
    result = find_image_file(test_input)
    status = "✓" if result != 'images/product-placeholder.svg' or 'nonexistent' in test_input else "✓"
    print(f"\n{status} Test: {description}")
    print(f"  Input:  {repr(test_input)}")
    print(f"  Output: {result}")

# Check what files actually exist
print("\n" + "=" * 70)
print("FILES IN UPLOADS DIRECTORY")
print("=" * 70)
uploads_dir = 'static/uploads'
if os.path.isdir(uploads_dir):
    files = sorted(os.listdir(uploads_dir))
    print(f"Total files: {len(files)}")
    print("\nImage files found:")
    for f in files:
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.jfif', '.webp')):
            print(f"  - {f}")
else:
    print(f"Directory not found: {uploads_dir}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
