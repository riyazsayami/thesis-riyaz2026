import os
import re
import time

import ollama
import requests


MODEL = "qwen2.5-coder:3b"
OLLAMA_HOST = "http://127.0.0.1:11434"

SONAR_HOST_URL = os.getenv(
    "SONAR_HOST_URL",
    "http://localhost:9000",
).rstrip("/")

SONAR_TOKEN = os.getenv("SONAR_TOKEN", "")
PROJECT_KEY = "thesis-riyaz2026"

client = ollama.Client(
    host=OLLAMA_HOST,
    timeout=300,
)


SUPPORTED_RULES = {
    "python:S4502": {
        "title": "CSRF protection is disabled",
        "solution": "Enable CSRF protection in the Flask application.",
        "how_to_fix": (
            "Use Flask-WTF CSRFProtect and initialize it with the Flask "
            "application. Do not disable CSRF protection."
        ),
    },
    "python:S4507": {
        "title": "Debug mode is enabled",
        "solution": "Disable Flask debug mode before running the application.",
        "how_to_fix": (
            "Replace debug=True with debug=False or remove the debug "
            "option from the production application startup."
        ),
    },
    "python:S8392": {
        "title": "Application binds to all network interfaces",
        "solution": (
            "Bind the Flask application to a specific trusted interface."
        ),
        "how_to_fix": (
            "Replace host='0.0.0.0' with host='127.0.0.1' unless external "
            "network access is explicitly required."
        ),
    },
    "docker:S6470": {
        "title": "Docker COPY instruction may copy sensitive files",
        "solution": (
            "Copy only the files required to build the Docker image."
        ),
        "how_to_fix": (
            "Avoid broad recursive COPY instructions such as COPY . . "
            "and use explicit COPY instructions together with .dockerignore."
        ),
    },
    "python:S6965": {
        "title": "HTTP route should explicitly define the HTTP method",
        "solution": (
            "Explicitly define the HTTP methods accepted by the route."
        ),
        "how_to_fix": (
            "Use Flask's methods parameter, for example "
            "methods=['GET'] or methods=['POST']."
        ),
    },
}


def clean_html(value):
    if not value:
        return ""

    value = re.sub(r"<[^>]+>", " ", str(value))
    value = value.replace("&quot;", '"')
    value = value.replace("&lt;", "<")
    value = value.replace("&gt;", ">")
    value = value.replace("&amp;", "&")
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def sonar_request(endpoint, params=None):
    if not SONAR_TOKEN:
        raise RuntimeError("SONAR_TOKEN is not set.")

    url = f"{SONAR_HOST_URL}{endpoint}"

    response = requests.get(
        url,
        params=params or {},
        auth=(SONAR_TOKEN, ""),
        timeout=20,
    )

    response.raise_for_status()

    return response.json()


def get_issue_by_rule(rule_key):
    data = sonar_request(
        "/api/issues/search",
        {
            "componentKeys": PROJECT_KEY,
            "resolved": "false",
            "rules": rule_key,
            "ps": 10,
        },
    )

    issues = data.get("issues", [])

    if not issues:
        raise RuntimeError(
            f"No unresolved SonarQube issue found for rule {rule_key}."
        )

    return issues[0]


def get_rule_details(rule_key):
    data = sonar_request(
        "/api/rules/show",
        {
            "key": rule_key,
        },
    )

    return data.get("rule", {})


def get_sonar_remediation(rule_details):
    remediation = (
        rule_details.get("remediation")
        or rule_details.get("remediationDescription")
        or rule_details.get("gapDescription")
        or rule_details.get("defaultRemFn")
        or ""
    )

    return clean_html(remediation)


def get_remediation_information(rule_key):
    if isinstance(rule_key, dict):
        possible_rule_key = (
            rule_key.get("key")
            or rule_key.get("rule")
        )

        if possible_rule_key:
            rule_key = possible_rule_key

    issue = get_issue_by_rule(rule_key)
    rule = get_rule_details(rule_key)

    remediation = get_sonar_remediation(rule)

    if not remediation:
        remediation = (
            SUPPORTED_RULES.get(rule_key, {}).get("how_to_fix")
            or "No remediation guidance was returned by SonarQube."
        )

    return {
        "issue": issue,
        "rule": rule,
        "remediation": remediation,
    }


def read_source_code(source_path):
    if not source_path:
        return ""

    if not os.path.exists(source_path):
        raise FileNotFoundError(
            f"Source file does not exist: {source_path}"
        )

    with open(
        source_path,
        "r",
        encoding="utf-8",
    ) as file:
        return file.read()


