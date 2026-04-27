"""
Modular Agentic Pipeline Runner - Local or MCP Implementation

Runs a use-case pipeline either directly from the local file system or through
the report-agent MCP server. Accepts a potentially misspelled use case name and
uses an LLM to resolve it before running. All step outputs are recorded in
context.json.

Usage:
    python agent.py <use_case_name>

Requires Ollama running locally with the target model pulled.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import Client
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from mcp_server import mcp

AGENT_TYPE = "local"  # either "local" or "mcp"
USE_CASES_DIR = Path(__file__).parent.parent / "use-cases"

_mcp_client: Client | None = None


# Data-access helpers

async def fetch_asset(uri: str | Path, channel: str, type: str = "prompt") -> str:
    if channel == "local":
        path = Path(uri)
        return path.read_text() if path.exists() else ""

    if channel == "mcp":
        if _mcp_client is None:
            raise RuntimeError("MCP client is not initialized")
        contents = await _mcp_client.read_resource(str(uri))
        return contents[0].text

    raise ValueError(f"Unsupported channel '{channel}'")


async def fetch_steps(use_case: str, channel: str) -> list[str]:
    if channel == "local":
        use_case_dir = USE_CASES_DIR / use_case
        return sorted(
            (d.name for d in use_case_dir.iterdir() if d.is_dir() and d.name.startswith("step_")),
            key=lambda name: int(name.split("_")[1]),
        )

    if channel == "mcp":
        return json.loads(await fetch_asset(f"use-cases://{use_case}/steps", channel))

    raise ValueError(f"Unsupported channel '{channel}'")


# Pipeline helpers

async def fetch_use_cases(channel: str) -> list[str]:
    if channel == "local":
        return sorted(p.name for p in USE_CASES_DIR.iterdir() if p.is_dir())

    if channel == "mcp":
        return json.loads(await fetch_asset("use-cases://", channel))

    raise ValueError(f"Unsupported channel '{channel}'")


async def resolve_use_case(use_case_input: str, llm: ChatOllama, channel: str) -> str:
    """Step 0: list all use cases and ask the LLM to pick the best match."""
    use_cases = await fetch_use_cases(channel)
    print(f"[step_0] available use cases: {use_cases}")

    response = llm.invoke([
        SystemMessage(
            content=(
                "You are a use case resolver. "
                "Given a user's input and a list of available use case names, "
                "return ONLY the exact name of the best matching use case. "
                "No explanation, no punctuation - just the exact name."
            )
        ),
        HumanMessage(
            content=(
                f"User input: {use_case_input}\n\n"
                f"Available use cases:\n{json.dumps(use_cases, indent=2)}\n\n"
                "Return only the exact use case name."
            )
        ),
    ])
    resolved = response.content.strip()
    print(f"[step_0] resolved '{use_case_input}' -> '{resolved}'\n")
    return resolved


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


def asset_uri(use_case: str, channel: str, asset: str, step_name: str | None = None) -> str | Path:
    if channel == "local":
        if asset == "task":
            return USE_CASES_DIR / use_case / "agent_task_description.md"
        if asset == "input":
            return USE_CASES_DIR / use_case / "input_data.md"
        if step_name is not None:
            return USE_CASES_DIR / use_case / step_name / f"{asset}.md"

    if channel == "mcp":
        if asset in {"task", "input"}:
            return f"use-cases://{use_case}/{asset}"
        if step_name is not None:
            return f"use-cases://{use_case}/{step_name}/{asset}"

    raise ValueError(f"Unsupported asset '{asset}' for channel '{channel}'")


async def run_step(
    use_case: str,
    step_name: str,
    agent_task_description: str,
    input_data: str,
    previous_outputs: dict[str, str],
    context: dict,
    context_path: Path,
    llm: ChatOllama,
    channel: str,
) -> str:
    print(f"[{step_name}] running ...")

    spec = await fetch_asset(asset_uri(use_case, channel, "spec", step_name), channel)
    output_format = await fetch_asset(asset_uri(use_case, channel, "output", step_name), channel)

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
    channel = AGENT_TYPE
    if channel not in {"local", "mcp"}:
        raise ValueError("AGENT_TYPE must be either 'local' or 'mcp'")

    llm = ChatOllama(model="gemma4:e4b", num_ctx=32768, temperature=0)
    use_case = await resolve_use_case(use_case_input, llm, channel)

    agent_task_description = await fetch_asset(asset_uri(use_case, channel, "task"), channel)
    input_data = await fetch_asset(asset_uri(use_case, channel, "input"), channel)
    steps = await fetch_steps(use_case, channel)

    if not steps:
        print("No steps found.")
        return ""

    print(f"Use case: {use_case}")
    print(f"Steps:    {steps}\n")

    context: dict = {}
    context_path = USE_CASES_DIR / use_case / "context.json"
    previous_outputs: dict[str, str] = {}

    for step_name in steps:
        step_output = await run_step(
            use_case, step_name,
            agent_task_description, input_data,
            previous_outputs, context, context_path, llm, channel,
        )
        previous_outputs[step_name] = step_output

    final_output = previous_outputs[steps[-1]]
    report_path = USE_CASES_DIR / use_case / "final_report.md"
    report_path.write_text(final_output)

    print(f"Pipeline complete. Results in context.json and {report_path}")
    return final_output


async def run_pipeline_with_client(use_case_input: str) -> str:
    global _mcp_client

    if AGENT_TYPE == "local":
        return await run_pipeline(use_case_input)

    async with Client(mcp) as client:
        _mcp_client = client
        try:
            return await run_pipeline(use_case_input)
        finally:
            _mcp_client = None


def main():
    if len(sys.argv) != 2:
        print("Usage: python agent.py <use_case_name>")
        sys.exit(1)

    asyncio.run(run_pipeline_with_client(sys.argv[1]))


if __name__ == "__main__":
    main()
