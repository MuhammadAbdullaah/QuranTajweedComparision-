from collections import Counter

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
    csv_lines = [["Line Number", "Mushaf Tajweed Colors", "App Tajweed Colors", "Issues"]]
    for line_no, seq1, seq2, issues in comparison_results:
        csv_lines.append([line_no, ",".join(seq1), ",".join(seq2), issues])
    return csv_lines