def build_prompt(
    rule_key,
    issue,
    rule_details,
    remediation,
    source_code,
):
    rule_info = SUPPORTED_RULES.get(
        rule_key,
        {},
    )

    issue_message = issue.get(
        "message",
        "",
    )

    issue_component = issue.get(
        "component",
        "",
    )

    issue_line = issue.get(
        "line",
        "",
    )

    if not issue_line:
        text_range = issue.get(
            "textRange",
            {},
        )

        issue_line = text_range.get(
            "startLine",
            "",
        )

    rule_name = rule_details.get(
        "name",
        rule_info.get(
            "title",
            rule_key,
        ),
    )

    rule_description = clean_html(
        rule_details.get("htmlDesc")
        or rule_details.get("description")
        or ""
    )

    prompt = f"""
You are a secure-code remediation AI agent.

Your job is to analyze a SonarQube security finding and propose an
actual source-code remediation.

SONARQUBE RULE:
{rule_key}

RULE NAME:
{rule_name}

SONARQUBE ISSUE:
{issue_message}

COMPONENT:
{issue_component}

LINE:
{issue_line}

SONARQUBE RULE DESCRIPTION:
{rule_description}

SONARQUBE REMEDIATION GUIDANCE:
{remediation}

SOURCE CODE:
{source_code}

TASK:

1. Identify the security vulnerability.
2. Explain why the existing code is insecure.
3. Use the SonarQube remediation guidance.
4. Propose a concrete code fix.
5. Modify the source code to apply the security fix.
6. Preserve the application's existing functionality.
7. Do not make unrelated changes.
8. Return the complete corrected source code.

For the security improvement section, explain what security protection
is added or improved by the proposed fix.

Return the response using exactly these four sections:

EXPLANATION:
<short explanation of the vulnerability and why the existing code is insecure>

PROPOSED FIX:
<short description of the exact code change>

SECURITY IMPROVEMENT:
<short explanation of how the change improves security>

CORRECTED CODE:
<complete corrected source code without omitting unchanged code>
"""

    return prompt


def extract_section(response, section_name, next_sections=None):
    if not response:
        return ""

    if next_sections is None:
        next_sections = []

    escaped_name = re.escape(section_name)

    if next_sections:
        next_pattern = "|".join(
            re.escape(section)
            for section in next_sections
        )

        pattern = (
            rf"{escaped_name}\s*:\s*(.*?)"
            rf"(?=\n(?:{next_pattern})\s*:|\Z)"
        )
    else:
        pattern = (
            rf"{escaped_name}\s*:\s*(.*)"
        )

    match = re.search(
        pattern,
        response,
        re.DOTALL | re.IGNORECASE,
    )

    if not match:
        return ""

    return match.group(1).strip()


def extract_corrected_code(response):
    if not response:
        return ""

    corrected_code = extract_section(
        response,
        "CORRECTED CODE",
    )

    if not corrected_code:
        match = re.search(
            r"```(?:python|dockerfile|text)?\s*(.*?)```",
            response,
            re.DOTALL | re.IGNORECASE,
        )

        if match:
            corrected_code = match.group(1).strip()

    if not corrected_code:
        return ""

    corrected_code = corrected_code.strip()

    if corrected_code.startswith("```"):
        corrected_code = re.sub(
            r"^```[a-zA-Z0-9_-]*\s*",
            "",
            corrected_code,
        )

    if corrected_code.endswith("```"):
        corrected_code = re.sub(
            r"\s*```$",
            "",
            corrected_code,
        )

    return corrected_code.strip()


def parse_ai_response(response):
    return {
        "explanation": extract_section(
            response,
            "EXPLANATION",
            [
                "PROPOSED FIX",
                "SECURITY IMPROVEMENT",
                "CORRECTED CODE",
            ],
        ),
        "proposed_fix": extract_section(
            response,
            "PROPOSED FIX",
            [
                "SECURITY IMPROVEMENT",
                "CORRECTED CODE",
            ],
        ),
        "security_improvement": extract_section(
            response,
            "SECURITY IMPROVEMENT",
            [
                "CORRECTED CODE",
            ],
        ),
        "corrected_code": extract_corrected_code(
            response
        ),
    }


def check_ollama():
    try:
        response = requests.get(
            f"{OLLAMA_HOST}/api/tags",
            timeout=10,
        )

        response.raise_for_status()

        models = response.json().get(
            "models",
            [],
        )

        model_names = [
            model.get("name", "")
            for model in models
        ]

        if MODEL not in model_names:
            raise RuntimeError(
                f"Ollama model '{MODEL}' is not available. "
                f"Available models: {model_names}"
            )

        return True

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not connect to Ollama at "
            f"{OLLAMA_HOST}: {exc}"
        ) from exc


