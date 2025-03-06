# import os
# import re
# from .image_processing import (natural_key, process_image, process_line_segment,
#                                combine_three_images, create_issue_image_from_boxes,
#                                split_image_into_lines, detect_lines_smart, split_image_by_peaks)
# from .comparison import compare_line_data

# def process_directory_pair(mushaf_directory, app_directory, color_ranges, box_colors, start_page=None, end_page=None, num_lines=15):
    
#     all_comparisons = []
#     all_combined_images = []
#     all_issue_csv = []
    
#     dir1_files = sorted(
#         [f for f in os.listdir(mushaf_directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
#         key=natural_key
#     )
#     dir2_files = sorted(
#         [f for f in os.listdir(app_directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
#         key=natural_key
#     )
    
#     if start_page is not None and end_page is not None:
#         def filter_by_range(files):
#             filtered = []
#             for f in files:
#                 match = re.search(r'\d+', f)
#                 if match:
#                     num = int(match.group())
#                     if start_page <= num <= end_page:
#                         filtered.append(f)
#             return filtered
#         dir1_files = filter_by_range(dir1_files)
#         dir2_files = filter_by_range(dir2_files)
    
#     if len(dir1_files) != len(dir2_files):
#         raise ValueError("Error: Both directories must contain the same number of images!")
    
#     for file1, file2 in zip(dir1_files, dir2_files):
#         from cv2 import imread, cvtColor, COLOR_BGR2RGB
#         page_no = natural_key(file1)
        
#         image1 = imread(os.path.join(mushaf_directory, file1))
#         image2 = imread(os.path.join(app_directory, file2))
#         if image1 is None or image2 is None:
#             continue
#         image1 = cvtColor(image1, COLOR_BGR2RGB)
#         image2 = cvtColor(image2, COLOR_BGR2RGB)
        
#         # Mushaf processing using smart detection:
#         # 1. Get red line boundaries.
#         smart_marked, _, _, peaks = detect_lines_smart(image1, num_lines=num_lines)
#         # 2. Split mushaf image using these peaks.
#         segments = split_image_by_peaks(image1, peaks)
#         line_data1 = []
#         boxes_data1 = []
#         marked_segments = []
#         for i, seg in enumerate(segments):
#             # Process each segment (line) using process_line_segment.
#             line_seq, marked_seg, boxes_seg = process_line_segment(seg, color_ranges, box_colors, min_contour_size=5)
#             line_data1.append((i+1, line_seq))
#             boxes_data1.append((i+1, boxes_seg))
#             marked_segments.append(marked_seg)
#         # Reassemble the processed segments vertically for composite display.
#         import numpy as np
#         final_marked_image1 = np.vstack(marked_segments)
        
#         # APP processing (uniform splitting via process_image).
#         line_data2, marked_image2, boxes_data2 = process_image(image2, color_ranges, box_colors, num_lines=num_lines)
        
#         # Compare line data.
#         comparison_results = compare_line_data(line_data1, line_data2)
#         for line_result in comparison_results:
#             all_comparisons.append([
#                 page_no, 
#                 line_result[0], 
#                 ",".join(line_result[1]), 
#                 ",".join(line_result[2]), 
#                 line_result[3]
#             ])
        
#         from .comparison import create_issue_csv_data
#         if any(cr[3] != "Looks good" for cr in comparison_results):
#             issue_csv_rows = create_issue_csv_data(page_no, comparison_results, boxes_data1, boxes_data2)
#             all_issue_csv.extend(issue_csv_rows)
        
#         issue_image = create_issue_image_from_boxes(image2, boxes_data2, comparison_results)
#         combined_image = combine_three_images(final_marked_image1, issue_image, marked_image2)
#         all_combined_images.append((page_no, combined_image))
    
#     return all_comparisons, all_combined_images, all_issue_csv

# def get_split_lines_dict_for_both(mushaf_directory, app_directory, start_page=None, end_page=None, num_lines=15):
#     from cv2 import imread, cvtColor, COLOR_BGR2RGB
#     import re

#     def get_split_lines_dict(directory, smart=False):
#         files = sorted(
#             [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
#             key=natural_key
#         )
#         if start_page is not None and end_page is not None:
#             def filter_by_range(files):
#                 filtered = []
#                 for f in files:
#                     match = re.search(r'\d+', f)
#                     if match:
#                         num = int(match.group())
#                         if start_page <= num <= end_page:
#                             filtered.append(f)
#                 return filtered
#             files = filter_by_range(files)
        
#         split_dict = {}
#         for f in files:
#             page_no = natural_key(f)
#             img = imread(os.path.join(directory, f))
#             if img is None:
#                 continue
#             img = cvtColor(img, COLOR_BGR2RGB)
#             if smart:
#                 _, _, _, peaks = detect_lines_smart(img, num_lines=num_lines)
#                 lines = split_image_by_peaks(img, peaks)
#             else:
#                 lines = split_image_into_lines(img, num_lines=num_lines)
#             split_dict[page_no] = lines
#         return split_dict

