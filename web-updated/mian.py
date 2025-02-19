import streamlit as st
import os

from utils.image_processing import natural_key
from utils.comparison import create_csv_data
from utils.file_handling import save_csv_to_temp, save_image_to_temp, create_zip, create_split_lines_zip_for_both
from utils.directory_processing import process_directory_pair, get_split_lines_dict_for_both

# --------------------------
# Color Configuration
# --------------------------
color_ranges = {
    # "red": ((0, 100, 100), (10, 255, 255)),
    "blue": ((90, 50, 50), (130, 255, 255)),
    "green": ((35, 50, 50), (85, 255, 255)),
    "orange": ((10, 100, 100), (25, 255, 255)),
    "purple": ((130, 50, 50), (160, 255, 255)),
    "yellow": ((25, 50, 50), (35, 255, 255)),
    "brown": ((10, 100, 20), (20, 255, 200)),
    "pink": ((160, 50, 50), (170, 255, 255)),
}

box_colors = {
    # "red": (255, 0, 0),
    "blue": (0, 102, 148),
    "green": (0, 255, 0),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
    "yellow": (255, 255, 0),
    "brown": (139, 69, 19),
    "pink": (255, 20, 147),
}

# --------------------------
# Streamlit App (Directory Pair Mode)
# --------------------------
st.set_page_config(layout="wide", page_title="Tajweed Comparison")
st.title("Tajweed Mark Comparison Web App - Directory Pair Mode")

st.header("Directory Comparison")
mushaf_directory = st.text_input("Enter Path to Reference Directory:", value="./sample/mushaf/")
app_directory = st.text_input("Enter Path to Comparison Directory:", value="./sample/app/")

range_option = st.radio("Select Image Range Option:", ["All", "Range"])
if range_option == "Range":
    start_page = st.number_input("Start Page", value=1, min_value=1, step=1)
    end_page = st.number_input("End Page", value=10, min_value=1, step=1)
    if end_page < start_page:
        st.error("End Page must be greater than or equal to Start Page.")
        start_page, end_page = None, None
else:
    start_page = None
    end_page = None

if "last_params" not in st.session_state:
    st.session_state.last_params = {
        "mushaf_directory": mushaf_directory,
        "app_directory": app_directory,
        "range_option": range_option,
        "start_page": start_page,
        "end_page": end_page
    }
else:
    if (st.session_state.last_params.get("mushaf_directory") != mushaf_directory or
        st.session_state.last_params.get("app_directory") != app_directory or
        st.session_state.last_params.get("range_option") != range_option or
        st.session_state.last_params.get("start_page") != start_page or
        st.session_state.last_params.get("end_page") != end_page):
        st.session_state.dir_processed = None
        st.session_state.last_params = {
            "mushaf_directory": mushaf_directory,
            "app_directory": app_directory,
            "range_option": range_option,
            "start_page": start_page,
            "end_page": end_page
        }

if "dir_processed" not in st.session_state:
    st.session_state.dir_processed = None

if mushaf_directory and app_directory:
    if st.button("Process Directories") or st.session_state.dir_processed is not None:
        if not os.path.exists(mushaf_directory) or not os.path.exists(app_directory):
            st.error("Error: One or both directories do not exist!")
        else:
            with st.spinner("Processing directories..."):
                if st.session_state.dir_processed is None:
                    all_comparisons, all_combined_images, issue_csv_data = process_directory_pair(
                        mushaf_directory, app_directory, color_ranges, box_colors, start_page, end_page
                    )
                    st.session_state.dir_processed = {
                        "all_comparisons": all_comparisons,
                        "all_combined_images": all_combined_images,
                        "issue_csv_data": issue_csv_data
                    }
                results = st.session_state.dir_processed

            if results["all_comparisons"] and results["all_combined_images"]:
                st.success("Processing completed!")
                
                csv_data = [["Page", "Line", "Mushaf Sequence", "App Sequence", "Issues"]]
                csv_data.extend(results["all_comparisons"])
                csv_path = save_csv_to_temp(csv_data)
                with open(csv_path, "rb") as f:
                    st.download_button("Download Full Report CSV", f, file_name="full_comparison.csv", mime="text/csv")
                
                issue_csv = [["Page", "Line", "Issues"]]
                issue_csv.extend(results["issue_csv_data"])
                issue_csv_path = save_csv_to_temp(issue_csv)
                with open(issue_csv_path, "rb") as f:
                    st.download_button("Download Issues Report CSV", f, file_name="issues_report.csv", mime="text/csv")
                
                zip_buffer = create_zip(results["all_combined_images"])
                st.download_button("Download All Images as ZIP", zip_buffer, file_name="comparison_images.zip", mime="application/zip")
                
                st.subheader("Page Comparison Results")
                images_per_row = 4
                for row_start in range(0, len(results["all_combined_images"]), images_per_row):
                    cols = st.columns(images_per_row)
                    row_images = results["all_combined_images"][row_start:row_start+images_per_row]
                    for col_idx, (page_no, image) in enumerate(row_images):
                        page_has_issue = any([line[4] != "Looks good" for line in results["all_comparisons"] if line[0] == page_no])
                        with cols[col_idx]:
                            st.image(image, caption=f"Page {page_no}", use_container_width=True)
                            if page_has_issue:
                                lines_with_issues = [str(line[1]) for line in results["all_comparisons"] if line[0] == page_no and line[4] != "Looks good"]
                                combined_lines = ", ".join(lines_with_issues)
                                st.write("Page has issues", unsafe_allow_html=True)
                                st.write(combined_lines, unsafe_allow_html=True)

    if st.button("Download Split Lines Zip"):
        try:
            mushaf_split_dict, app_split_dict = get_split_lines_dict_for_both(
                mushaf_directory, app_directory, start_page, end_page
            )
            split_zip = create_split_lines_zip_for_both(mushaf_split_dict, app_split_dict)
            st.download_button("Download Split Lines Zip", split_zip, file_name="split_lines.zip", mime="application/zip")
        except Exception as e:
            st.error(f"Error in generating split lines zip: {e}")
