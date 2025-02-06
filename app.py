import cv2
import numpy as np
import streamlit as st
import pandas as pd
import tempfile
import csv
import os
from io import BytesIO
import zipfile
import matplotlib.pyplot as plt
# --------------------------
# Utility Functions
# --------------------------

def load_image_from_bytes(image_bytes):
    file_bytes = np.asarray(bytearray(image_bytes), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if image is None:
        st.error("Error loading image!")
        return None
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

def convert_to_hsv(image):
    return cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

def process_image(image, color_ranges, box_colors, min_contour_size=5, num_lines=15):
    hsv = convert_to_hsv(image)
    height, width = image.shape[:2]
    line_height = height // num_lines
    marked_image = image.copy()
    line_data = []

    for line_num in range(num_lines):
        y_start = line_num * line_height
        y_end = y_start + line_height
        if line_num == num_lines - 1:
            y_end = height  # Include any remaining pixels

        line_region = hsv[y_start:y_end, :]
        processed_mask = np.zeros(line_region.shape[:2], dtype=np.uint8)
        color_sequence = []

        for color_name in color_ranges:
            lower, upper = color_ranges[color_name]
            mask = cv2.inRange(line_region, np.array(lower), np.array(upper))
            mask = cv2.bitwise_and(mask, cv2.bitwise_not(processed_mask))
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if w >= min_contour_size and h >= min_contour_size:
                    color_sequence.append((x, color_name))
                    cv2.drawContours(processed_mask, [cnt], -1, 255, -1)
                    cv2.rectangle(marked_image, (x, y_start + y), (x + w, y_start + y + h), box_colors[color_name], 2)
        
        color_sequence.sort(key=lambda x: x[0])
        line_data.append((line_num + 1, [color for _, color in color_sequence]))
    return line_data, marked_image

def compare_line_data(data1, data2):
    comparison_results = []
    num_lines = min(len(data1), len(data2))
    for i in range(num_lines):
        line_no, seq1 = data1[i]
        _, seq2 = data2[i]
        if seq1 == seq2:
            issues = "Looks good"
        else:
            issues_list = []
            len1, len2 = len(seq1), len(seq2)
            min_len = min(len1, len2)
            for j in range(min_len):
                if seq1[j] != seq2[j]:
                    issues_list.append(f"Color Position {j+1}: expected {seq1[j]}, found {seq2[j]}")
            if len1 > len2:
                extra = seq1[len2:]
                issues_list.append(f"Missing colors in APP image: {extra}")
            elif len2 > len1:
                extra = seq2[len1:]
                issues_list.append(f"Found extra colors in APP image: {extra}")
            issues = "; ".join(issues_list)
        comparison_results.append((line_no, seq1, seq2, issues))
    return comparison_results

def create_csv_data(comparison_results):
    csv_lines = [["Line Number", "Mushaf Tajweed Colors", "App Tajweed Colors", "Issues"]]
    for line_no, seq1, seq2, issues in comparison_results:
        csv_lines.append([line_no, ",".join(seq1), ",".join(seq2), issues])
    return csv_lines

def save_csv_to_temp(csv_data):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode='w', newline='', encoding='utf-8')
    writer = csv.writer(temp_file)
    writer.writerows(csv_data)
    temp_file.close()
    return temp_file.name

def combine_images_side_by_side(image1, image2):
    if image1.shape[0] != image2.shape[0]:
        scale = image1.shape[0] / image2.shape[0]
        new_width = int(image2.shape[1] * scale)
        image2 = cv2.resize(image2, (new_width, image1.shape[0]))
    combined = np.concatenate((image1, image2), axis=1)
    return combined