def call_ollama(prompt):
    check_ollama()

    last_error = None

    for attempt in range(1, 4):
        try:
            print(
                f"\nOllama attempt {attempt}/3 "
                f"using {MODEL}..."
            )

            response = client.chat(
                model=MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                options={
                    "temperature": 0.1,
                    "num_ctx": 2048,
                    "num_predict": 2048,
                },
            )

            content = response.get(
                "message",
                {},
            ).get(
                "content",
                "",
            )

            if not content.strip():
                raise RuntimeError(
                    "Ollama returned an empty response."
                )

            print(
                "Ollama response received successfully."
            )

            return content

        except Exception as exc:
            last_error = exc

            print(
                f"Ollama attempt {attempt}/3 failed: {exc}"
            )

            if attempt < 3:
                time.sleep(3)

    raise RuntimeError(
        "Ollama failed after 3 attempts. "
        f"Last error: {last_error}"
    ) from last_error


def validate_remediation(
    rule_key,
    original_code,
    corrected_code,
):
    result = {
        "passed": False,
        "checks": [],
        "message": "",
    }

    if not corrected_code.strip():
        result["checks"].append(
            "Corrected code generated: FAIL"
        )
        result["message"] = (
            "The AI did not return corrected source code."
        )
        return result

    result["checks"].append(
        "Corrected code generated: PASS"
    )

    if rule_key == "python:S4502":
        original_lower = original_code.lower()
        corrected_lower = corrected_code.lower()

        csrf_protection = (
            "csrfprotect" in corrected_lower
            or "csrf_protect" in corrected_lower
            or "csrf_protection" in corrected_lower
        )

        csrf_disabled = (
            "csrf_enabled = false" in corrected_lower
            or "csrf_enabled=False".lower() in corrected_lower
            or "wtf_csrf_enabled = false" in corrected_lower
            or "wtf_csrf_enabled=False".lower() in corrected_lower
            or "csrf_enabled=false" in corrected_lower
            or "wtf_csrf_enabled=false" in corrected_lower
        )

        if csrf_protection:
            result["checks"].append(
                "CSRF protection mechanism detected: PASS"
            )
        else:
            result["checks"].append(
                "CSRF protection mechanism detected: FAIL"
            )

        if csrf_disabled:
            result["checks"].append(
                "CSRF remains explicitly disabled: FAIL"
            )
        else:
            result["checks"].append(
                "CSRF is not explicitly disabled: PASS"
            )

        original_disabled = (
            "csrf_enabled = false" in original_lower
            or "csrf_enabled=false" in original_lower
            or "wtf_csrf_enabled = false" in original_lower
            or "wtf_csrf_enabled=false" in original_lower
        )

        if original_disabled and not csrf_disabled:
            result["checks"].append(
                "Original insecure configuration removed: PASS"
            )
        else:
            result["checks"].append(
                "Original insecure configuration removed: FAIL"
            )

        result["passed"] = (
            bool(csrf_protection)
            and not csrf_disabled
            and not (
                original_disabled
                and csrf_disabled
            )
        )

        if result["passed"]:
            result["message"] = (
                "The corrected code contains a CSRF protection "
                "mechanism and does not explicitly disable CSRF."
            )
        else:
            result["message"] = (
                "The corrected code did not satisfy the "
                "automated S4502 security checks."
            )

        return result

    if rule_key == "python:S4507":
        corrected_lower = corrected_code.lower()

        debug_true = (
            "debug=true" in corrected_lower
            or "debug = true" in corrected_lower
        )

        debug_false = (
            "debug=false" in corrected_lower
            or "debug = false" in corrected_lower
        )

        debug_removed_from_run = (
            "app.run(" in corrected_lower
            and "debug=" not in corrected_lower
        )

        debug_disabled = (
            not debug_true
            and (
                debug_false
                or debug_removed_from_run
            )
        )

        if debug_disabled:
            result["checks"].append(
                "Debug mode disabled: PASS"
            )
        else:
            result["checks"].append(
                "Debug mode disabled: FAIL"
            )

        result["passed"] = debug_disabled

        result["message"] = (
            "Debug mode is disabled or the debug option "
            "has been removed."
            if debug_disabled
            else "Debug mode still appears to be enabled."
        )

        return result

    if rule_key == "python:S8392":
        corrected_lower = corrected_code.lower()

        insecure_host = (
            'host="0.0.0.0"' in corrected_lower
            or "host='0.0.0.0'" in corrected_lower
        )

        if insecure_host:
            result["checks"].append(
                "Binding to 0.0.0.0 removed: FAIL"
            )
        else:
            result["checks"].append(
                "Binding to 0.0.0.0 removed: PASS"
            )

        result["passed"] = not insecure_host

        result["message"] = (
            "The all-interface binding was removed."
            if result["passed"]
            else "The all-interface binding remains."
        )

        return result

    if rule_key == "docker:S6470":
        corrected_upper = corrected_code.upper()

        broad_copy = (
            "COPY . ." in corrected_upper
            or "COPY . /" in corrected_upper
        )

        if broad_copy:
            result["checks"].append(
                "Broad recursive COPY removed: FAIL"
            )
        else:
            result["checks"].append(
                "Broad recursive COPY removed: PASS"
            )

        result["passed"] = not broad_copy

        result["message"] = (
            "The broad Docker COPY instruction was removed."
            if result["passed"]
            else "A broad Docker COPY instruction remains."
        )

        return result

    if rule_key == "python:S6965":
        corrected_lower = corrected_code.lower()

        methods_present = (
            "methods=" in corrected_lower
        )

        if methods_present:
            result["checks"].append(
                "Explicit HTTP methods detected: PASS"
            )
        else:
            result["checks"].append(
                "Explicit HTTP methods detected: FAIL"
            )

        result["passed"] = methods_present

        result["message"] = (
            "The route explicitly defines HTTP methods."
            if result["passed"]
            else "No explicit HTTP method definition was detected."
        )

        return result

    result["checks"].append(
        "Generic corrected-code validation: PASS"
    )

    result["passed"] = True
    result["message"] = (
        "Corrected code was generated successfully."
    )

    return result
