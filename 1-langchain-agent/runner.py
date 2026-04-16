"""
Modular Agentic Pipeline Runner — LangChain Implementation

Reads a pipeline directory, discovers steps in order, and executes each
one by calling an LLM with the step's spec, output format, and the
previous step's output. All outputs are recorded in context.json.

Usage:
    python runner.py <pipeline_directory>

Requires Ollama running locally with the target model pulled.
"""

import json
import sys
from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage


def discover_steps(pipeline_dir: Path) -> list[Path]:
    """Find all step_* directories, sorted by name."""
    return sorted(
        d for d in pipeline_dir.iterdir()
        if d.is_dir() and d.name.startswith("step_")
    )


def read_file(path: Path) -> str:
    """Read a file and return its contents, or empty string if missing."""
    return path.read_text() if path.exists() else ""


def run_pipeline(pipeline_dir: str) -> str:
    """Execute the full pipeline and return the final step's output."""
    root = Path(pipeline_dir).resolve()

    pipeline_md = read_file(root / "pipeline.md")
    input_data = read_file(root / "input_data.md")

    steps = discover_steps(root)
    if not steps:
        print("No step directories found.")
        return ""

    print(f"Pipeline: {root.name}")
    print(f"Steps:    {[s.name for s in steps]}\n")

    context: dict = {}
    context_path = root / "context.json"
    llm = ChatOllama(model="gemma4:31b", num_ctx=8192)

    previous_output: str | None = None

    for step_dir in steps:
        step_name = step_dir.name
        print(f"[{step_name}] running ...")

        spec = read_file(step_dir / "spec.md")
        output_format = read_file(step_dir / "output.md")

        system_prompt = (
            "You are an AI assistant executing one step of a multi-step pipeline.\n\n"
            "## Pipeline Overview\n"
            f"{pipeline_md}\n\n"
            "## Your Task\n"
            f"{spec}\n\n"
            "## Required Output Format\n"
            f"{output_format}\n\n"
            "Produce ONLY the output described in the required output format. "
            "Do not include any preamble, commentary, or explanation outside "
            "the specified format."
        )

        if previous_output is None:
            user_content = (
                "Here is the raw input data for this pipeline run:\n\n"
                f"{input_data}\n\n"
                "Execute this step and produce the output in the specified format."
            )
        else:
            user_content = (
                "Here is the output from the previous step:\n\n"
                f"{previous_output}\n\n"
                "Execute this step and produce the output in the specified format."
            )

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ])
        step_output = response.content

        context[step_name] = {
            "output_type": "text",
            "content": step_output,
            "description": f"Output of {step_name}",
        }
        context_path.write_text(json.dumps(context, indent=2))

        print(f"[{step_name}] done ({len(step_output)} chars)\n")
        previous_output = step_output

    print("Pipeline complete. Results in context.json")
    return previous_output


def main():
    if len(sys.argv) != 2:
        print("Usage: python runner.py <pipeline_directory>")
        sys.exit(1)

    pipeline_dir = sys.argv[1]
    if not Path(pipeline_dir).is_dir():
        print(f"Error: {pipeline_dir} is not a directory")
        sys.exit(1)

    final_output = run_pipeline(pipeline_dir)
    if final_output:
        print("\n=== FINAL REPORT ===\n")
        print(final_output)


if __name__ == "__main__":
    main()
