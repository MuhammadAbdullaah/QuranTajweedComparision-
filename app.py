import cv2
import numpy as np
import streamlit as st
import pandas as pd
import tempfile
import csv
import os

# --------------------------
# Utility Functions
# --------------------------

def load_image_from_bytes(image_bytes):
    # Convert uploaded file (bytes) to a CV2 image in RGB
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
            issues = "No issues"
        else:
            issues_list = []
            len1, len2 = len(seq1), len(seq2)
            min_len = min(len1, len2)
            for j in range(min_len):
                if seq1[j] != seq2[j]:
                    issues_list.append(f"Position {j+1}: expected {seq1[j]}, found {seq2[j]}")
            if len1 > len2:
                extra = seq1[len2:]
                issues_list.append(f"Missing in compared image: {extra}")
            elif len2 > len1:
                extra = seq2[len1:]
                issues_list.append(f"Extra in compared image: {extra}")
            issues = "; ".join(issues_list)
        comparison_results.append((line_no, seq1, seq2, issues))
    return comparison_results

def create_csv_data(comparison_results):
    csv_lines = [["Line Number", "Image1 Tajweed Colors", "Image2 Tajweed Colors", "Issues"]]
    for line_no, seq1, seq2, issues in comparison_results:
        csv_lines.append([line_no, ",".join(seq1), ",".join(seq2), issues])
    return csv_lines

def save_csv_to_temp(csv_data):
    # Create a temporary CSV file and return its path
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode='w', newline='', encoding='utf-8')
    writer = csv.writer(temp_file)
    writer.writerows(csv_data)
    temp_file.close()
    return temp_file.name

def combine_images_side_by_side(image1, image2):
    # Resize image2 to match image1 height if necessary
    if image1.shape[0] != image2.shape[0]:
        scale = image1.shape[0] / image2.shape[0]
        new_width = int(image2.shape[1] * scale)
        image2 = cv2.resize(image2, (new_width, image1.shape[0]))
    combined = np.concatenate((image1, image2), axis=1)
    return combined

def save_image_to_temp(image):
    # Save image temporarily and return file path
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    cv2.imwrite(temp_file.name, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    temp_file.close()
    return temp_file.name

# --------------------------
# Define the Color Ranges & Box Colors
# --------------------------
color_ranges = {
        "red": ((0, 100, 100), (10, 255, 255)),       
        # "dark_red": ((170, 50, 50), (180, 255, 255)),  
        "blue": ((90, 50, 50), (130, 255, 255)),
        "green": ((35, 50, 50), (85, 255, 255)),        
        "orange": ((10, 100, 100), (25, 255, 255)),    
        "purple": ((130, 50, 50), (160, 255, 255)),     
        "yellow": ((25, 50, 50), (35, 255, 255)),     
        "brown": ((10, 100, 20), (20, 255, 200)),    
        "pink": ((160, 50, 50), (170, 255, 255)),      
        # "silver": ((0, 0, 192), (180, 30, 255)),     
        # "white": ((0, 0, 200), (180, 30, 255)),         
        # "gray": ((0, 0, 150), (180, 30, 200)),     
        # "deep_blue": ((95, 150, 100), (110, 255, 255)),  # #056996
        # "sky_blue": ((90, 100, 100), (105, 255, 255)),  # #00adef
        # "light_blue": ((95, 50, 150), (110, 255, 255)), # #94d8f3
        # "navy_blue": ((100, 150, 50), (115, 255, 255)),
}
    
box_colors = {
        "red": (255, 0, 0),
        # "dark_red": (200, 0, 0),
        "blue": (0, 102, 148),
        "green": (0, 255, 0),
        "orange": (255, 165, 0),
        "purple": (128, 0, 128),
        "yellow": (255, 255, 0),
        "brown": (139, 69, 19),
        "pink": (255, 20, 147),
        # "silver": (192, 192, 192),
        # "white": (255, 255, 255),
        # "gray": (171, 171, 169), 
        # "deep_blue": (5, 105, 150),  # #056996
        # "sky_blue": (0, 173, 239),   # #00adef
        # "light_blue": (148, 216, 243), # #94d8f3
        # "navy_blue": (0, 102, 148),  # #006694
}

# --------------------------
# Streamlit App
# --------------------------
st.title("Tajweed Mark Comparison")

st.write("""
Upload the **Correct Image** and the **Compared Image**.
Then click the **Process Images** button to see the results.
""")

# File uploaders for two images
uploaded_file1 = st.file_uploader("Upload Correct Image", type=["png", "jpg", "jpeg"])
uploaded_file2 = st.file_uploader("Upload Compared Image", type=["png", "jpg", "jpeg"])

if uploaded_file1 is not None and uploaded_file2 is not None:
    # Load images from uploaded files
    image1 = load_image_from_bytes(uploaded_file1.read())
    image2 = load_image_from_bytes(uploaded_file2.read())
    
    if image1 is not None and image2 is not None:
        # Display the uploaded images
        st.subheader("Uploaded Images")
        col1, col2 = st.columns(2)
        with col1:
            st.image(image1, caption="Correct Image", use_column_width=True)
        with col2:
            st.image(image2, caption="Compared Image", use_column_width=True)
            
        # Process images when button is clicked
        if st.button("Process Images"):
            num_lines = 15  # You can change this as needed
            min_contour_size = 5
            
            # Process each image
            line_data1, marked_image1 = process_image(image1, color_ranges, box_colors, min_contour_size, num_lines)
            line_data2, marked_image2 = process_image(image2, color_ranges, box_colors, min_contour_size, num_lines)
            
            # Compare line data
            comparison_results = compare_line_data(line_data1, line_data2)
            csv_data = create_csv_data(comparison_results)
            
            # Create a DataFrame for display
            df = pd.DataFrame(csv_data[1:], columns=csv_data[0])
            st.subheader("Comparison CSV Data")
            st.dataframe(df)
            
            # Save CSV to a temporary file and provide download link
            csv_file_path = save_csv_to_temp(csv_data)
            with open(csv_file_path, "rb") as f:
                st.download_button(label="Download CSV", data=f, file_name="tajweed_comparison.csv", mime="text/csv")
            
            # Combine the marked images side by side
            combined_image = combine_images_side_by_side(marked_image1, marked_image2)
            st.subheader("Marked Images (Combined)")
            st.image(combined_image, use_column_width=True)
            
            # Save combined image to a temporary file and provide download link
            combined_image_path = save_image_to_temp(combined_image)
            with open(combined_image_path, "rb") as f:
                st.download_button(label="Download Combined Image", data=f, file_name="tajweed_marked_pages.png", mime="image/png")
            
            # Optionally, you can display individual marked images as well
            st.subheader("Individual Marked Images")
            col1, col2 = st.columns(2)
            with col1:
                st.image(marked_image1, caption="Correct Image Marked", use_column_width=True)
            with col2:
                st.image(marked_image2, caption="Compared Image Marked", use_column_width=True)
                
            # Clean up temporary files if needed
            # os.remove(csv_file_path)
            # os.remove(combined_image_path)
else:
    st.info("Please upload both images to continue.")
