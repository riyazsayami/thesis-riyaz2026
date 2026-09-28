import os
import shutil
import subprocess
import tempfile


def create_backup(source_path):
    """
    Create a backup of the source file before modification.
    """

    backup_path = source_path + ".auto_backup"

    shutil.copy2(
        source_path,
        backup_path
    )

    return backup_path


def restore_backup(source_path, backup_path):
    """
    Restore the original source file from backup.
    """

    shutil.copy2(
        backup_path,
        source_path
    )


def validate_python_syntax(source_path):
    """
    Validate Python syntax without executing the application.
    """

    if not source_path.endswith(".py"):
        return True, "Syntax validation skipped for non-Python file."

    result = subprocess.run(
        [
            "python3",
            "-m",
            "py_compile",
            source_path
        ],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return True, "Python syntax validation passed."

    error = result.stderr.strip()

    return False, error


def replace_code(
    source_path,
    old_code,
    new_code
):
    """
    Safely replace an exact section of source code.

    The replacement is performed only when old_code
    exists exactly once in the file.
    """

    if not os.path.exists(source_path):
        return False, "Source file does not exist."

    if not old_code:
        return False, "Old code is empty."

    if not new_code:
        return False, "New code is empty."

    with open(
        source_path,
        "r",
        encoding="utf-8"
    ) as file:

        original_content = file.read()

    occurrence_count = original_content.count(
        old_code
    )

    if occurrence_count == 0:
        return (
            False,
            "The expected original code was not found."
        )

    if occurrence_count > 1:
        return (
            False,
            "The expected original code appears "
            "multiple times. Modification stopped."
        )

    backup_path = create_backup(
        source_path
    )

    modified_content = original_content.replace(
        old_code,
        new_code,
        1
    )

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=os.path.dirname(source_path),
            delete=False
        ) as temp_file:

            temp_file.write(
                modified_content
            )

            temp_path = temp_file.name

        os.replace(
            temp_path,
            source_path
        )

        valid, message = validate_python_syntax(
            source_path
        )

        if not valid:

            restore_backup(
                source_path,
                backup_path
            )

            return (
                False,
                "Modification failed syntax validation. "
                "Original file restored.\n"
                + message
            )

        return (
            True,
            "Code modification applied successfully.\n"
            + message
        )

    except Exception as error:

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        restore_backup(
            source_path,
            backup_path
        )

        return (
            False,
            "Modification failed. "
            "Original file restored.\n"
            + str(error)
        )


def modify_file(
    source_path,
    old_code,
    new_code
):
    """
    Main entry point for automatic source-code modification.
    """

    print("\n" + "=" * 60)
    print(" AUTOMATIC CODE MODIFICATION")
    print("=" * 60)

    print(
        f"File : {source_path}"
    )

    print(
        "\nCreating safety backup..."
    )

    success, message = replace_code(
        source_path,
        old_code,
        new_code
    )

    if success:

        print(
            "\nSTATUS: SUCCESS"
        )

        print(
            message
        )

    else:

        print(
            "\nSTATUS: FAILED"
        )

        print(
            message
        )

    print("=" * 60)

    return success, message


if __name__ == "__main__":

    print(
        "code_modifier.py loaded successfully."
    )
