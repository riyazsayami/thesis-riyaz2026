from ai_agent.agent import (
    get_issue_by_rule,
    get_rule_details,
    get_remediation_information,
)

from ai_agent.ai_remediator import (
    analyze_finding,
    apply_remediation,
)


RULE_KEY = "python:S4502"

SOURCE_PATH = "app/app.py"


def print_separator():
    print("=" * 60)


def main():
    print_separator()
    print(" S4502 AI REMEDIATION TEST")
    print_separator()

    print("\n[1] Fetching SonarQube issue...")

    issue = get_issue_by_rule(
        RULE_KEY
    )

    print("SonarQube issue found.")
    print(f"Rule: {issue.get('rule')}")
    print(f"Message: {issue.get('message')}")
    print(f"Component: {issue.get('component')}")
    print(f"Line: {issue.get('line')}")

    print("\n[2] Fetching SonarQube rule details...")

    rule_details = get_rule_details(
        RULE_KEY
    )

    print("Rule details found.")
    print(
        f"Rule name: "
        f"{rule_details.get('name', RULE_KEY)}"
    )

    print("\n[3] Extracting remediation guidance...")

    remediation_info = get_remediation_information(
        rule_details
    )

    print("Remediation information extracted.")

    if isinstance(remediation_info, dict):
        for key, value in remediation_info.items():
            print(f"\n--- {key.upper()} ---")
            print(value)
    else:
        print(remediation_info)

    print("\n[4] Sending finding to AI remediator...")

    result = analyze_finding(
        issue=issue,
        remediation=remediation_info,
        source_path=SOURCE_PATH,
    )

    print("\n")
    print_separator()
    print(" AI ANALYSIS")
    print_separator()

    print("\nEXPLANATION:")
    print(
        result.get(
            "explanation",
            "No explanation returned.",
        )
    )

    print("\nPROPOSED FIX:")
    print(
        result.get(
            "proposed_fix",
            "No proposed fix returned.",
        )
    )

    print("\nSECURITY IMPROVEMENT:")
    print(
        result.get(
            "security_improvement",
            "No security improvement returned.",
        )
    )

    print("\nCORRECTED CODE:")
    print_separator()

    corrected_code = result.get(
        "corrected_code",
        "",
    )

    if corrected_code:
        print(corrected_code)
    else:
        print("No corrected code returned.")

    print_separator()

    print("\nVALIDATION:")
    print_separator()

    validation = result.get(
        "validation",
        {},
    )

    checks = validation.get(
        "checks",
        [],
    )

    for check in checks:
        print(check)

    validation_passed = validation.get(
        "passed",
        False,
    )

    print(
        "\nOverall Validation:",
        "PASS"
        if validation_passed
        else "FAIL",
    )

    print("\nValidation Message:")

    print(
        validation.get(
            "message",
            "No validation message returned.",
        )
    )

    if validation_passed and corrected_code:
        print(
            "\n[5] Applying automatic code remediation..."
        )

        try:
            apply_result = apply_remediation(
                source_path=SOURCE_PATH,
                corrected_code=corrected_code,
            )

            if apply_result.get("success"):
                print(
                    "Automatic code remediation: PASS"
                )

                print(
                    f"Updated file: "
                    f"{apply_result.get('source_path')}"
                )

                backup_path = apply_result.get(
                    "backup_path"
                )

                if backup_path:
                    print(
                        f"Backup created: {backup_path}"
                    )
            else:
                print(
                    "Automatic code remediation: FAIL"
                )

        except Exception as exc:
            print(
                "Automatic code remediation: FAIL"
            )
            print(
                f"Error: {exc}"
            )

    else:
        print(
            "\n[5] Automatic code remediation skipped."
        )

        if not validation_passed:
            print(
                "Reason: AI validation did not pass."
            )
        elif not corrected_code:
            print(
                "Reason: No corrected code was returned."
            )

    print("\n")
    print_separator()
    print(" S4502 TEST COMPLETED")
    print_separator()


if __name__ == "__main__":
    main()
