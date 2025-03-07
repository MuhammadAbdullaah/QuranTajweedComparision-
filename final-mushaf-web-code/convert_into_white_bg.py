from PIL import Image
import os

def convert_transparent_to_white(input_path, output_path):
    img = Image.open(input_path)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    white_bg = Image.new("RGB", img.size, (255, 255, 255))
    white_bg.paste(img, mask=img.split()[3])
    white_bg.save(output_path)

if __name__ == "__main__":
    input_dir = "/home/infiniti/Tarteel/mushaf-verfication/final-mushaf-web-code/sample/mushaf-604/"
    output_dir = "/home/infiniti/Tarteel/mushaf-verfication/final-mushaf-web-code/sample/mushaf-white-bg"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for filename in os.listdir(input_dir):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            convert_transparent_to_white(input_path, output_path)
