import os
import re
import time
import requests


SONAR_HOST_URL = os.getenv(
    "SONAR_HOST_URL",
    "http://localhost:9000"
)

SONAR_TOKEN = os.getenv("SONAR_TOKEN")

PROJECT_KEY = "thesis-riyaz2026"

SONAR_TIMEOUT = 30
SONAR_RETRIES = 3
SONAR_RETRY_DELAY = 2


def clean_html(content):
    if not content:
        return ""

    content = re.sub(
        r"<[^>]+>",
        "",
        content
    )

    content = content.replace("&nbsp;", " ")
    content = content.replace("&lt;", "<")
    content = content.replace("&gt;", ">")
    content = content.replace("&amp;", "&")

    content = re.sub(
        r"\s+",
        " ",
        content
    )

    return content.strip()


def sonar_get(endpoint, params=None):
    if not SONAR_TOKEN:
        raise RuntimeError(
            "SONAR_TOKEN environment variable is not set."
        )

    url = f"{SONAR_HOST_URL}{endpoint}"

    last_error = None

    for attempt in range(1, SONAR_RETRIES + 1):

        try:
            response = requests.get(
                url,
                params=params,
                auth=(SONAR_TOKEN, ""),
                timeout=SONAR_TIMEOUT
            )

            response.raise_for_status()

            return response

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError
        ) as error:

            last_error = error

            if attempt < SONAR_RETRIES:
                time.sleep(SONAR_RETRY_DELAY)
                continue

            raise RuntimeError(
                f"SonarQube request failed after "
                f"{SONAR_RETRIES} attempts: {url}"
            ) from last_error

        except requests.exceptions.HTTPError as error:

            status_code = response.status_code

            raise RuntimeError(
                f"SonarQube API returned HTTP "
                f"{status_code}: {response.text}"
            ) from error

        except requests.exceptions.RequestException as error:

            raise RuntimeError(
                f"SonarQube request failed: {error}"
            ) from error


def get_issue_by_rule(rule_key):

    params = {
        "projects": PROJECT_KEY,
        "rules": rule_key,
        "resolved": "false",
        "ps": 100
    }

    response = sonar_get(
        "/api/issues/search",
        params=params
    )

    data = response.json()

    issues = data.get(
        "issues",
        []
    )

    if not issues:
        return None

    return issues[0]


def get_rule_details(rule_key):

    params = {
        "key": rule_key
    }

    response = sonar_get(
        "/api/rules/show",
        params=params
    )

    data = response.json()

    return data.get(
        "rule"
    )


def get_remediation_information(rule_details):

    if not rule_details:
        return {
            "introduction": "",
            "root_cause": "",
            "how_to_fix": ""
        }

    sections = rule_details.get(
        "descriptionSections",
        []
    )

    introduction = ""
    root_cause = ""
    how_to_fix = ""

    for section in sections:

        section_key = section.get(
            "key"
        )

        content = section.get(
            "content",
            ""
        )

        if section_key == "introduction":

            if not introduction:
                introduction = clean_html(
                    content
                )

        elif section_key == "root_cause":

            if not root_cause:
                root_cause = clean_html(
                    content
                )

    for section in sections:

        if section.get("key") != "how_to_fix":
            continue

        content = section.get(
            "content",
            ""
        )

        context = section.get(
            "context",
            {}
        )

        context_key = context.get(
            "key",
            ""
        )

        if context_key == "flask":

            how_to_fix = clean_html(
                content
            )

            break

        if content and not how_to_fix:

            how_to_fix = clean_html(
                content
            )

    return {
        "introduction": introduction,
        "root_cause": root_cause,
        "how_to_fix": how_to_fix
    }


def main():

    params = {
        "projects": PROJECT_KEY,
        "resolved": "false",
        "ps": 100
    }

    response = sonar_get(
        "/api/issues/search",
        params=params
    )

    data = response.json()

    issues = data.get(
        "issues",
        []
    )

    print(
        f"Found {len(issues)} unresolved SonarQube issues."
    )

    for issue in issues:

        print(
            f"{issue.get('rule')} | "
            f"{issue.get('severity')} | "
            f"{issue.get('message')}"
        )


if __name__ == "__main__":
    main()
