#!/usr/bin/env python3
"""
CI Accuracy Gate — Runs AI accuracy tests and fails if thresholds aren't met.

Blueprint spec (tests/README.md):
  Intent Classification: ≥70%
  Domain Detection:      ≥60%
  Entity Extraction:     ≥50%
  Characteristic Detection: ≥60%
  Out-of-Scope Detection:   ≥60%

Usage:
  python scripts/ci_accuracy_gate.py

Exit codes:
  0 — All thresholds met
  1 — One or more thresholds failed
  2 — Test execution error
"""
import os
import sys
import json
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
TESTS_DIR = Path(__file__).resolve().parent.parent / "tests"

# Thresholds from tests/README.md
THRESHOLDS = {
    "intent_classification": 0.70,
    "domain_detection": 0.60,
    "entity_extraction": 0.50,
    "characteristic_detection": 0.60,
    "out_of_scope_detection": 0.60,
}

def run_accuracy_tests():
    """Run the accuracy test suite and collect results."""
    sys.path.insert(0, str(BACKEND_DIR))
    os.chdir(BACKEND_DIR)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "command_center.settings")

    import django
    django.setup()

    from layer2.intent_parser import IntentParser

    parser = IntentParser()
    results = {}

    # Intent classification test cases
    intent_cases = [
        ("What's the status of the pumps?", "query"),
        ("Show me transformer temperatures", "query"),
        ("Compare pump 1 vs pump 2", "query"),
        ("What alerts are active?", "query"),
        ("Hello", "greeting"),
        ("Thank you", "conversation"),
        ("What's the weather like?", "out_of_scope"),
        ("How many people are on shift?", "query"),
        ("Show energy consumption trends", "query"),
        ("What maintenance is overdue?", "query"),
    ]

    correct = 0
    for text, expected in intent_cases:
        parsed = parser.parse(text)
        if parsed.type == expected:
            correct += 1
    results["intent_classification"] = correct / len(intent_cases)

    # Domain detection
    domain_cases = [
        ("Show pump status", ["industrial"]),
        ("What alerts are active?", ["alerts"]),
        ("How many people on shift?", ["people"]),
        ("Show inventory levels", ["supply"]),
        ("Show transformer temperature trends", ["industrial"]),
    ]

    correct = 0
    for text, expected_domains in domain_cases:
        parsed = parser.parse(text)
        if any(d in parsed.domains for d in expected_domains):
            correct += 1
    results["domain_detection"] = correct / len(domain_cases)

    # Entity extraction
    entity_cases = [
        ("What's pump 1 status?", {"devices": True}),
        ("Show transformer T-101", {"devices": True}),
        ("Show power from the last 24 hours", {"time": True}),
    ]

    correct = 0
    for text, expected in entity_cases:
        parsed = parser.parse(text)
        has_entities = len(parsed.entities) > 0
        if has_entities == any(expected.values()):
            correct += 1
    results["entity_extraction"] = correct / len(entity_cases)

    # Characteristic detection
    char_cases = [
        ("Show temperature trends", "trend"),
        ("Compare pump 1 vs pump 2", "comparison"),
        ("What's the distribution of alerts?", "distribution"),
    ]

    correct = 0
    for text, expected_char in char_cases:
        parsed = parser.parse(text)
        if parsed.primary_characteristic == expected_char:
            correct += 1
    results["characteristic_detection"] = correct / len(char_cases)

    # Out-of-scope detection
    oos_cases = [
        ("What's the weather like?", True),
        ("Tell me a joke", True),
        ("What's the stock price?", True),
        ("Show pump status", False),
        ("What alerts are active?", False),
    ]

    correct = 0
    for text, should_be_oos in oos_cases:
        parsed = parser.parse(text)
        is_oos = parsed.type == "out_of_scope"
        if is_oos == should_be_oos:
            correct += 1
    results["out_of_scope_detection"] = correct / len(oos_cases)

    return results


def main():
    print("=" * 60)
    print("  CI ACCURACY GATE")
    print("=" * 60)

    try:
        results = run_accuracy_tests()
    except Exception as e:
        print(f"\nERROR: Test execution failed: {e}")
        sys.exit(2)

    all_passed = True
    print(f"\n{'Test':<30} {'Score':>8} {'Threshold':>10} {'Status':>8}")
    print("-" * 60)

    for test_name, threshold in THRESHOLDS.items():
        score = results.get(test_name, 0.0)
        passed = score >= threshold
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"{test_name:<30} {score*100:>7.1f}% {threshold*100:>9.0f}% {status:>8}")

    print("-" * 60)

    # Write JSON report
    report_path = Path(__file__).resolve().parent.parent / "tests" / "ci_accuracy_report.json"
    report = {
        "passed": all_passed,
        "results": {k: {"score": v, "threshold": THRESHOLDS.get(k, 0), "passed": v >= THRESHOLDS.get(k, 0)} for k, v in results.items()},
    }
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\nReport saved to: {report_path}")

    if all_passed:
        print("\nACCURACY GATE: PASSED")
        sys.exit(0)
    else:
        print("\nACCURACY GATE: FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
