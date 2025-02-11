import os
import re
from .image_processing import natural_key, process_image, combine_three_images, create_issue_image_from_boxes, split_image_into_lines
from .comparison import compare_line_data

def process_directory_pair(mushaf_directory, app_directory, color_ranges, box_colors, start_page=None, end_page=None, num_lines=15):
    all_comparisons = []
    all_combined_images = []
    
    # Get files using natural sorting
    dir1_files = sorted(
        [f for f in os.listdir(mushaf_directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
        key=natural_key
    )
    dir2_files = sorted(
        [f for f in os.listdir(app_directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
        key=natural_key
    )
    
    # Filter by range if provided
    if start_page is not None and end_page is not None:
        def filter_by_range(files):
            filtered = []
            for f in files:
                match = re.search(r'\d+', f)
                if match:
                    num = int(match.group())
                    if start_page <= num <= end_page:
                        filtered.append(f)
            return filtered
        dir1_files = filter_by_range(dir1_files)
        dir2_files = filter_by_range(dir2_files)
    
    if len(dir1_files) != len(dir2_files):
        raise ValueError("Error: Both directories must contain the same number of images!")
    
    for file1, file2 in zip(dir1_files, dir2_files):
        from cv2 import imread, cvtColor, COLOR_BGR2RGB
        page_no = natural_key(file1)  # Use the extracted page number as heading
        
        # Load images
        image1 = imread(os.path.join(mushaf_directory, file1))
        image2 = imread(os.path.join(app_directory, file2))
        if image1 is None or image2 is None:
            continue
        
        image1 = cvtColor(image1, COLOR_BGR2RGB)
        image2 = cvtColor(image2, COLOR_BGR2RGB)
        
        # Process images and get boxes data for both reference and app images
        line_data1, marked_image1, boxes_data1 = process_image(image1, color_ranges, box_colors, num_lines=num_lines)
        line_data2, marked_image2, boxes_data2 = process_image(image2, color_ranges, box_colors, num_lines=num_lines)
        comparison_results = compare_line_data(line_data1, line_data2)
        
        # Append comparison results for CSV output.
        for line_result in comparison_results:
            all_comparisons.append([
                page_no, 
                line_result[0], 
                ",".join(line_result[1]), 
                ",".join(line_result[2]), 
                line_result[3]
            ])
        
        # Create center issue image using the original marking logic.
        issue_image = create_issue_image_from_boxes(image2, boxes_data2, comparison_results)
        combined_image = combine_three_images(marked_image1, issue_image, marked_image2)
        all_combined_images.append((page_no, combined_image))
    
    return all_comparisons, all_combined_images

def get_split_lines_dict(directory, start_page=None, end_page=None, num_lines=15):
    from cv2 import imread, cvtColor, COLOR_BGR2RGB
    files = sorted(
        [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
        key=natural_key
    )
    if start_page is not None and end_page is not None:
        def filter_by_range(files):
            filtered = []
            for f in files:
                match = re.search(r'\d+', f)
                if match:
                    num = int(match.group())
                    if start_page <= num <= end_page:
                        filtered.append(f)
            return filtered
        files = filter_by_range(files)
    
    split_lines_dict = {}
    for f in files:
        page_no = natural_key(f)
        img = imread(os.path.join(directory, f))
        if img is None:
            continue
        img = cvtColor(img, COLOR_BGR2RGB)
        lines = split_image_into_lines(img, num_lines=num_lines)
        split_lines_dict[page_no] = lines
    return split_lines_dict
