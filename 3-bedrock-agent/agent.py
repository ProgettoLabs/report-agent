"""
Modular Agentic Pipeline Runner — Amazon Bedrock Implementation

Reads a pipeline directory, discovers steps in order, and executes each
one by calling an LLM with the step's spec, output format, and the
previous step's output. All outputs are recorded in context.json.

Usage:
    python agent.py <pipeline_directory>

Requires AWS credentials configured and Bedrock model access enabled.
"""

import json
import sys
from pathlib import Path

import boto3


def discover_steps(pipeline_dir: Path) -> list[Path]:
    """Find all step_* directories, sorted by name."""
    return sorted(
        d for d in pipeline_dir.iterdir()
        if d.is_dir() and d.name.startswith("step_")
    )


def read_file(path: Path) -> str:
    """Read a file and return its contents, or empty string if missing."""
    return path.read_text() if path.exists() else ""


def build_system_prompt(agent_task_description: str, spec: str, output_format: str) -> str:
    return (
        "You are an AI assistant executing one step of a multi-step task.\n\n"
        "## Task Overview\n"
        f"{agent_task_description}\n\n"
        "## Your Task\n"
        f"{spec}\n\n"
        "## Required Output Format\n"
        f"{output_format}\n\n"
        "Produce ONLY the output described in the required output format. "
        "Do not include any preamble, commentary, or explanation outside "
        "the specified format."
    )


def format_prior_outputs(previous_outputs: dict[str, str]) -> str:
    if not previous_outputs:
        return ""

    sections = "\n\n---\n\n".join(
        f"### {name}\n\n{content}"
        for name, content in previous_outputs.items()
    )
    return f"Here are the outputs from all previous steps:\n\n{sections}\n\n"


def build_user_content(input_data: str, previous_outputs: dict[str, str]) -> str:
    prior_steps_text = format_prior_outputs(previous_outputs)
    return (
        "Here is the raw input data for this pipeline run:\n\n"
        f"{input_data}\n\n"
        f"{prior_steps_text}"
        "Execute this step and produce the output in the specified format."
    )


def save_context(context_path: Path, context: dict) -> None:
    context_path.write_text(json.dumps(context, indent=2))


def save_final_report(root: Path, content: str) -> Path:
    report_path = root / "final_report.md"
    report_path.write_text(content)
    return report_path


def run_step(
    step_dir: Path,
    agent_task_description: str,
    input_data: str,
    previous_outputs: dict[str, str],
    context: dict,
    context_path: Path,
    client,
    model_id: str,
) -> str:
    """Execute a single pipeline step, persist its output to context, and return the output."""
    step_name = step_dir.name
    print(f"[{step_name}] running ...")

    spec = read_file(step_dir / "spec.md")
    output_format = read_file(step_dir / "output.md")

    system_prompt = build_system_prompt(agent_task_description, spec, output_format)
    user_content = build_user_content(input_data, previous_outputs)

    response = client.converse(
        modelId=model_id,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_content}]}],
        inferenceConfig={"temperature": 0, "maxTokens": 8192},
    )
    step_output = response["output"]["message"]["content"][0]["text"]

    context[step_name] = {
        "output_type": "text",
        "content": step_output,
        "description": f"Output of {step_name}",
    }
    save_context(context_path, context)

    print(f"[{step_name}] done ({len(step_output)} chars)\n")
    return step_output


def run_pipeline(pipeline_dir: str) -> str:
    """Execute the full pipeline and return the final step's output."""
    root = Path(pipeline_dir).resolve()

    agent_task_description = read_file(root / "agent_task_description.md")
    input_data = read_file(root / "input_data.md")

    steps = discover_steps(root)
    if not steps:
        print("No step directories found.")
        return ""

    print(f"Pipeline: {root.name}")
    print(f"Steps:    {[s.name for s in steps]}\n")

    context: dict = {}
    context_path = root / "context.json"
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    model_id = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

    previous_outputs: dict[str, str] = {}

    for step_dir in steps:
        step_output = run_step(
            step_dir, agent_task_description, input_data, previous_outputs, context, context_path, client, model_id
        )
        previous_outputs[step_dir.name] = step_output

    final_output = previous_outputs[steps[-1].name]
    report_path = save_final_report(root, final_output)

    print(f"Pipeline complete. Results in context.json and {report_path}")
    return final_output


def main():
    if len(sys.argv) != 2:
        print("Usage: python agent.py <pipeline_directory>")
        sys.exit(1)

    pipeline_dir = sys.argv[1]
    if not Path(pipeline_dir).is_dir():
        print(f"Error: {pipeline_dir} is not a directory")
        sys.exit(1)

    final_output = run_pipeline(pipeline_dir)
    if final_output:
        print(f"Final report saved to final_report.md")


if __name__ == "__main__":
    main()