def save_image_to_temp(image):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    cv2.imwrite(temp_file.name, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    temp_file.close()
    return temp_file.name

def process_directory_pair(mushaf_directory, app_directory, color_ranges, box_colors):
    all_comparisons = []
    all_combined_images = []
    
    # Get sorted list of image files in directories
    dir1_files = sorted([f for f in os.listdir(mushaf_directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    dir2_files = sorted([f for f in os.listdir(app_directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    
    if len(dir1_files) != len(dir2_files):
        st.error("Error: Both directories must contain the same number of images!")
        return None, None
    
    for page_idx, (file1, file2) in enumerate(zip(dir1_files, dir2_files)):
        # Load images
        image1 = cv2.imread(os.path.join(mushaf_directory, file1))
        image2 = cv2.imread(os.path.join(app_directory, file2))
        if image1 is None or image2 is None:
            st.error(f"Error loading images: {file1} or {file2}")
            continue
        
        image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2RGB)
        image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2RGB)
        
        # Process and compare
        line_data1, marked_image1 = process_image(image1, color_ranges, box_colors)
        line_data2, marked_image2 = process_image(image2, color_ranges, box_colors)
        comparison_results = compare_line_data(line_data1, line_data2)
        
        # Store results
        for line_result in comparison_results:
            all_comparisons.append([
                page_idx + 1, 
                line_result[0], 
                ",".join(line_result[1]), 
                ",".join(line_result[2]), 
                line_result[3]
            ])
        
        # Create combined image
        combined_image = combine_images_side_by_side(marked_image1, marked_image2)
        all_combined_images.append((page_idx + 1, combined_image))
    
    return all_comparisons, all_combined_images

def create_zip(combined_images):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for page_num, image in combined_images:
            img_bytes = BytesIO()
            plt.imsave(img_bytes, image, format='png')
            zip_file.writestr(f"page_{page_num}.png", img_bytes.getvalue())
    zip_buffer.seek(0)
    return zip_buffer

# --------------------------
# Streamlit App
# --------------------------

st.set_page_config(layout="wide", page_title="Tajweed Comparison")
st.title("Tajweed Mark Comparison Web App")

# Mode selection
mode = st.radio("Comparison Mode:", ["Single Image Pair", "Directory Pair"])

# Color Configuration
color_ranges = {
    "red": ((0, 100, 100), (10, 255, 255)),
    "blue": ((90, 50, 50), (130, 255, 255)),
    "green": ((35, 50, 50), (85, 255, 255)),
    "orange": ((10, 100, 100), (25, 255, 255)),
    "purple": ((130, 50, 50), (160, 255, 255)),
    "yellow": ((25, 50, 50), (35, 255, 255)),
    "brown": ((10, 100, 20), (20, 255, 200)),
    "pink": ((160, 50, 50), (170, 255, 255)),
    "golden": ((20, 100, 100), (30, 255, 255)),
}

box_colors = {
    "red": (255, 0, 0),
    "blue": (0, 102, 148),
    "green": (0, 255, 0),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
    "yellow": (255, 255, 0),
    "brown": (139, 69, 19),
    "pink": (255, 20, 147),
    "golden": (198, 145, 25),
}

# --------------------------
# Single Image Pair Interface
# --------------------------

if mode == "Single Image Pair":
    st.header("Single Image Comparison")
    uploaded_file1 = st.file_uploader("Upload Correct Image", type=["png", "jpg", "jpeg"])
    uploaded_file2 = st.file_uploader("Upload Compared Image", type=["png", "jpg", "jpeg"])

    if uploaded_file1 is not None and uploaded_file2 is not None:
        image1 = load_image_from_bytes(uploaded_file1.read())
        image2 = load_image_from_bytes(uploaded_file2.read())
        
        if image1 is not None and image2 is not None:
            st.subheader("Uploaded Images")
            col1, col2 = st.columns(2)
            with col1:
                st.image(image1, caption="Correct Image", use_container_width=True)
            with col2:
                st.image(image2, caption="Compared Image", use_container_width=True)

            if st.button("Process Images"):
                line_data1, marked_image1 = process_image(image1, color_ranges, box_colors)
                line_data2, marked_image2 = process_image(image2, color_ranges, box_colors)
                comparison_results = compare_line_data(line_data1, line_data2)
                csv_data = create_csv_data(comparison_results)
                
                df = pd.DataFrame(csv_data[1:], columns=csv_data[0])
                st.subheader("Comparison CSV Data")
                st.dataframe(df)
                
                csv_file_path = save_csv_to_temp(csv_data)
                with open(csv_file_path, "rb") as f:
                    st.download_button(label="Download CSV", data=f, file_name="tajweed_comparison.csv", mime="text/csv")
                
                combined_image = combine_images_side_by_side(marked_image1, marked_image2)
                st.subheader("Marked Images (Combined)")
                st.image(combined_image, use_column_width=True)
                
                combined_image_path = save_image_to_temp(combined_image)
                with open(combined_image_path, "rb") as f:
                    st.download_button(label="Download Combined Image", data=f, file_name="tajweed_marked_pages.png", mime="image/png")

# --------------------------
# Directory Pair Interface
# --------------------------

else:
    st.header("Directory Comparison")
    mushaf_directory = st.text_input("Enter Path to Reference Directory:", value="./sample/mushaf/")
    app_directory = st.text_input("Enter Path to Comparison Directory:", value="./sample/app/")

    if mushaf_directory and app_directory:
        if st.button("Process Directories"):
            if not os.path.exists(mushaf_directory) or not os.path.exists(app_directory):
                st.error("Error: One or both directories do not exist!")
            else:
                with st.spinner("Processing directories..."):
                    all_comparisons, all_combined_images = process_directory_pair(mushaf_directory, app_directory, color_ranges, box_colors)
                    
                    if all_comparisons and all_combined_images:
                        st.success("Processing completed!")
                        
                        # CSV Download
                        csv_data = [["Page", "Line", "Mushaf", "App", "Issues"]]
                        csv_data.extend(all_comparisons)
                        csv_path = save_csv_to_temp(csv_data)
                        with open(csv_path, "rb") as f:
                            st.download_button("Download Full Report CSV", f, file_name="full_comparison.csv", mime="text/csv")
                        
                        # Zip Download
                        zip_buffer = create_zip(all_combined_images)
                        st.download_button("Download All Images as ZIP", zip_buffer, file_name="comparison_images.zip", mime="application/zip")
                        
                        # Grid Display
                        st.subheader("Page Comparison Results")
                        images_per_row = 4
                        for row_start in range(0, len(all_combined_images), images_per_row):
                            cols = st.columns(images_per_row)
                            row_images = all_combined_images[row_start:row_start+images_per_row]
                            for col_idx, (page_num, image) in enumerate(row_images):
                                page_has_issue = any([line[4] != "Looks good" for line in all_comparisons if line[0] == page_num])

                                # Detect the lines that has issues and print those lines
                                with cols[col_idx]:
                                    st.image(image, caption=f"Page {page_num}", use_container_width=True)
                                    if page_has_issue:
                                        lines_with_issues = [str(line[1]) for line in all_comparisons if line[0] == page_num and line[4] != "Looks good"]
                                        combined_lines = ", ".join(lines_with_issues)

                                        st.write("Page has issues", unsafe_allow_html=True)
                                        st.write(combined_lines, unsafe_allow_html=True)
