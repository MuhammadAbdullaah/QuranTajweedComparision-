import cv2
import numpy as np
import re

def load_image_from_bytes(image_bytes):
    file_bytes = np.asarray(bytearray(image_bytes), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Error loading image!")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

def convert_to_hsv(image):
    return cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

def natural_key(filename):
    match = re.search(r'\d+', filename)
    return int(match.group()) if match else float('inf')

def process_image(image, color_ranges, box_colors, min_contour_size=5, num_lines=15):
    hsv = convert_to_hsv(image)
    height, width = image.shape[:2]
    line_height = height // num_lines
    marked_image = image.copy()
    line_data = []
    boxes_data = []  # list of tuples: (line_number, list of boxes)

    # Define thresholds for gray dots (if any)
    min_gray_size = 6  
    max_gray_size = 60  

    for line_num in range(num_lines):
        y_start = line_num * line_height
        y_end = y_start + line_height
        if line_num == num_lines - 1:
            y_end = height  # include any remaining pixels

        line_region = hsv[y_start:y_end, :]
        processed_mask = np.zeros(line_region.shape[:2], dtype=np.uint8)
        color_sequence = []
        boxes_line = []
        for color_name in color_ranges:
            lower, upper = color_ranges[color_name]
            mask = cv2.inRange(line_region, np.array(lower), np.array(upper))
            mask = cv2.bitwise_and(mask, cv2.bitwise_not(processed_mask))
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if color_name == "gray":
                    if w < min_gray_size or h < min_gray_size or w > max_gray_size or h > max_gray_size:
                        continue
                if w >= min_contour_size and h >= min_contour_size:
                    color_sequence.append((x, color_name))
                    boxes_line.append((x, y_start + y, w, h, color_name))
                    cv2.drawContours(processed_mask, [cnt], -1, 255, -1)
                    cv2.rectangle(marked_image, (x, y_start + y), (x + w, y_start + y + h), box_colors[color_name], 2)
        
        color_sequence.sort(key=lambda x: x[0])
        line_data.append((line_num + 1, [color for _, color in color_sequence]))
        boxes_data.append((line_num + 1, boxes_line))
    return line_data, marked_image, boxes_data

def split_image_into_lines(image, num_lines=15):
    """
    Splits an image into horizontal segments.
    Returns a list of images, each representing one line.
    """
    height, width = image.shape[:2]
    line_height = height // num_lines
    lines = []
    for i in range(num_lines):
        y_start = i * line_height
        # Ensure the last line gets any remaining pixels.
        y_end = y_start + line_height if i < num_lines - 1 else height
        line_img = image[y_start:y_end, :]
        lines.append(line_img)
    return lines

def combine_images_side_by_side(image1, image2):
    if image1.shape[0] != image2.shape[0]:
        scale = image1.shape[0] / image2.shape[0]
        new_width = int(image2.shape[1] * scale)
        image2 = cv2.resize(image2, (new_width, image1.shape[0]))
    return np.concatenate((image1, image2), axis=1)

def combine_three_images(image_left, image_center, image_right):
    h = image_left.shape[0]
    if image_center.shape[0] != h:
        scale = h / image_center.shape[0]
        image_center = cv2.resize(image_center, (int(image_center.shape[1] * scale), h))
    if image_right.shape[0] != h:
        scale = h / image_right.shape[0]
        image_right = cv2.resize(image_right, (int(image_right.shape[1] * scale), h))
    return np.concatenate((image_left, image_center, image_right), axis=1)

def create_issue_image_from_boxes(app_image, boxes_data, comparison_results):
    issue_image = app_image.copy()
    from collections import Counter
    for line_result in comparison_results:
        line_no, seq1, seq2, issues = line_result
        if issues == "Looks good":
            continue
        boxes_line = None
        for ln, boxes in boxes_data:
            if ln == line_no:
                boxes_line = boxes
                break
        if boxes_line is None:
            continue
        counter_ref = Counter(seq1)
        counter_app = Counter(seq2)
        extra_counts = {}
        for color, count in counter_app.items():
            diff = count - counter_ref.get(color, 0)
            if diff > 0:
                extra_counts[color] = diff
        for box in boxes_line:
            x, y, w, h, color_name = box
            if color_name in extra_counts and extra_counts[color_name] > 0:
                cv2.rectangle(issue_image, (x, y), (x+w, y+h), (255, 0, 0), 2)
                extra_counts[color_name] -= 1
    return issue_image
