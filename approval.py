
from pathlib import Path
import logging
import shutil

from config import BASE_DIR

logger = logging.getLogger(__name__)

PENDING_DIR = BASE_DIR / "runtime" / "pending"
PENDING_DIR.mkdir(parents=True, exist_ok=True)


def save_pending_code(
    filename: str,
    source_code: str,
) -> Path:
    """Save generated code without activating it."""

    if Path(filename).name != filename:
        raise ValueError("Only a filename is allowed")

    if not filename.endswith(".py"):
        raise ValueError("Generated files must end in .py")

    pending_path = PENDING_DIR / filename
    pending_path.write_text(
        source_code,
        encoding="utf-8",
    )

    logging.getLogger("agent_activity").info(
        "event=code_saved_pending filename=%s",
        filename,
    )

    return pending_path


def approve_and_activate(
    pending_path: Path,
    destination_path: Path,
) -> Path:
    """Activate reviewed code after basic syntax validation."""

    pending_path = pending_path.resolve()
    destination_path = destination_path.resolve()

    if not pending_path.is_relative_to(PENDING_DIR.resolve()):
        raise ValueError("Pending file is outside the pending directory")

    # Only approved project directories may receive generated files.
    allowed_roots = [
        (BASE_DIR / "agents").resolve(),
        (BASE_DIR / "generated_tools").resolve(),
    ]

    if not any(
        destination_path.is_relative_to(root)
        for root in allowed_roots
    ):
        raise ValueError("Destination directory is not allowed")

    if not pending_path.is_file():
        raise FileNotFoundError(pending_path)

    # Syntax validation does NOT prove that code is safe.
    source = pending_path.read_text(encoding="utf-8")
    compile(source, str(pending_path), "exec")

    destination_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Preserve an existing version for rollback.
    if destination_path.exists():
        backup_path = destination_path.with_suffix(
            destination_path.suffix + ".bak"
        )
        shutil.copy2(destination_path, backup_path)

    shutil.copy2(pending_path, destination_path)

    logging.getLogger("agent_activity").info(
        "event=code_activated destination=%s",
        destination_path.name,
    )

    return destination_path
