import os
import re
from .image_processing import (natural_key, process_image, process_line_segment,
                               combine_three_images, create_issue_image_from_boxes,
                               split_image_into_lines, detect_lines_smart, split_image_by_peaks)
from .comparison import compare_line_data

def process_directory_pair(mushaf_directory, app_directory, color_ranges, box_colors, start_page=None, end_page=None, num_lines=15):
    
    all_comparisons = []
    all_combined_images = []
    all_issue_csv = []
    
    dir1_files = sorted(
        [f for f in os.listdir(mushaf_directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
        key=natural_key
    )
    dir2_files = sorted(
        [f for f in os.listdir(app_directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
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
        dir1_files = filter_by_range(dir1_files)
        dir2_files = filter_by_range(dir2_files)
    
    if len(dir1_files) != len(dir2_files):
        raise ValueError("Error: Both directories must contain the same number of images!")
    
    for file1, file2 in zip(dir1_files, dir2_files):
        from cv2 import imread, cvtColor, COLOR_BGR2RGB
        page_no = natural_key(file1)
        
        image1 = imread(os.path.join(mushaf_directory, file1))
        image2 = imread(os.path.join(app_directory, file2))
        if image1 is None or image2 is None:
            continue
        image1 = cvtColor(image1, COLOR_BGR2RGB)
        image2 = cvtColor(image2, COLOR_BGR2RGB)
        
        # Mushaf processing using smart detection:
        # 1. Get red line boundaries.
        smart_marked, _, _, peaks = detect_lines_smart(image1, num_lines=num_lines)
        # 2. Split mushaf image using these peaks.
        segments = split_image_by_peaks(image1, peaks)
        line_data1 = []
        boxes_data1 = []
        marked_segments = []
        for i, seg in enumerate(segments):
            # Process each segment (line) using process_line_segment.
            line_seq, marked_seg, boxes_seg = process_line_segment(seg, color_ranges, box_colors, min_contour_size=5)
            line_data1.append((i+1, line_seq))
            boxes_data1.append((i+1, boxes_seg))
            marked_segments.append(marked_seg)
        # Reassemble the processed segments vertically for composite display.
        import numpy as np
        final_marked_image1 = np.vstack(marked_segments)
        
        # APP processing (uniform splitting via process_image).
        line_data2, marked_image2, boxes_data2 = process_image(image2, color_ranges, box_colors, num_lines=num_lines)
        
        # Compare line data.
        comparison_results = compare_line_data(line_data1, line_data2)
        for line_result in comparison_results:
            all_comparisons.append([
                page_no, 
                line_result[0], 
                ",".join(line_result[1]), 
                ",".join(line_result[2]), 
                line_result[3]
            ])
        
        from .comparison import create_issue_csv_data
        if any(cr[3] != "Looks good" for cr in comparison_results):
            issue_csv_rows = create_issue_csv_data(page_no, comparison_results, boxes_data1, boxes_data2)
            all_issue_csv.extend(issue_csv_rows)
        
        issue_image = create_issue_image_from_boxes(image2, boxes_data2, comparison_results)
        combined_image = combine_three_images(final_marked_image1, issue_image, marked_image2)
        all_combined_images.append((page_no, combined_image))
    
    return all_comparisons, all_combined_images, all_issue_csv

def get_split_lines_dict_for_both(mushaf_directory, app_directory, start_page=None, end_page=None, num_lines=15):
    from cv2 import imread, cvtColor, COLOR_BGR2RGB
    import re

    def get_split_lines_dict(directory, smart=False):
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
        
        split_dict = {}
        for f in files:
            page_no = natural_key(f)
            img = imread(os.path.join(directory, f))
            if img is None:
                continue
            img = cvtColor(img, COLOR_BGR2RGB)
            if smart:
                _, _, _, peaks = detect_lines_smart(img, num_lines=num_lines)
                lines = split_image_by_peaks(img, peaks)
            else:
                lines = split_image_into_lines(img, num_lines=num_lines)
            split_dict[page_no] = lines
        return split_dict

    mushaf_split_dict = get_split_lines_dict(mushaf_directory, smart=True)
    app_split_dict = get_split_lines_dict(app_directory, smart=False)
    return mushaf_split_dict, app_split_dict
