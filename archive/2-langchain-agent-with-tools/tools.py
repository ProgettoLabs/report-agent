import json
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from utils import PIPELINE_DIR


CONTEXT_PATH = str(PIPELINE_DIR / "context.json")
INPUT_DATA_PATH = str(PIPELINE_DIR / "input_data.md")


# ---------------------------------------------------------------------------
# Schema
#
# context.json layout — each step maps to a list of output entries:
#
# {
#   "step_01_data_structuring": [
#     {
#       "name": "revenue_by_product_line",
#       "output_type": "file",          # "text" or "file"
#       "content": "/abs/path/to.csv",  # path when file, raw text when text
#       "description": "..."
#     },
#     {
#       "name": "validation_notes",
#       "output_type": "text",
#       "content": "No discrepancies found.",
#       "description": "..."
#     }
#   ]
# }
# ---------------------------------------------------------------------------


@tool
def read_input_data() -> str:
    """Read the raw input data provided at the start of this pipeline run.

    Returns:
        The full contents of input_data.md, or an error message if the file is missing.
    """
    path = Path(INPUT_DATA_PATH)
    if not path.exists():
        return f"Error: input data file not found at {path}"
    return path.read_text()


@tool
def read_step_output(step_number: int) -> str:
    """Read all outputs produced by a completed pipeline step.

    Returns every named output for that step concatenated into a single block,
    with a header line identifying each output's name and type.

    Args:
        step_number: 1-based step number (e.g. 1 for the first step).

    Returns:
        All outputs for the step, or an error message if not found.
    """
    context_path = Path(CONTEXT_PATH)
    if not context_path.exists():
        return f"Error: context file not found at {context_path}"

    context = json.loads(context_path.read_text())

    step_key = next(
        (k for k in sorted(context.keys()) if k.startswith(f"step_{step_number:02d}_")),
        None,
    )
    if step_key is None:
        available = ", ".join(sorted(context.keys())) or "none"
        return f"Error: step {step_number} not found. Steps with outputs so far: {available}"

    outputs = context[step_key]
    if not outputs:
        return f"Step {step_key} has no outputs yet."

    sections = []
    for entry in outputs:
        name = entry["name"]
        output_type = entry.get("output_type", "text")
        header = f"### {name} ({output_type})"

        if output_type == "text":
            sections.append(f"{header}\n{entry['content']}")

        elif output_type == "file":
            file_path = Path(entry["content"])
            if not file_path.exists():
                sections.append(f"{header}\nError: file not found at {file_path}")
            elif file_path.suffix not in {".txt", ".csv", ".md"}:
                sections.append(f"{header}\nError: unsupported file type '{file_path.suffix}'")
            else:
                sections.append(f"{header}\n{file_path.read_text()}")

        else:
            sections.append(f"{header}\nError: unknown output_type '{output_type}'")

    return "\n\n".join(sections)


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
    output_name: str,
    content_type: str,
    content: str,
    filename: Optional[str] = None,
) -> str:
    """Append one named output to a pipeline step's output list in context.json.

    Call this once per output — multiple calls produce multiple outputs for the
    same step (e.g. one CSV per table).

    Args:
        step_number: 1-based step number (e.g. 1 for the first step).
        output_name: Label for this output (e.g. 'revenue_by_product_line').
        content_type: Either 'text' or 'file'.
        content: The content to store.  For 'text', stored directly.  For
            'file', written to disk and the path recorded in context.json.
        filename: Required when content_type is 'file'.  Filename to create
            inside the step directory (e.g. 'revenue.csv').
            Supported extensions: .txt, .csv, .md.

    Returns:
        A success message or an error string.
    """
    if not output_name:
        return "Error: output_name must not be empty."

    if content_type not in {"text", "file"}:
        return f"Error: unsupported content_type '{content_type}'. Use 'text' or 'file'."

    step_dir = _resolve_step_dir(step_number)
    if step_dir is None:
        return f"Error: no directory found for step {step_number} under {PIPELINE_DIR}"

    step_key = step_dir.name
    context_path = Path(CONTEXT_PATH)
    context = json.loads(context_path.read_text()) if context_path.exists() else {}

    if step_key not in context:
        context[step_key] = []

    if content_type == "text":
        entry = {
            "name": output_name,
            "output_type": "text",
            "content": content,
            "description": f"{output_name} output of {step_key}",
        }

    else:  # file
        if not filename:
            return "Error: 'filename' is required when content_type is 'file'."
        file_path = step_dir / filename
        if file_path.suffix not in {".txt", ".csv", ".md"}:
            return f"Error: unsupported file type '{file_path.suffix}'. Supported: .txt, .csv, .md"
        file_path.write_text(content)
        entry = {
            "name": output_name,
            "output_type": "file",
            "content": str(file_path),
            "description": f"{output_name} output of {step_key}",
        }

    context[step_key].append(entry)
    context_path.write_text(json.dumps(context, indent=2))
    return f"OK: '{output_name}' appended to {step_key}"