#     mushaf_split_dict = get_split_lines_dict(mushaf_directory, smart=True)
#     app_split_dict = get_split_lines_dict(app_directory, smart=False)
#     return mushaf_split_dict, app_split_dict




import os
import re
import csv
import numpy as np
from .image_processing import (
    natural_key, process_image, process_line_segment, 
    create_issue_image_from_boxes, split_image_into_lines,
    combine_three_images
)
from .comparison import compare_line_data, create_issue_csv_data


def load_mushaf_line_heights(csv_path):
    """
    Reads a CSV file that has columns like:
      page, lines
    Where 'lines' is a string like "1:134, 2:125, 3:110, ..."
    Returns a dict:
      { page_no: [height1, height2, ...], ... }
    """
    line_heights_dict = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if not row or len(row) < 2:
                continue
            page_str = row[0]
            lines_str = row[1]
            try:
                page_no = int(page_str)
            except:
                continue
            pairs = lines_str.split(",")
            heights = []
            for p in pairs:
                p = p.strip()
                if ":" in p:
                    _, val = p.split(":")
                    val = val.strip()
                    try:
                        heights.append(int(val))
                    except:
                        pass
            line_heights_dict[page_no] = heights
    return line_heights_dict


def load_ignore_csv(ignore_csv_path):
    """
    Reads a CSV that has columns:
      Page, Line, Ignore_issues, Issue_exists
    Example row:
      6, 15, missing pink(1) at position 23 [9, 18], no

    We'll store them in a dict:
      ignore_dict[(page_no, line_no, "missing pink(1) at position 23 [9, 18]")] = True
    """
    ignore_dict = {}
    with open(ignore_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter='\t')
        # If your CSV is comma-separated, use `csv.reader` or adjust the delimiter
        # or just do "reader = csv.reader(f)" and parse columns by index
        # For demonstration, let's do a flexible approach:
        # We'll assume columns are: Page,Line,Ignore_issues,Issue_exists
        # and the delimiter might be ',' if you have a normal CSV.
        # We'll guess the user has a normal CSV with commas:

        # So let's do:
        f.seek(0)
        reader = csv.reader(f)
        header = next(reader, None)
        # we expect header = ["Page", "Line", "Ignore_issues", "Issue_exists"]

        if header is None:
            return ignore_dict

        # find column indexes
        col_map = {}
        for i, col in enumerate(header):
            col_map[col.strip()] = i

        for row in reader:
            if len(row) < 3:
                continue
            # parse page, line, ignore_issue
            try:
                page_no = int(row[col_map["Page"]])
                line_no = int(row[col_map["Line"]])
                issue_str = row[col_map["Ignore_issues"]].strip()
                # issue_exists = row[col_map["Issue_exists"]]
                # we don't actually need "issue_exists" for ignoring logic
                ignore_dict[(page_no, line_no, issue_str)] = True
            except:
                continue

    return ignore_dict


