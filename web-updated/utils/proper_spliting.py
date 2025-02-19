# import cv2
# import numpy as np
# from PIL import Image
# import os
# import csv


# LINES_PER_PAGE = 15  # Number of lines per page

# def split_lines(image, num_lines=LINES_PER_PAGE):
#   """Splits an image into lines based on uniform height division."""
#   h, w, _ = image.shape
#   line_height = h // num_lines
#   return [image[i * line_height:(i + 1) * line_height, :] for i in range(num_lines)]


# def split_mushaf_lines(image, num_lines=LINES_PER_PAGE):
#     """Splits an image into lines based on uniform height division while preserving transparency."""
#     pil_image = Image.fromarray(image)
    
#     # Get dimensions
#     width, height = pil_image.size
#     line_height = height // num_lines
#     # Split and save with transparency
#     lines = []
#     for i in range(num_lines):
#         # Calculate coordinates for cropping
#         top = i * line_height
#         bottom = (i + 1) * line_height

#         # Crop the line
#         line = pil_image.crop((0, top  + i , width, bottom + i))
#         lines.append(line)

#     return lines


# # Usage example:
# # save_line_images(mushaf_img, lines_dir, page_num)

# # Example usage:
# # image = cv2.imread('path_to_image.png')
# # lines = split_lines(image)
# # for i, line in enumerate(lines):
# #     cv2.imwrite(f'line_{i}.png', line)



# # Define expected line height range (for step size ~136)
# LINE_HEIGHT_MIN = 120
# LINE_HEIGHT_MAX = 140


# def detect_lines_smart(image, num_lines=15, color=(0, 128, 0), thickness=1):
#     """Detects and draws red lines at the end of each text line."""
#     if image.shape[-1] == 4:  # Convert BGRA -> BGR if needed
#         image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#     blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
#     h, w, _ = image.shape
#     step = h // num_lines  # Approximate line height
    
#     # Compute horizontal projection to detect text density
#     horizontal_projection = np.sum(blurred, axis=1)
#     peaks = []
#     line_heights = []
#     abnormal_lines = []  # Store abnormal line data

#     last_y = 0  # Track previous line position
#     threshold = np.mean(horizontal_projection) * 0.5  # Threshold for detecting gaps
#     #print(horizontal_projection, len(horizontal_projection), threshold)

#     for i in range(1, num_lines):
#         start = max(i * step - step // 3, 0)
#         end = min(i * step + step // 3, h)

#         # Find deepest gap where text density is lowest
#         min_index = np.argmin(horizontal_projection[start:end]) + start

#         # Make sure it's an actual separation (check pixel density)
#         while min_index > 5 and horizontal_projection[min_index] > threshold:
#             min_index -= 1

#         # Compute detected line height
#         line_height = min_index - last_y
#         #print("Start", start, end, "Min", min_index, "Mean", horizontal_projection[min_index], "Threshold", threshold, "last y", last_y, "step", step, "line height", line_height)

#         last_y = min_index

#         # Store line heights
#         line_heights.append(f"{i}:{line_height}")

#         # Check if line height is abnormal
#         if not (LINE_HEIGHT_MIN <= line_height <= LINE_HEIGHT_MAX):
#             abnormal_lines.append(f"{i}:{line_height}")

#         peaks.append(min_index)

#     # Draw red lines
#     image_with_lines = image.copy()
#     for y in peaks:
#         cv2.line(image_with_lines, (0, y), (w, y), color, thickness)

#     return image_with_lines, line_heights, abnormal_lines

# def process_images(transparent_dir):
#     """Processes images, marks lines, and saves normal + abnormal line heights to CSV."""
#     output_dir = os.path.join(transparent_dir, "line_marking_smart")
#     os.makedirs(output_dir, exist_ok=True)
    
#     csv_all_path = os.path.join(output_dir, "line_heights_all.csv")
#     csv_abnormal_path = os.path.join(output_dir, "line_heights_abnormal.csv")

#     with open(csv_all_path, "w", newline="") as csvfile_all, \
#          open(csv_abnormal_path, "w", newline="") as csvfile_abnormal:

#         csv_writer_all = csv.writer(csvfile_all)
#         csv_writer_abnormal = csv.writer(csvfile_abnormal)

#         csv_writer_all.writerow(["page", "lines"])  # Header
#         csv_writer_abnormal.writerow(["page", "lines"])  # Header

#         for page_num in range(2, 605):
#             image_path = os.path.join(transparent_dir, f"{page_num}.png")
#             output_path = os.path.join(output_dir, f"{page_num}.png")

#             if os.path.exists(image_path):
#                 image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
#                 processed_image, line_heights, abnormal_lines = detect_lines_smart(image)

#                 cv2.imwrite(output_path, processed_image)

#                 # Log all line heights
#                 csv_writer_all.writerow([page_num, ", ".join(line_heights)])

#                 # Log abnormal lines if any
#                 if abnormal_lines:
#                     csv_writer_abnormal.writerow([page_num, ", ".join(abnormal_lines)])

#                 print(f"Processed {page_num}.png -> Saved to {output_path}")
#             else:
#                 print(f"Skipping {page_num}.png (File not found)")

#     print(f"CSV files saved at:\n- {csv_all_path}\n- {csv_abnormal_path}")

# process_images("/home/infiniti/Tarteel/app/QuranTajweedComparision-/sample/mushaf")


import cv2
import numpy as np
from PIL import Image
import os
import csv
import glob

# Constants
LINES_PER_PAGE = 15  # Expected number of lines per page
LINE_HEIGHT_MIN = 120
LINE_HEIGHT_MAX = 140

