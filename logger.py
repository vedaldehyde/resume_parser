from datetime import datetime


def get_timestamp() -> str:
    """Returns the current date, day name, and time.

    Example: '2026-10-14 | Wednesday | 11:35:50'
    """
    return datetime.now().strftime("%Y-%m-%d | %A | %H:%M:%S")


def log(message: str = "", end: str = "\n", flush: bool = True) -> None:
    """Prints a message prefixed with the current date, day, and time.

    Example output:
    [2026-10-14 | Wednesday | 11:35:50] Processing: resume.pdf...
    """
    if not message:
        print("", end=end, flush=flush)
        return

    timestamp = get_timestamp()
    prefix = f"[{timestamp}]"

    # Preserve leading/trailing newlines if present
    leading_newlines = len(message) - len(message.lstrip("\n"))
    trailing_newlines = len(message) - len(message.rstrip("\n"))
    clean_message = message.strip("\n")

    if leading_newlines > 0:
        print("\n" * (leading_newlines - 1))

    for line in clean_message.split("\n"):
        if line.strip():
            print(f"{prefix} {line}", flush=flush)
        else:
            print("", flush=flush)

    if trailing_newlines > 0:
        print("\n" * (trailing_newlines - 1), end="")

