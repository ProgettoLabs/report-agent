"""
Modular Agentic Pipeline Runner — File System Implementation

Reads the use-cases directory to discover use cases and pipeline steps, then
executes each step by calling an LLM with the step's spec, output format, and
all previous steps' outputs. All step outputs are recorded in context.json.

Usage:
    python agent.py <use_case_name>

Requires Ollama running locally with the target model pulled.
"""

import asyncio
import json
import sys
from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

USE_CASES_DIR = Path(__file__).parent.parent / "use-cases"


# ── data-access helpers (file system) ────────────────────────────────────────

async def fetch_resource(path: Path) -> str:
    return path.read_text() if path.exists() else ""


async def fetch_steps(use_case: str) -> list[str]:
    use_case_dir = USE_CASES_DIR / use_case
    return sorted(
        (d.name for d in use_case_dir.iterdir() if d.is_dir() and d.name.startswith("step_")),
        key=lambda name: int(name.split("_")[1]),
    )



# ── pipeline helpers ──────────────────────────────────────────────────────────

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


async def run_step(
    use_case: str,
    step_name: str,
    agent_task_description: str,
    input_data: str,
    previous_outputs: dict[str, str],
    context: dict,
    context_path: Path,
    llm: ChatOllama,
) -> str:
    print(f"[{step_name}] running ...")

    spec = await fetch_resource(USE_CASES_DIR / use_case / step_name / "spec.md")
    output_format = await fetch_resource(USE_CASES_DIR / use_case / step_name / "output.md")

    system_prompt = build_system_prompt(agent_task_description, spec, output_format)
    user_content = build_user_content(input_data, previous_outputs)

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
    return step_output


async def run_pipeline(use_case_input: str) -> str:
    llm = ChatOllama(model="gemma4:e4b", num_ctx=32768, temperature=0)

    agent_task_description = await fetch_resource(USE_CASES_DIR / use_case_input / "agent_task_description.md")
    input_data = await fetch_resource(USE_CASES_DIR / use_case_input / "input_data.md")
    steps = await fetch_steps(use_case_input)

    if not steps:
        print("No steps found.")
        return ""

    print(f"Use case: {use_case_input}")
    print(f"Steps:    {steps}\n")

    context: dict = {}
    context_path = USE_CASES_DIR / use_case_input / "context.json"
    previous_outputs: dict[str, str] = {}

    for step_name in steps:
        step_output = await run_step(
            use_case_input, step_name,
            agent_task_description, input_data,
            previous_outputs, context, context_path, llm,
        )
        previous_outputs[step_name] = step_output

    final_output = previous_outputs[steps[-1]]
    report_path = USE_CASES_DIR / use_case_input / "final_report.md"
    report_path.write_text(final_output)

    print(f"Pipeline complete. Results in context.json and {report_path}")
    return final_output


def main():
    if len(sys.argv) != 2:
        print("Usage: python agent.py <use_case_name>")
        sys.exit(1)

    asyncio.run(run_pipeline(sys.argv[1]))


if __name__ == "__main__":
    main()
