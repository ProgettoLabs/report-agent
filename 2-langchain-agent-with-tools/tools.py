import json
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from utils import PIPELINE_DIR


CONTEXT_PATH = str(PIPELINE_DIR / "context.json")


@tool
def read_step_output(step_number: int) -> str:
    """Read the output of a specific pipeline step from context.json.

    Args:
        step_number: 1-based step number (e.g. 1 for the first step).

    Returns:
        The text content produced by that step, or an error message if not found.
    """
    resolved = Path(CONTEXT_PATH).resolve()

    if not resolved.exists():
        return f"Error: context file not found at {resolved}"

    context = json.loads(resolved.read_text())

    step_key = next(
        (k for k in sorted(context.keys()) if k.startswith(f"step_{step_number:02d}_")),
        None,
    )

    if step_key is None:
        available = ", ".join(sorted(context.keys()))
        return f"Error: step {step_number} not found. Available steps: {available}"

    step = context[step_key]
    output_type = step.get("output_type", "text")

    if output_type == "text":
        return step["content"]

    if output_type == "file":
        file_path = Path(step["content"])
        if file_path.suffix not in {".txt", ".csv", ".md"}:
            return f"Error: unsupported file type '{file_path.suffix}'. Supported: .txt, .csv, .md"
        if not file_path.exists():
            return f"Error: file not found at {file_path}"
        return file_path.read_text()

    return f"Error: unknown output_type '{output_type}'"


def _resolve_step_dir(step_number: int) -> Optional[Path]:
    """Return the step directory for the given 1-based step number, or None if not found."""
    prefix = f"step_{step_number:02d}_"
    return next(
        (d for d in sorted(PIPELINE_DIR.iterdir()) if d.is_dir() and d.name.startswith(prefix)),
        None,
    )


@tool
def write_step_output(
    step_number: int,
    content_type: str,
    content: str,
    filename: Optional[str] = None,
) -> str:
    """Write the output of a pipeline step to context.json.

    Args:
        step_number: 1-based step number (e.g. 1 for the first step).
        content_type: Either 'text' or 'file'.
        content: The full content to store (plain text, or file contents when type is 'file').
        filename: Required when content_type is 'file'. Name of the file to write inside
            the step directory (e.g. 'output.csv'). Supported extensions: .txt, .csv, .md.

    Returns:
        A success message or an error string.
    """
    if content_type not in {"text", "file"}:
        return f"Error: unsupported content_type '{content_type}'. Use 'text' or 'file'."

    step_dir = _resolve_step_dir(step_number)
    if step_dir is None:
        return f"Error: no directory found for step {step_number} under {PIPELINE_DIR}"

    step_key = step_dir.name
    context_path = Path(CONTEXT_PATH)
    context = json.loads(context_path.read_text()) if context_path.exists() else {}

    if content_type == "text":
        context[step_key] = {
            "output_type": "text",
            "content": content,
            "description": f"Output of {step_key}",
        }

    else:  # file
        if not filename:
            return "Error: 'filename' is required when content_type is 'file'."
        file_path = step_dir / filename
        if file_path.suffix not in {".txt", ".csv", ".md"}:
            return f"Error: unsupported file type '{file_path.suffix}'. Supported: .txt, .csv, .md"
        file_path.write_text(content)
        context[step_key] = {
            "output_type": "file",
            "content": str(file_path),
            "description": f"Output of {step_key}",
        }

    context_path.write_text(json.dumps(context, indent=2))
    return f"OK: step {step_key} written to context.json"
