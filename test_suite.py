#!/usr/bin/env python3
"""
Comprehensive Testing Suite for Clase Analytics Platform
Validates file integrity, links, data consistency, and content visibility
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Set
from html.parser import HTMLParser
import math

# Configuration
BASE_DIR = "/Users/santi/clase-analytics/data/clases/2026-04-07"
REQUIRED_HTML_FILES = [
    "index.html",
    "overview.html",
    "transcripcion.html",
    "evaluacion.html",
    "timeline.html",
    "rubrics.html"
]

REQUIRED_JSON_FILES = [
    "weighted_grades.json",
    "analysis.json"
]

EXPECTED_GRADES = {
    "Aryang": 3.12,
    "Grace": 2.82,
    "Sthepen": 2.98,
    "Chilaka": 1.8
}

EXPECTED_PARTICIPATIONS = {
    "Aryang": 83,
    "Grace": 21,
    "Sthepen": 12,
    "Chilaka": 1
}

TOTAL_PARTICIPATIONS = 137

# Test Results Storage
test_results = {
    "passed": [],
    "failed": [],
    "warnings": [],
    "stats": {}
}


class LinkExtractor(HTMLParser):
    """Extract all href links from HTML"""
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, value in attrs:
                if attr == 'href':
                    self.links.append(value)


def add_pass(test_name: str, message: str = ""):
    """Record a passing test"""
    msg = f"✅ {test_name}"
    if message:
        msg += f": {message}"
    test_results["passed"].append(msg)
    print(msg)


def add_fail(test_name: str, message: str = ""):
    """Record a failing test"""
    msg = f"❌ {test_name}"
    if message:
        msg += f": {message}"
    test_results["failed"].append(msg)
    print(msg)


def add_warning(test_name: str, message: str = ""):
    """Record a warning"""
    msg = f"⚠️  {test_name}"
    if message:
        msg += f": {message}"
    test_results["warnings"].append(msg)
    print(msg)


def get_file_stats(filepath: str) -> Dict:
    """Get file size and modification date"""
    if not os.path.exists(filepath):
        return None
    stat = os.stat(filepath)
    return {
        "size_bytes": stat.st_size,
        "size_kb": round(stat.st_size / 1024, 2),
        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    }


def extract_links_from_html(filepath: str) -> List[str]:
    """Extract all href links from an HTML file"""
    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        extractor = LinkExtractor()
        extractor.feed(content)
        return extractor.links
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []


def extract_text_between_tags(filepath: str, start_tag: str, end_tag: str) -> str:
    """Extract text between HTML tags"""
    if not os.path.exists(filepath):
        return ""

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        pattern = f"{start_tag}(.*?){end_tag}"
        matches = re.findall(pattern, content, re.DOTALL)
        return " ".join(matches) if matches else ""
    except Exception as e:
        return ""


def count_html_elements(filepath: str, selector: str) -> int:
    """Count elements matching a pattern"""
    if not os.path.exists(filepath):
        return 0

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        return content.count(selector)
    except:
        return 0


def extract_json_data(filepath: str) -> Dict:
    """Load and parse JSON file"""
    if not os.path.exists(filepath):
        return {}

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return {}


# ==================== TEST SUITE ====================

def test_file_integrity():
    """Test 1: File Integrity Tests"""
    print("\n" + "="*70)
    print("TEST 1: FILE INTEGRITY TESTS")
    print("="*70)

    # Check HTML files exist
    print("\n📄 Checking Required HTML Files:")
    html_files_found = []
    for filename in REQUIRED_HTML_FILES:
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.exists(filepath):
            stats = get_file_stats(filepath)
            add_pass(f"HTML file exists: {filename}", f"{stats['size_kb']} KB")
            html_files_found.append(filename)
        else:
            add_fail(f"HTML file missing: {filename}")

    test_results["stats"]["html_files_found"] = len(html_files_found)
    test_results["stats"]["html_files_expected"] = len(REQUIRED_HTML_FILES)

    # Check JSON files exist
    print("\n📊 Checking Required JSON Files:")
    json_files_found = []
    for filename in REQUIRED_JSON_FILES:
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.exists(filepath):
            stats = get_file_stats(filepath)
            add_pass(f"JSON file exists: {filename}", f"{stats['size_kb']} KB")
            json_files_found.append(filename)
        else:
            add_fail(f"JSON file missing: {filename}")

    test_results["stats"]["json_files_found"] = len(json_files_found)
    test_results["stats"]["json_files_expected"] = len(REQUIRED_JSON_FILES)


def test_link_verification():
    """Test 2: Link Verification Tests"""
    print("\n" + "="*70)
    print("TEST 2: LINK VERIFICATION TESTS")
    print("="*70)

    internal_links = {}
    broken_links = []

    for filename in REQUIRED_HTML_FILES:
        filepath = os.path.join(BASE_DIR, filename)
        links = extract_links_from_html(filepath)

        print(f"\n📎 Links in {filename}:")
        for link in links:
            # Skip external links and anchors
            if link.startswith('http://') or link.startswith('https://') or link.startswith('mailto:'):
                continue

            # Check if it's an anchor link
            if link.startswith('#'):
                add_pass(f"  Anchor link valid: {link}")
                continue

            # Check if internal file exists
            link_path = os.path.join(BASE_DIR, link)
            if os.path.exists(link_path):
                add_pass(f"  Link valid: {link}")
                internal_links[link] = True
            elif link in REQUIRED_HTML_FILES:
                add_pass(f"  Link valid: {link} (required file)")
                internal_links[link] = True
            else:
                add_fail(f"  Broken link: {link}")
                broken_links.append((filename, link))

    test_results["stats"]["internal_links"] = len(internal_links)
    test_results["stats"]["broken_links"] = len(broken_links)

    if broken_links:
        add_warning("Some broken links detected", f"{len(broken_links)} links not found")


def test_data_consistency():
    """Test 3: Data Consistency Tests"""
    print("\n" + "="*70)
    print("TEST 3: DATA CONSISTENCY TESTS")
    print("="*70)

    # Load weighted_grades.json
    print("\n📊 Loading Grade Data:")
    grades_data = extract_json_data(os.path.join(BASE_DIR, "weighted_grades.json"))

    if not grades_data:
        add_fail("Could not load weighted_grades.json")
        return

    # Verify grades match expected values
    print("\n📈 Verifying Grades:")
    grade_mismatches = []
    for student, expected_grade in EXPECTED_GRADES.items():
        if student not in grades_data:
            add_fail(f"Grade missing for student: {student}")
            continue

        actual_grade = grades_data[student]["final_grade"]
        if abs(actual_grade - expected_grade) < 0.01:
            add_pass(f"Grade correct: {student} = {actual_grade}")
        else:
            add_fail(f"Grade mismatch: {student} (expected {expected_grade}, got {actual_grade})")
            grade_mismatches.append(student)

    test_results["stats"]["grade_mismatches"] = len(grade_mismatches)

    # Verify participations match expected values
    print("\n👥 Verifying Participation Counts:")
    participation_mismatches = []
    total_from_grades = 0

    for student, expected_count in EXPECTED_PARTICIPATIONS.items():
        if student not in grades_data:
            add_fail(f"Participation missing for student: {student}")
            continue

        actual_count = grades_data[student]["total_participations"]
        total_from_grades += actual_count

        if actual_count == expected_count:
            add_pass(f"Participation count correct: {student} = {actual_count}")
        else:
            add_fail(f"Participation mismatch: {student} (expected {expected_count}, got {actual_count})")
            participation_mismatches.append(student)

    # Verify total participations
    if total_from_grades == TOTAL_PARTICIPATIONS:
        add_pass(f"Total participations correct: {total_from_grades}")
    else:
        add_fail(f"Total participation mismatch (expected {TOTAL_PARTICIPATIONS}, got {total_from_grades})")

    test_results["stats"]["participation_mismatches"] = len(participation_mismatches)
    test_results["stats"]["total_from_grades"] = total_from_grades

    # Verify bonus calculations
    print("\n🎁 Verifying Bonus Calculations:")
    for student, data in grades_data.items():
        participations = data["total_participations"]
        expected_bonus = 0

        if participations >= 40:
            expected_bonus = 0.15
        elif participations >= 20:
            expected_bonus = 0.10
        elif participations < 5:
            expected_bonus = -0.20

        actual_bonus = data["quantity_bonus"]

        if abs(actual_bonus - expected_bonus) < 0.01:
            add_pass(f"Bonus correct: {student} ({participations} turns) = {actual_bonus}")
        else:
            add_warning(f"Bonus discrepancy: {student} (expected {expected_bonus}, got {actual_bonus})")

    # Verify weighted average calculations
    print("\n⚖️  Verifying Weighted Averages:")
    for student, data in grades_data.items():
        responses = data["breakdown"]["responses"]
        questions = data["breakdown"]["questions"]
        comments = data["breakdown"]["comments"]

        if len(responses) == 0:
            avg_response = 0
        else:
            avg_response = sum(responses) / len(responses)

        if len(questions) == 0:
            avg_question = 0
        else:
            avg_question = sum(questions) / len(questions)

        if len(comments) == 0:
            avg_comment = 0
        else:
            avg_comment = sum(comments) / len(comments)

        # Calculate expected weighted average
        weighted_avg = (avg_response * 0.50) + (avg_question * 0.30) + (avg_comment * 0.20)
        actual_weighted_avg = data["weighted_average"]

        if abs(weighted_avg - actual_weighted_avg) < 0.01:
            add_pass(f"Weighted average correct: {student} = {actual_weighted_avg:.2f}")
        else:
            add_warning(f"Weighted average discrepancy: {student} (expected {weighted_avg:.2f}, got {actual_weighted_avg})")


def test_content_visibility():
    """Test 4: Content Visibility Tests"""
    print("\n" + "="*70)
    print("TEST 4: CONTENT VISIBILITY TESTS")
    print("="*70)

    overview_path = os.path.join(BASE_DIR, "overview.html")

    # Check if all student names appear on overview
    print("\n👥 Checking Student Names on Overview:")
    overview_text = extract_text_between_tags(overview_path, "<body>", "</body>")

    for student in EXPECTED_GRADES.keys():
        if student.lower() in overview_text.lower():
            add_pass(f"Student name visible: {student}")
        else:
            add_fail(f"Student name missing: {student}")

    # Check if all grades are displayed
    print("\n📊 Checking Grades Display on Overview:")
    for student, grade in EXPECTED_GRADES.items():
        grade_str = str(grade)
        if grade_str in overview_text:
            add_pass(f"Grade displayed: {student} = {grade}")
        else:
            add_fail(f"Grade not displayed: {student} = {grade}")

    # Check participation numbers
    print("\n📈 Checking Participation Numbers:")
    for student, count in EXPECTED_PARTICIPATIONS.items():
        if str(count) in overview_text:
            add_pass(f"Participation count visible: {student} = {count}")
        else:
            add_fail(f"Participation count missing: {student} = {count}")

    # Check total participation count
    if str(TOTAL_PARTICIPATIONS) in overview_text:
        add_pass(f"Total participation count visible: {TOTAL_PARTICIPATIONS}")
    else:
        add_fail(f"Total participation count missing: {TOTAL_PARTICIPATIONS}")


def test_color_styling():
    """Test 5: Color & Styling Tests"""
    print("\n" + "="*70)
    print("TEST 5: COLOR & STYLING TESTS")
    print("="*70)

    print("\n🎨 Checking Color Scheme:")

    for filename in REQUIRED_HTML_FILES:
        filepath = os.path.join(BASE_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for purple gradient
        if "#667eea" in content and "#764ba2" in content:
            add_pass(f"Purple gradient present: {filename}")
        else:
            add_warning(f"Purple gradient colors missing: {filename}")

        # Check for white background
        if "#ffffff" in content or "white" in content.lower():
            add_pass(f"White background present: {filename}")
        else:
            add_warning(f"White background not explicitly defined: {filename}")

    # Check student colors in timeline
    print("\n🎯 Checking Student Colors in Timeline:")
    timeline_path = os.path.join(BASE_DIR, "timeline.html")
    with open(timeline_path, 'r', encoding='utf-8') as f:
        timeline_content = f.read()

    student_colors = {
        "Aryang": "#dc2626",  # red
        "Grace": "#0284c7",   # blue
        "Sthepen": "#7c3aed",  # purple
        "Chilaka": "#d97706"   # orange
    }

    for student, color in student_colors.items():
        if color in timeline_content:
            add_pass(f"Student color present: {student} = {color}")
        else:
            add_warning(f"Student color may be missing: {student} = {color}")


def test_functional_features():
    """Test 6: Functional Feature Tests"""
    print("\n" + "="*70)
    print("TEST 6: FUNCTIONAL FEATURE TESTS")
    print("="*70)

    # Check transcription filter
    print("\n🔍 Checking Transcription Filter:")
    transcription_path = os.path.join(BASE_DIR, "transcripcion.html")
    with open(transcription_path, 'r', encoding='utf-8') as f:
        trans_content = f.read()

    # Check for filter dropdown
    if "speaker-filter" in trans_content:
        add_pass("Filter dropdown present: speaker-filter")
    else:
        add_fail("Filter dropdown missing: speaker-filter")

    # Check for filter JavaScript function
    if "filterBySpeaker" in trans_content:
        add_pass("Filter JavaScript function present: filterBySpeaker()")
    else:
        add_fail("Filter JavaScript function missing: filterBySpeaker()")

    # Check for all student options in filter
    print("\n📋 Checking Student Filter Options:")
    for student in EXPECTED_GRADES.keys():
        if f'<option value="{student.upper()}">' in trans_content:
            add_pass(f"Filter option exists: {student}")
        else:
            add_fail(f"Filter option missing: {student}")

    # Count statements in transcription
    print("\n📝 Checking Transcription Statements:")
    statement_count = trans_content.count('class="student-')
    if statement_count >= TOTAL_PARTICIPATIONS - 10:  # Allow some variance
        add_pass(f"Sufficient statements found: {statement_count}")
    else:
        add_warning(f"Statement count may be low: {statement_count} (expected ~{TOTAL_PARTICIPATIONS})")


def test_formula_accuracy():
    """Test 7: Formula Accuracy Verification"""
    print("\n" + "="*70)
    print("TEST 7: FORMULA ACCURACY VERIFICATION")
    print("="*70)

    grades_data = extract_json_data(os.path.join(BASE_DIR, "weighted_grades.json"))

    print("\n⚙️  Verifying Grade Calculation Formula:")
    formula_errors = []

    for student, data in grades_data.items():
        responses = data["breakdown"]["responses"]
        questions = data["breakdown"]["questions"]
        comments = data["breakdown"]["comments"]
        bonus = data["quantity_bonus"]

        # Calculate averages
        avg_resp = sum(responses) / len(responses) if responses else 0
        avg_ques = sum(questions) / len(questions) if questions else 0
        avg_comm = sum(comments) / len(comments) if comments else 0

        # Apply formula
        calculated_grade = round((avg_resp * 0.50 + avg_ques * 0.30 + avg_comm * 0.20 + bonus), 2)
        actual_grade = data["final_grade"]

        if abs(calculated_grade - actual_grade) < 0.01:
            add_pass(f"Formula accurate: {student} = {actual_grade}")
        else:
            add_fail(f"Formula error: {student} (calculated {calculated_grade}, got {actual_grade})")
            formula_errors.append(student)

    test_results["stats"]["formula_errors"] = len(formula_errors)


def test_timeline_percentages():
    """Test 8: Timeline Percentage Tests"""
    print("\n" + "="*70)
    print("TEST 8: TIMELINE PERCENTAGE TESTS")
    print("="*70)

    timeline_path = os.path.join(BASE_DIR, "timeline.html")
    with open(timeline_path, 'r', encoding='utf-8') as f:
        timeline_content = f.read()

    print("\n📊 Checking Timeline Widths (Percentages):")

    # Extract percentages from style attributes
    width_pattern = r'width:\s*(\d+\.?\d*)%'
    widths = re.findall(width_pattern, timeline_content)

    if widths:
        total_width = sum(float(w) for w in widths)
        if abs(total_width - 100.0) < 1.0:
            add_pass(f"Timeline widths sum to 100%: {total_width:.1f}%")
        else:
            add_warning(f"Timeline widths don't sum to 100%: {total_width:.1f}%")
    else:
        add_warning("Could not extract timeline widths for verification")


def generate_report():
    """Generate final test report"""
    print("\n" + "="*70)
    print("TEST REPORT SUMMARY")
    print("="*70)

    passed = len(test_results["passed"])
    failed = len(test_results["failed"])
    warnings = len(test_results["warnings"])

    print(f"\n✅ PASSED TESTS: {passed}")
    print(f"❌ FAILED TESTS: {failed}")
    print(f"⚠️  WARNINGS: {warnings}")
    print(f"\n📊 TOTAL TESTS: {passed + failed + warnings}")

    success_rate = (passed / (passed + failed)) * 100 if (passed + failed) > 0 else 0
    print(f"✓ SUCCESS RATE: {success_rate:.1f}%")

    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)
    for key, value in test_results["stats"].items():
        print(f"  {key}: {value}")

    if failed > 0:
        print("\n" + "="*70)
        print("FAILED TESTS DETAILS")
        print("="*70)
        for i, test in enumerate(test_results["failed"], 1):
            print(f"{i}. {test}")

    if warnings > 0:
        print("\n" + "="*70)
        print("WARNINGS")
        print("="*70)
        for i, test in enumerate(test_results["warnings"], 1):
            print(f"{i}. {test}")

    # Generate JSON report
    report_path = os.path.join(BASE_DIR, "test_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "total": passed + failed + warnings,
                "success_rate": f"{success_rate:.1f}%"
            },
            "statistics": test_results["stats"],
            "details": {
                "passed_tests": test_results["passed"],
                "failed_tests": test_results["failed"],
                "warnings": test_results["warnings"]
            }
        }, f, indent=2)

    print(f"\n📄 Detailed report saved to: test_report.json")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("CLASE ANALYTICS COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Test Directory: {BASE_DIR}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run all test suites
    test_file_integrity()
    test_link_verification()
    test_data_consistency()
    test_content_visibility()
    test_color_styling()
    test_functional_features()
    test_formula_accuracy()
    test_timeline_percentages()

    # Generate report
    generate_report()


if __name__ == "__main__":
    main()
