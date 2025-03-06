# from collections import Counter, defaultdict

# def compare_line_data(data1, data2):
#     comparison_results = []
#     num_lines = min(len(data1), len(data2))
#     for i in range(num_lines):
#         line_no, seq1 = data1[i]
#         _, seq2 = data2[i]
#         counter1 = Counter(seq1)
#         counter2 = Counter(seq2)
#         if counter1 == counter2:
#             issues = "Looks good"
#         else:
#             issues_list = []
#             missing = counter1 - counter2
#             if missing:
#                 issues_list.append(f"Missing colors in APP image: {dict(missing)}")
#             extra = counter2 - counter1
#             if extra:
#                 issues_list.append(f"Found extra colors in APP image: {dict(extra)}")
#             issues = "; ".join(issues_list)
#         comparison_results.append((line_no, seq1, seq2, issues))
#     return comparison_results

# def create_csv_data(comparison_results):
#     csv_lines = [["Line Number", "Mushaf Tajweed Colors", "App Tajweed Colors", "Issues"]]
#     for line_no, seq1, seq2, issues in comparison_results:
#         csv_lines.append([line_no, ",".join(seq1), ",".join(seq2), issues])
#     return csv_lines

# # ---------------------------
# # New: Issue Report CSV Logic
# # ---------------------------
# def create_issue_csv_data(page_no, comparison_results, boxes_data_ref, boxes_data_app):
    
#     csv_rows = []
    
#     def get_positions(seq_ref, seq_other):
#         pos = defaultdict(list)
#         for i, color in enumerate(seq_ref):
#             pos[color].append(i + 1)
#         for color in seq_other:
#             if pos[color]:
#                 pos[color].pop(0)
#         return pos

#     for (line_no, seq1, seq2, issues) in comparison_results:
#         if issues == "Looks good":
#             continue
#         from collections import Counter
#         counter1 = Counter(seq1)
#         counter2 = Counter(seq2)
#         missing = counter1 - counter2
#         extra = counter2 - counter1
        
#         missing_positions = get_positions(seq1, seq2)
#         extra_positions = get_positions(seq2, seq1)
        
#         boxes_line_ref = None
#         boxes_line_app = None
#         for ln, b_line in boxes_data_ref:
#             if ln == line_no:
#                 boxes_line_ref = b_line
#                 break
#         for ln, b_line in boxes_data_app:
#             if ln == line_no:
#                 boxes_line_app = b_line
#                 break
        
#         for color, cnt in missing.items():
#             positions = missing_positions.get(color, [])
#             pos = positions[0] if positions else "N/A"
#             if boxes_line_ref and isinstance(pos, int) and pos - 1 < len(boxes_line_ref):
#                 _, _, w, h, _ = boxes_line_ref[pos - 1]
#                 bbox = f"[{w}, {h}]"
#             else:
#                 bbox = "N/A"
#             csv_rows.append([page_no, line_no, f"missing {color}({cnt}) at position {pos} {bbox}"])
        
#         for color, cnt in extra.items():
#             positions = extra_positions.get(color, [])
#             pos = positions[0] if positions else "N/A"
#             if boxes_line_app and isinstance(pos, int) and pos - 1 < len(boxes_line_app):
#                 _, _, w, h, _ = boxes_line_app[pos - 1]
#                 bbox = f"[{w}, {h}]"
#             else:
#                 bbox = "N/A"
#             csv_rows.append([page_no, line_no, f"extra {color}({cnt}) at position {pos} {bbox}"])
    
#     return csv_rows



from collections import Counter, defaultdict

def compare_line_data(data1, data2):
    comparison_results = []
    num_lines = min(len(data1), len(data2))
    for i in range(num_lines):
        line_no, seq1 = data1[i]
        _, seq2 = data2[i]
        counter1 = Counter(seq1)
        counter2 = Counter(seq2)
        if counter1 == counter2:
            issues = "Looks good"
        else:
            issues_list = []
            missing = counter1 - counter2
            if missing:
                issues_list.append(f"Missing colors in APP image: {dict(missing)}")
            extra = counter2 - counter1
            if extra:
                issues_list.append(f"Found extra colors in APP image: {dict(extra)}")
            issues = "; ".join(issues_list)
        comparison_results.append((line_no, seq1, seq2, issues))
    return comparison_results