def process_directory_pair(
    mushaf_directory, 
    app_directory, 
    color_ranges, 
    box_colors, 
    start_page=None, 
    end_page=None, 
    num_lines=15,
    csv_path_for_mushaf=None,
    ignore_csv_path=None
):
    """
    For Mushaf: uses CSV-based line heights to split lines.
    For App: uses uniform splitting.

    Also uses 'ignore_csv_path' to skip certain issues in final CSV + final images.
    """
    if not csv_path_for_mushaf or not os.path.exists(csv_path_for_mushaf):
        raise ValueError("Please provide a valid CSV path for Mushaf line heights!")
    line_heights_dict = load_mushaf_line_heights(csv_path_for_mushaf)

    # Load ignore CSV
    ignore_issues_dict = {}
    if ignore_csv_path and os.path.exists(ignore_csv_path):
        ignore_issues_dict = load_ignore_csv(ignore_csv_path)

    from cv2 import imread, cvtColor, COLOR_BGR2RGB

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
    
    from .image_processing import process_image, process_line_segment, create_issue_image_from_boxes, combine_three_images
    import numpy as np

    for file1, file2 in zip(dir1_files, dir2_files):
        page_no = natural_key(file1)
        img_mushaf_path = os.path.join(mushaf_directory, file1)
        img_app_path = os.path.join(app_directory, file2)

        mushaf_img = imread(img_mushaf_path)
        app_img = imread(img_app_path)
        if mushaf_img is None or app_img is None:
            continue
        mushaf_img = cvtColor(mushaf_img, COLOR_BGR2RGB)
        app_img = cvtColor(app_img, COLOR_BGR2RGB)

        # MUSHAF splitting from CSV
        heights_arr = line_heights_dict.get(page_no, [])
        if not heights_arr:
            # skip or fallback
            continue

        # If we want EXACT lines = num_lines
        if len(heights_arr) < num_lines:
            needed = num_lines - len(heights_arr)
            avg_height = int(np.mean(heights_arr)) if heights_arr else 50
            for _ in range(needed):
                heights_arr.append(avg_height)
        elif len(heights_arr) > num_lines:
            heights_arr = heights_arr[:num_lines]

        H = mushaf_img.shape[0]
        csum = np.cumsum(heights_arr)
        if csum[-1] < H:
            csum[-1] = H
        else:
            csum = [min(x, H) for x in csum]

        line_data_mushaf = []
        boxes_data_mushaf = []
        line_segments_marked = []
        prev_boundary = 0
        idx_line = 1
        for boundary in csum:
            top = prev_boundary
            bottom = boundary
            if bottom <= top:
                continue
            line_segment = mushaf_img[top:bottom, :].copy()
            seq, seg_marked, boxes_line = process_line_segment(line_segment, color_ranges, box_colors)
            # shift bounding boxes
            shifted_boxes_line = []
            for (x, y, w, h, c) in boxes_line:
                shifted_boxes_line.append((x, y + top, w, h, c))
            line_data_mushaf.append((idx_line, seq))
            boxes_data_mushaf.append((idx_line, shifted_boxes_line))
            line_segments_marked.append(seg_marked)
            idx_line += 1
            prev_boundary = bottom

        if line_segments_marked:
            final_mushaf_marked = np.vstack(line_segments_marked)
        else:
            final_mushaf_marked = mushaf_img.copy()

        # APP
        line_data_app, marked_app, boxes_data_app = process_image(app_img, color_ranges, box_colors, num_lines=num_lines)

        # Compare
        comparison_results = compare_line_data(line_data_mushaf, line_data_app)
        for line_result in comparison_results:
            all_comparisons.append([
                page_no, 
                line_result[0], 
                ",".join(line_result[1]), 
                ",".join(line_result[2]), 
                line_result[3]
            ])

        # Issue CSV
        issue_csv_rows = create_issue_csv_data(
            page_no,
            comparison_results,
            boxes_data_mushaf,
            boxes_data_app,
            ignore_issues_dict=ignore_issues_dict
        )
        all_issue_csv.extend(issue_csv_rows)

        # Issue Image
        issue_image = create_issue_image_from_boxes(
            app_img,
            boxes_data_app,
            comparison_results,
            ignore_issues_dict=ignore_issues_dict,
            page_no=page_no
        )
        combined_image = combine_three_images(final_mushaf_marked, issue_image, marked_app)
        all_combined_images.append((page_no, combined_image))

    return all_comparisons, all_combined_images, all_issue_csv


def get_split_lines_dict_for_both(
    mushaf_directory, 
    app_directory, 
    start_page=None, 
    end_page=None, 
    num_lines=15,
    csv_path_for_mushaf=None
):
    """
    Returns dict of page -> list of line images for Mushaf & App
    (No ignoring logic needed here, just the splitting.)
    """
    if not csv_path_for_mushaf or not os.path.exists(csv_path_for_mushaf):
        raise ValueError("Please provide a valid CSV path for Mushaf line heights!")
    line_heights_dict = load_mushaf_line_heights(csv_path_for_mushaf)

    from cv2 import imread, cvtColor, COLOR_BGR2RGB
    import re
    from .image_processing import split_image_into_lines, process_line_segment, natural_key

    mushaf_split_dict = {}
    app_split_dict = {}

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
        raise ValueError("Both directories must contain the same number of images for splitting!")

    import numpy as np

    for mf, af in zip(dir1_files, dir2_files):
        pm = natural_key(mf)
        pa = natural_key(af)
        img_mushaf = imread(os.path.join(mushaf_directory, mf))
        img_app = imread(os.path.join(app_directory, af))
        if img_mushaf is None or img_app is None:
            continue
        img_mushaf = cvtColor(img_mushaf, COLOR_BGR2RGB)
        img_app = cvtColor(img_app, COLOR_BGR2RGB)

        # MUSHAF
        heights_arr = line_heights_dict.get(pm, [])
        if not heights_arr:
            mushaf_split_dict[pm] = []
            app_split_dict[pa] = []
            continue

        if len(heights_arr) < num_lines:
            needed = num_lines - len(heights_arr)
            avg_height = int(np.mean(heights_arr)) if heights_arr else 50
            for _ in range(needed):
                heights_arr.append(avg_height)
        elif len(heights_arr) > num_lines:
            heights_arr = heights_arr[:num_lines]

        H = img_mushaf.shape[0]
        csum = np.cumsum(heights_arr)
        if csum[-1] < H:
            csum[-1] = H
        else:
            csum = [min(x, H) for x in csum]

        lines_mushaf = []
        prev = 0
        for boundary in csum:
            if boundary <= prev:
                continue
            lines_mushaf.append(img_mushaf[prev:boundary, :].copy())
            prev = boundary

        mushaf_split_dict[pm] = lines_mushaf

        # APP
        lines_app = split_image_into_lines(img_app, num_lines=num_lines)
        app_split_dict[pa] = lines_app

    return mushaf_split_dict, app_split_dict