def split_lines(image, num_lines=LINES_PER_PAGE):
    """Splits an image into lines based on uniform height division."""
    h, w, _ = image.shape
    line_height = h // num_lines
    return [image[i * line_height:(i + 1) * line_height, :] for i in range(num_lines)]

def split_mushaf_lines(image, num_lines=LINES_PER_PAGE):
    """Splits an image into lines based on uniform height division while preserving transparency."""
    pil_image = Image.fromarray(image)
    
    width, height = pil_image.size
    line_height = height // num_lines
    lines = []
    for i in range(num_lines):
        top = i * line_height
        bottom = (i + 1) * line_height
        # Thoda offset add karte hue (agar zarurat ho)
        line = pil_image.crop((0, top + i, width, bottom + i))
        lines.append(line)
    return lines

def detect_lines_smart(image, num_lines=15, color=(0, 128, 0), thickness=1):
    """
    Detects text line boundaries using horizontal projection,
    draws red lines at the detected boundaries, and returns:
      - image_with_lines (the marked image),
      - line_heights (list of computed line heights),
      - abnormal_lines (list of lines outside expected range),
      - peaks (list of y-coordinates where lines were detected).
    """
    # Agar image mein transparency ho (4 channel), to convert kar dein BGR
    if image.shape[-1] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    h, w, _ = image.shape
    step = h // num_lines  # Approximate step (line height)
    horizontal_projection = np.sum(blurred, axis=1)
    
    peaks = []
    line_heights = []
    abnormal_lines = []
    last_y = 0
    threshold = np.mean(horizontal_projection) * 0.5

    for i in range(1, num_lines):
        start = max(i * step - step // 3, 0)
        end = min(i * step + step // 3, h)
        min_index = np.argmin(horizontal_projection[start:end]) + start

        while min_index > 5 and horizontal_projection[min_index] > threshold:
            min_index -= 1

        line_height = min_index - last_y
        last_y = min_index
        line_heights.append(f"{i}:{line_height}")
        if not (LINE_HEIGHT_MIN <= line_height <= LINE_HEIGHT_MAX):
            abnormal_lines.append(f"{i}:{line_height}")
        peaks.append(min_index)

    image_with_lines = image.copy()
    for y in peaks:
        cv2.line(image_with_lines, (0, y), (w, y), color, thickness)
    return image_with_lines, line_heights, abnormal_lines, peaks

def split_image_by_peaks(image, peaks):
    """
    Splits the given image into segments using detected peaks as boundaries.
    Boundaries: [0] + peaks + [image height]
    Returns a list of image segments.
    """
    h, w, _ = image.shape
    boundaries = [0] + peaks + [h]
    line_images = []
    for i in range(len(boundaries) - 1):
        top = boundaries[i]
        bottom = boundaries[i+1]
        segment = image[top:bottom, :].copy()
        line_images.append(segment)
    return line_images

def process_images(input_dir):
    """
    Processes images from the input directory:
      - Marks text lines using smart detection.
      - Saves the marked images in an output folder.
      - Splits each page based on detected line boundaries and saves the split lines
        in a separate folder structure.
      - Also logs line heights (normal and abnormal) into CSV files.
    """
    output_dir = os.path.join(input_dir, "line_marking_smart")
    os.makedirs(output_dir, exist_ok=True)
    
    csv_all_path = os.path.join(output_dir, "line_heights_all.csv")
    csv_abnormal_path = os.path.join(output_dir, "line_heights_abnormal.csv")
    
    # Folder for split lines
    split_lines_dir = os.path.join(input_dir, "split_lines")
    os.makedirs(split_lines_dir, exist_ok=True)

    with open(csv_all_path, "w", newline="") as csvfile_all, \
         open(csv_abnormal_path, "w", newline="") as csvfile_abnormal:

        csv_writer_all = csv.writer(csvfile_all)
        csv_writer_abnormal = csv.writer(csvfile_abnormal)

        csv_writer_all.writerow(["page", "lines"])  # Header
        csv_writer_abnormal.writerow(["page", "lines"])  # Header

        # Process pages in a given numeric range (update range as needed)
        for page_num in range(2, 605):
            image_path = os.path.join(input_dir, f"{page_num}.png")
            output_image_path = os.path.join(output_dir, f"{page_num}.png")

            if os.path.exists(image_path):
                # Read image (with transparency if available)
                image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
                processed_image, line_heights, abnormal_lines, peaks = detect_lines_smart(image)
                cv2.imwrite(output_image_path, processed_image)
                csv_writer_all.writerow([page_num, ", ".join(line_heights)])
                if abnormal_lines:
                    csv_writer_abnormal.writerow([page_num, ", ".join(abnormal_lines)])
                print(f"Processed {page_num}.png -> Saved marked image to {output_image_path}")
                
                # --- Split the page into lines using detected peaks ---
                # Note: Splitting is done on the original image (without red lines)
                split_lines_list = split_image_by_peaks(image, peaks)
                
                # Create an output folder for split lines for this page
                page_split_dir = os.path.join(split_lines_dir, f"page_{page_num}")
                os.makedirs(page_split_dir, exist_ok=True)
                
                for idx, line_img in enumerate(split_lines_list):
                    line_output_path = os.path.join(page_split_dir, f"line{idx+1}.png")
                    cv2.imwrite(line_output_path, line_img)
                    print(f"Saved split line {idx+1} for page {page_num} to {line_output_path}")
            else:
                print(f"Skipping {page_num}.png (File not found)")
                
    print(f"CSV files saved at:\n- {csv_all_path}\n- {csv_abnormal_path}")

# Example usage:
process_images("/home/infiniti/Tarteel/app/QuranTajweedComparision-/sample/mushaf")
