import subprocess


DEFAULT_SOURCE_PATH = "app/app.py"
DEFAULT_BRANCH = "main"


def run_git_command(command):
    """
    Run a Git command and return its result.
    """

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def check_repository():
    """
    Verify that the current directory is a Git repository.
    """

    result = run_git_command(
        [
            "git",
            "rev-parse",
            "--is-inside-work-tree",
        ]
    )

    if result["returncode"] != 0:
        return {
            "success": False,
            "message": (
                "Current directory is not a Git repository."
            ),
            "details": result,
        }

    return {
        "success": True,
        "message": "Git repository verified.",
        "details": result,
    }


def check_file_changed(
    source_path=DEFAULT_SOURCE_PATH,
):
    """
    Check whether the specified source file has
    uncommitted changes.
    """

    result = run_git_command(
        [
            "git",
            "status",
            "--short",
            "--",
            source_path,
        ]
    )

    if result["returncode"] != 0:
        return {
            "success": False,
            "changed": False,
            "message": (
                "Unable to determine Git file status."
            ),
            "details": result,
        }

    changed = bool(result["stdout"])

    return {
        "success": True,
        "changed": changed,
        "message": (
            "Source file has uncommitted changes."
            if changed
            else "Source file has no uncommitted changes."
        ),
        "details": result,
    }


def stage_file(
    source_path=DEFAULT_SOURCE_PATH,
):
    """
    Stage the modified source file.
    """

    result = run_git_command(
        [
            "git",
            "add",
            "--",
            source_path,
        ]
    )

    if result["returncode"] != 0:
        return {
            "success": False,
            "message": "Git staging failed.",
            "details": result,
        }

    return {
        "success": True,
        "message": (
            f"Successfully staged {source_path}."
        ),
        "details": result,
    }


def create_commit(
    commit_message,
):
    """
    Create a Git commit for the staged changes.
    """

    if not commit_message:
        raise ValueError(
            "Commit message is required."
        )

    result = run_git_command(
        [
            "git",
            "commit",
            "-m",
            commit_message,
        ]
    )

    if result["returncode"] != 0:
        return {
            "success": False,
            "message": "Git commit failed.",
            "details": result,
        }

    return {
        "success": True,
        "message": "Git commit created successfully.",
        "details": result,
    }


def push_changes(
    branch=DEFAULT_BRANCH,
):
    """
    Push the current branch to origin.
    """

    result = run_git_command(
        [
            "git",
            "push",
            "origin",
            branch,
        ]
    )

    if result["returncode"] != 0:
        return {
            "success": False,
            "message": (
                f"Git push failed for branch {branch}."
            ),
            "details": result,
        }

    return {
        "success": True,
        "message": (
            f"Changes pushed successfully to "
            f"origin/{branch}."
        ),
        "details": result,
    }


def commit_and_push(
    source_path=DEFAULT_SOURCE_PATH,
    commit_message=None,
    branch=DEFAULT_BRANCH,
):
    """
    Commit and push an automatically remediated source file.

    The function performs:

        1. Git repository validation
        2. Source-file change detection
        3. Git staging
        4. Git commit
        5. Git push

    The function does not modify source code.
    """

    if commit_message is None:
        commit_message = (
            "Apply AI security remediation"
        )

    print("\n" + "=" * 60)
    print(" GIT AUTOMATION")
    print("=" * 60)

    print("\n[1] Checking Git repository...")

    repository = check_repository()

    if not repository["success"]:
        print(
            "Git repository check: FAIL"
        )
        print(
            repository["message"]
        )
        return {
            "success": False,
            "stage": "repository",
            "message": repository["message"],
        }

    print(
        "Git repository check: PASS"
    )

    print("\n[2] Checking source-file changes...")

    file_status = check_file_changed(
        source_path
    )

    if not file_status["success"]:
        print(
            "Source-file status check: FAIL"
        )
        print(
            file_status["message"]
        )
        return {
            "success": False,
            "stage": "status",
            "message": file_status["message"],
        }

    if not file_status["changed"]:
        print(
            "Source-file status check: FAIL"
        )
        print(
            "No uncommitted changes detected."
        )
        return {
            "success": False,
            "stage": "status",
            "message": (
                "No uncommitted changes were detected "
                f"for {source_path}."
            ),
        }

    print(
        "Source-file status check: PASS"
    )

    print("\n[3] Staging source file...")

    staging = stage_file(
        source_path
    )

    if not staging["success"]:
        print(
            "Git staging: FAIL"
        )
        print(
            staging["message"]
        )
        return {
            "success": False,
            "stage": "staging",
            "message": staging["message"],
        }

    print(
        "Git staging: PASS"
    )

    print("\n[4] Creating commit...")

    commit = create_commit(
        commit_message
    )

    if not commit["success"]:
        print(
            "Git commit: FAIL"
        )
        print(
            commit["message"]
        )
        return {
            "success": False,
            "stage": "commit",
            "message": commit["message"],
        }

    print(
        "Git commit: PASS"
    )

    print(
        commit["details"]["stdout"]
    )

    print("\n[5] Pushing to GitHub...")

    push = push_changes(
        branch
    )

    if not push["success"]:
        print(
            "Git push: FAIL"
        )
        print(
            push["message"]
        )
        return {
            "success": False,
            "stage": "push",
            "message": push["message"],
        }

    print(
        "Git push: PASS"
    )

    print(
        push["message"]
    )

    print("\n" + "=" * 60)
    print(" GIT AUTOMATION COMPLETED")
    print("=" * 60)

    return {
        "success": True,
        "stage": "completed",
        "source_path": source_path,
        "commit_message": commit_message,
        "branch": branch,
        "message": (
            "Source-file changes were committed "
            "and pushed successfully."
        ),
    }


if __name__ == "__main__":
    print(
        "git_manager.py loaded successfully."
    )
