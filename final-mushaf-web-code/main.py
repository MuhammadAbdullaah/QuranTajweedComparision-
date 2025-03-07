import streamlit as st
import os
import cv2
import numpy as np
import time

from utils.image_processing import natural_key
from utils.comparison import create_csv_data
from utils.file_handling import save_csv_to_temp, create_zip, create_split_lines_zip_for_both
from utils.directory_processing import process_directory_pair, get_split_lines_dict_for_both

# --------------------------
# Color Configuration
# --------------------------
color_ranges = {
    "red": ((0, 100, 100), (10, 255, 255)),
    "blue": ((90, 50, 50), (130, 255, 255)),
    "green": ((35, 50, 50), (85, 255, 255)),
    "orange": ((10, 100, 100), (25, 255, 255)),
    "purple": ((130, 50, 50), (160, 255, 255)),
    "yellow": ((25, 50, 50), (35, 255, 255)),
    "brown": ((10, 100, 20), (20, 255, 200)),
    "pink": ((160, 50, 50), (170, 255, 255)),
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
}

# --------------------------
# App Configuration
# --------------------------
st.set_page_config(layout="wide", page_title="Tajweed Comparison")
st.title("Tajweed Mark Comparison Web App - Real-Time Display (With Ignore CSV)")

st.header("Directory Comparison Settings")
mushaf_directory = st.text_input("Reference Directory (Mushaf):", value="./sample/mushaf-604/")
app_directory = st.text_input("Comparison Directory (App):", value="./sample/app-56")
csv_path_for_mushaf = st.text_input("Mushaf Line Heights CSV Path:", value="./csv/all_line_height.csv")
ignore_csv_path = st.text_input("Ignore Issues CSV Path (optional):", value="./csv/ignored_issues.csv")

range_option = st.radio("Image Range Option:", ["All", "Range"])
if range_option == "Range":
    start_page = st.number_input("Start Page", value=1, min_value=1, step=1)
    end_page = st.number_input("End Page", value=10, min_value=1, step=1)
    if end_page < start_page:
        st.error("End Page must be >= Start Page.")
        start_page, end_page = None, None
else:
    start_page = None
    end_page = None

# --------------------------
# Containers for Real-Time Display and Progress
# --------------------------
grid_container = st.empty()
progress_container = st.empty()

all_comparisons = []
all_combined_images = []
all_issue_csv = []

composite_images = []

progress_container.text("Starting processing...")

mushaf_files = sorted(
    [f for f in os.listdir(mushaf_directory) if f.lower().endswith(('.png','.jpg','.jpeg'))],
    key=natural_key
)
app_files = sorted(
    [f for f in os.listdir(app_directory) if f.lower().endswith(('.png','.jpg','.jpeg'))],
    key=natural_key
)

if start_page and end_page:
    def filter_by_range(files):
        filtered = []
        for f in files:
            match = re.search(r'\d+', f)
            if match:
                num = int(match.group())
                if start_page <= num <= end_page:
                    filtered.append(f)
        return filtered
    mushaf_files = filter_by_range(mushaf_files)
    app_files = filter_by_range(app_files)

if len(mushaf_files) != len(app_files):
    st.error("Both directories must contain the same number of images!")
    st.stop()

from utils.directory_processing import load_mushaf_line_heights, load_ignore_csv
mushaf_heights = load_mushaf_line_heights(csv_path_for_mushaf)
ignore_dict = {}
if ignore_csv_path and os.path.exists(ignore_csv_path):
    ignore_dict = load_ignore_csv(ignore_csv_path)