def apply_remediation(
    source_path,
    corrected_code,
    create_backup=True,
):
    if not source_path:
        raise ValueError(
            "Source path is required."
        )

    if not corrected_code.strip():
        raise ValueError(
            "Corrected code is empty."
        )

    if not os.path.exists(source_path):
        raise FileNotFoundError(
            f"Source file does not exist: {source_path}"
        )

    backup_path = None

    if create_backup:
        backup_path = f"{source_path}.backup"

        with open(
            source_path,
            "r",
            encoding="utf-8",
        ) as source_file:
            original_code = source_file.read()

        with open(
            backup_path,
            "w",
            encoding="utf-8",
        ) as backup_file:
            backup_file.write(original_code)

    with open(
        source_path,
        "w",
        encoding="utf-8",
    ) as source_file:
        source_file.write(
            corrected_code.rstrip() + "\n"
        )

    return {
        "success": True,
        "source_path": source_path,
        "backup_path": backup_path,
    }

def analyze_finding(
    issue,
    remediation,
    source_path=None,
    source_code=None,
):
    if not issue:
        raise ValueError(
            "SonarQube issue is required."
        )

    rule_key = issue.get(
        "rule",
        "",
    )

    if not rule_key:
        raise ValueError(
            "SonarQube issue does not contain a rule key."
        )

    if source_code is None:
        if source_path is None:
            raise RuntimeError(
                "Either source_code or source_path "
                "must be provided."
            )

        source_code = read_source_code(
            source_path
        )

    if not source_code.strip():
        raise RuntimeError(
            "No source code was provided "
            "for AI remediation."
        )

    rule_details = get_rule_details(
        rule_key
    )

    if isinstance(remediation, dict):
        remediation_text = (
            remediation.get("remediation")
            or remediation.get("how_to_fix")
            or remediation.get("description")
            or remediation.get("solution")
            or ""
        )
    else:
        remediation_text = str(
            remediation or ""
        )

    if not remediation_text:
        remediation_text = (
            SUPPORTED_RULES.get(
                rule_key,
                {},
            ).get(
                "how_to_fix"
            )
            or "No remediation guidance was provided."
        )

    prompt = build_prompt(
        rule_key=rule_key,
        issue=issue,
        rule_details=rule_details,
        remediation=remediation_text,
        source_code=source_code,
    )

    ai_response = call_ollama(
        prompt
    )

    parsed_response = parse_ai_response(
        ai_response
    )

    corrected_code = parsed_response[
        "corrected_code"
    ]

    validation = validate_remediation(
        rule_key=rule_key,
        original_code=source_code,
        corrected_code=corrected_code,
    )

    return {
        "rule_key": rule_key,
        "issue": issue,
        "rule": rule_details,
        "remediation": remediation_text,
        "prompt": prompt,
        "ai_response": ai_response,
        "explanation": parsed_response[
            "explanation"
        ],
        "proposed_fix": parsed_response[
            "proposed_fix"
        ],
        "security_improvement": parsed_response[
            "security_improvement"
        ],
        "corrected_code": corrected_code,
        "source_code": source_code,
        "validation": validation,
    }
