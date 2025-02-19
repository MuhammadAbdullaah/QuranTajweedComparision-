import tempfile
import csv
from io import BytesIO
import zipfile
import matplotlib.pyplot as plt
import cv2

def save_csv_to_temp(csv_data):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode='w', newline='', encoding='utf-8')
    writer = csv.writer(temp_file)
    writer.writerows(csv_data)
    temp_file.close()
    return temp_file.name

def save_image_to_temp(image):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    cv2.imwrite(temp_file.name, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    temp_file.close()
    return temp_file.name

def create_zip(combined_images):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for page_no, image in combined_images:
            img_bytes = BytesIO()
            plt.imsave(img_bytes, image, format='png')
            zip_file.writestr(f"page_{page_no}.png", img_bytes.getvalue())
    zip_buffer.seek(0)
    return zip_buffer

def create_split_lines_zip_for_both(mushaf_split_dict, app_split_dict):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for page_no, lines in mushaf_split_dict.items():
            for i, line_img in enumerate(lines, start=1):
                img_bytes = BytesIO()
                plt.imsave(img_bytes, line_img, format="png")
                file_path = f"mushaf/page_{page_no}/line_{i}.png"
                zip_file.writestr(file_path, img_bytes.getvalue())
        for page_no, lines in app_split_dict.items():
            for i, line_img in enumerate(lines, start=1):
                img_bytes = BytesIO()
                plt.imsave(img_bytes, line_img, format="png")
                file_path = f"app/page_{page_no}/line_{i}.png"
                zip_file.writestr(file_path, img_bytes.getvalue())
    zip_buffer.seek(0)
    return zip_buffer