def create_csv_data(comparison_results):
    """
    Creates a standard CSV (line_no, Mushaf Colors, App Colors, Issues).
    """
    csv_lines = [["Line Number", "Mushaf Tajweed Colors", "App Tajweed Colors", "Issues"]]
    for line_no, seq1, seq2, issues in comparison_results:
        csv_lines.append([line_no, ",".join(seq1), ",".join(seq2), issues])
    return csv_lines


# -----------------------------------
# New: Issue Report CSV with ignoring
# -----------------------------------
def create_issue_csv_data(page_no, comparison_results, boxes_data_ref, boxes_data_app, ignore_issues_dict=None):
    """
    For each line that has counter differences (i.e. not "Looks good"),
    generate a CSV row for each missing/extra color as follows:
      Page, Line, Issue

    'ignore_issues_dict' is a dictionary of the form:
      {
        (page, line, "missing pink(1) at position 23 [9, 18]"): True,
        (page, line, "extra green(2) at position 8 [13, 17]"): True,
        ...
      }
    If an issue EXACTLY matches one in 'ignore_issues_dict', we skip it.

    The Issue string is like:
      "missing green(2) at position 3 [width, height]"
      or
      "extra pink(1) at position 16 [19, 9]"
    """
    from collections import defaultdict, Counter
    csv_rows = []
    
    def get_positions(seq_ref, seq_other):
        pos = defaultdict(list)
        for i, color in enumerate(seq_ref):
            pos[color].append(i + 1)
        for color in seq_other:
            if pos[color]:
                pos[color].pop(0)
        return pos

    for (line_no, seq1, seq2, issues) in comparison_results:
        if issues == "Looks good":
            continue

        counter1 = Counter(seq1)
        counter2 = Counter(seq2)
        missing = counter1 - counter2  # e.g. {"green": 2}
        extra = counter2 - counter1    # e.g. {"pink": 1}

        missing_positions = get_positions(seq1, seq2)
        extra_positions = get_positions(seq2, seq1)

        # Get bounding box lists for this line from boxes_data_ref and boxes_data_app.
        boxes_line_ref = None
        boxes_line_app = None
        for ln, b_line in boxes_data_ref:
            if ln == line_no:
                boxes_line_ref = b_line
                break
        for ln, b_line in boxes_data_app:
            if ln == line_no:
                boxes_line_app = b_line
                break

        # For each missing color
        for color, cnt in missing.items():
            positions = missing_positions.get(color, [])
            pos = positions[0] if positions else "N/A"
            # bounding box
            if boxes_line_ref and isinstance(pos, int) and pos - 1 < len(boxes_line_ref):
                _, _, w, h, _ = boxes_line_ref[pos - 1]
                bbox = f"[{w}, {h}]"
            else:
                bbox = "N/A"
            # e.g. "missing green(2) at position 3 [10, 12]"
            issue_str = f"missing {color}({cnt}) at position {pos} {bbox}"

            # IGNORE LOGIC
            if ignore_issues_dict and ignore_issues_dict.get((page_no, line_no, issue_str)):
                # skip
                continue

            csv_rows.append([page_no, line_no, issue_str])

        # For each extra color
        for color, cnt in extra.items():
            positions = extra_positions.get(color, [])
            pos = positions[0] if positions else "N/A"
            if boxes_line_app and isinstance(pos, int) and pos - 1 < len(boxes_line_app):
                _, _, w, h, _ = boxes_line_app[pos - 1]
                bbox = f"[{w}, {h}]"
            else:
                bbox = "N/A"
            issue_str = f"extra {color}({cnt}) at position {pos} {bbox}"

            # IGNORE LOGIC
            if ignore_issues_dict and ignore_issues_dict.get((page_no, line_no, issue_str)):
                # skip
                continue

            csv_rows.append([page_no, line_no, issue_str])
    
    return csv_rows
