import pytest

def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest file
    after command line options have been parsed.
    """
    config.test_results = []

def pytest_sessionfinish(session):
    """
    Hook that runs after all tests are completed.
    Generates the final Markdown report.
    """
    results = getattr(session.config, 'test_results', [])
    if not results:
        print("\n\nNo test results were collected. Report not generated.")
        return

    num_total = len(results)
    # A test is successful if its actual status is 'SUCCESS' or if it's a planned cancellation.
    successes = [r for r in results if r["actual"] == "SUCCESS" or (r["actual"] == "CANCELLED" and "cancel" in r["id"].lower())]
    failures = [r for r in results if r not in successes]
    num_success = len(successes)
    num_failed = len(failures)

    report = f"""# CyberBlitz Exhaustive Test Report

## Summary

- **Total Tests Executed:** {num_total}
- **✅ Successful Tests:** {num_success}
- **❌ Failed Tests:** {num_failed}

---

## Failed Test Details

"""

    if not failures:
        report += "No failures detected. All tests passed successfully or were gracefully handled!"
    else:
        for failure in failures:
            report += f"### ❌ Test ID: `{failure['id']}`\n\n"
            report += f"- **Input Combination:**\n"
            report += f"```json\n{failure['inputs']}\n```\n"
            report += f"- **Expected Behavior:** {failure['expected']}\n"
            report += f"- **Actual Result:** {failure['actual']} - {failure['error']}\n"
            if failure['output']:
                report += f"- **Captured Output:**\n"
                report += f"```\n{failure['output']}\n```\n"
            report += "\n---\n"

    with open("analysis_report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n\nComprehensive test report generated at: analysis_report.txt")
