import os
import re
import shutil

def natural_sort_key(s):
    """
    Is function se filenames ke andar ke numbers ko extract karke natural order
    mein sort kiya jata hai. Misal ke taur par: "page2.png" se pehle "page10.png" aayega.
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

# Input directory jahan aapki original PNG images mojood hain.
input_dir = r"a"  # e.g., r"C:\Users\YourName\Pictures\Input"

# Output directory jahan renamed images ko copy karna hai.
output_dir = r"b"  # e.g., r"C:\Users\YourName\Pictures\Output"

# Agar output directory exist nahi karti to use create kar lete hain.
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Sirf .png extension wali files filter karte hain.
files = [f for f in os.listdir(input_dir) if f.lower().endswith(".png")]

# Files ko natural order ke mutabiq sort karte hain.
files.sort(key=natural_sort_key)

# Har file ko sequentially rename karke output directory mein copy karte hain.
for index, filename in enumerate(files, start=1):
    new_filename = f"{index}.png"
    src_path = os.path.join(input_dir, filename)
    dest_path = os.path.join(output_dir, new_filename)
    
    # File ko copy karte hue new name assign kar rahe hain.
    shutil.copy(src_path, dest_path)
    print(f"Copied and renamed '{filename}' to '{new_filename}' in output directory")