for file1, file2 in zip(mushaf_files, app_files):
    page_no = natural_key(file1)
    mushaf_path = os.path.join(mushaf_directory, file1)
    app_path = os.path.join(app_directory, file2)
    
    mushaf_img = cv2.imread(mushaf_path)
    app_img = cv2.imread(app_path)
    if mushaf_img is None or app_img is None:
        continue
    mushaf_img = cv2.cvtColor(mushaf_img, cv2.COLOR_BGR2RGB)
    app_img = cv2.cvtColor(app_img, cv2.COLOR_BGR2RGB)
    
    heights_arr = mushaf_heights.get(page_no, [])
    if not heights_arr:
        continue  
    if len(heights_arr) < 15:
        needed = 15 - len(heights_arr)
        avg = int(np.mean(heights_arr)) if heights_arr else 50
        heights_arr += [avg] * needed
    elif len(heights_arr) > 15:
        heights_arr = heights_arr[:15]
    
    H = mushaf_img.shape[0]
    csum = np.cumsum(heights_arr)
    if csum[-1] < H:
        csum[-1] = H
    else:
        csum = [min(x, H) for x in csum]
    
    mushaf_line_data = []
    mushaf_boxes_data = []
    marked_segments = []
    segment_heights = []
    prev = 0
    line_idx = 1
    raw_line_segments = {}
    for boundary in csum:
        top = prev
        bottom = boundary
        if bottom <= top:
            continue
        segment = mushaf_img[top:bottom, :].copy()
        raw_line_segments[line_idx] = segment
        seq, seg_marked, boxes_line = __import__('utils.image_processing').process_line_segment(segment, color_ranges, box_colors)
        mushaf_line_data.append((line_idx, seq))

        shifted_boxes = [(x, y+top, w, h, c) for (x, y, w, h, c) in boxes_line]
        mushaf_boxes_data.append((line_idx, shifted_boxes))
        marked_segments.append(seg_marked)
        segment_heights.append(segment.shape[0])
        line_idx += 1
        prev = bottom
    if marked_segments:
        final_mushaf_marked = np.vstack(marked_segments)
    else:
        final_mushaf_marked = mushaf_img.copy()
    
    app_line_data, marked_app, app_boxes_data = __import__('utils.image_processing').process_image(app_img, color_ranges, box_colors, num_lines=15)
    
    comp_results = compare_line_data(mushaf_line_data, app_line_data)
    for res in comp_results:
        all_comparisons.append([page_no, res[0], ",".join(res[1]), ",".join(res[2]), res[3]])
    
    issue_rows = create_issue_csv_data(page_no, comp_results, mushaf_boxes_data, app_boxes_data, ignore_issues_dict=ignore_dict)
    all_issue_csv.extend(issue_rows)
    
    problem_lines = [line_no for (line_no, seq1, seq2, issues) in comp_results if issues != "Looks good"]
    cum_heights = np.cumsum(segment_heights)
    y_top = 0
    for i, seg_height in enumerate(segment_heights, start=1):
        y_bottom = cum_heights[i-1]
        if i in problem_lines:
            cv2.rectangle(final_mushaf_marked, (0, y_top), (final_mushaf_marked.shape[1]-1, y_top+seg_height-1), (255, 0, 0), 4)
        y_top += seg_height
    
    issue_image = __import__('utils.image_processing').create_issue_image_from_boxes(app_img, app_boxes_data, comp_results, ignore_issues_dict=ignore_dict, page_no=page_no)
    
    composite = __import__('utils.image_processing').combine_three_images(final_mushaf_marked, issue_image, marked_app)
    if any(row[0] == page_no for row in issue_rows):
        all_combined_images.append((page_no, composite))
        composite_images = [ (pg, img) for (pg, img) in all_combined_images ]
        num_per_row = 4
        grid_container.empty()
        grid_rows = [composite_images[i:i+num_per_row] for i in range(0, len(composite_images), num_per_row)]
        for row in grid_rows:
            cols = st.columns(len(row))
            for idx, (pg, comp_img) in enumerate(row):
                issue_rows_page = [r for r in all_issue_csv if r[0] == pg]
                line_nums = sorted(set(str(r[1]) for r in issue_rows_page))
                header = "Lines with issues: " + ", ".join(line_nums)
                details = "<br>".join([f"Line {r[1]}: {r[2].strip()}" for r in issue_rows_page])
                caption = f"<b>Page {pg}</b><br>{header}<br>{details}"
                cols[idx].markdown(f"<div style='margin: 10px;'>", unsafe_allow_html=True)
                cols[idx].image(comp_img, caption=None, use_column_width=True)
                cols[idx].markdown(caption, unsafe_allow_html=True)
                cols[idx].markdown("</div>", unsafe_allow_html=True)
    
    progress_container.text(f"Processed page {page_no}.")
    time.sleep(0.1) 

progress_container.text("Processing completed.")

# --- Final Download Buttons ---
if all_combined_images:
    full_csv = [["Page", "Line", "Mushaf Sequence", "App Sequence", "Issues"]]
    full_csv.extend(all_comparisons)
    full_csv_path = save_csv_to_temp(full_csv)
    st.download_button("Download Full Report CSV", full_csv_path, file_name="full_comparison.csv", mime="text/csv")
    
    issues_csv = [["Page", "Line", "Issues"]]
    issues_csv.extend(all_issue_csv)
    issues_csv_path = save_csv_to_temp(issues_csv)
    st.download_button("Download Issues Report CSV", issues_csv_path, file_name="issues_report.csv", mime="text/csv")
    
    zip_buf = create_zip(all_combined_images)
    st.download_button("Download Composite Images ZIP", zip_buf, file_name="comparison_images.zip", mime="application/zip")
    
    if st.button("Download Split Lines Zip"):
        try:
            mushaf_split_dict, app_split_dict = get_split_lines_dict_for_both(
                mushaf_directory,
                app_directory,
                start_page,
                end_page,
                num_lines=15,
                csv_path_for_mushaf=csv_path_for_mushaf
            )
            split_zip = create_split_lines_zip_for_both(mushaf_split_dict, app_split_dict)
            st.download_button("Download Split Lines Zip", split_zip, file_name="split_lines.zip", mime="application/zip")
        except Exception as e:
            st.error(f"Error in generating split lines zip: {e}")
