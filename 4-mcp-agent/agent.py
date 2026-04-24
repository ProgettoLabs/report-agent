"""
Modular Agentic Pipeline Runner — MCP Implementation

Connects to the report-agent MCP server to discover use cases and execute
pipeline steps. Accepts a (potentially misspelled) use case name and uses
an LLM to resolve it before running.

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
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from mcp_server import mcp

USE_CASES_DIR = Path(__file__).parent.parent / "use-cases"


async def resolve_use_case(client: Client, user_input: str, llm: ChatOllama) -> str:
    """Step 0: list all use cases and ask the LLM to pick the best match."""
    contents = await client.read_resource("use-cases://")
    use_cases: list[str] = json.loads(contents[0].text)

    print(f"[step_0] available use cases: {use_cases}")

    response = llm.invoke([
        SystemMessage(
            content=(
                "You are a use case resolver. "
                "Given a user's input and a list of available use case names, "
                "return ONLY the exact name of the best matching use case. "
                "No explanation, no punctuation — just the exact name."
            )
        ),
        HumanMessage(
            content=(
                f"User input: {user_input}\n\n"
                f"Available use cases:\n{json.dumps(use_cases, indent=2)}\n\n"
                "Return only the exact use case name."
            )
        ),
    ])
    resolved = response.content.strip()
    print(f"[step_0] resolved '{user_input}' → '{resolved}'\n")
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


async def run_step(
    client: Client,
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

    spec_contents = await client.read_resource(f"use-cases://{use_case}/{step_name}/spec")
    output_contents = await client.read_resource(f"use-cases://{use_case}/{step_name}/output")
    spec = spec_contents[0].text
    output_format = output_contents[0].text

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
    llm = ChatOllama(model="gemma4", num_ctx=32768, temperature=0)

    async with Client(mcp) as client:
        use_case = await resolve_use_case(client, use_case_input, llm)

        task_contents = await client.read_resource(f"use-cases://{use_case}/task")
        agent_task_description = task_contents[0].text

        input_contents = await client.read_resource(f"use-cases://{use_case}/input")
        input_data = input_contents[0].text

        steps_contents = await client.read_resource(f"use-cases://{use_case}/steps")
        steps: list[str] = json.loads(steps_contents[0].text)

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
                client, use_case, step_name,
                agent_task_description, input_data,
                previous_outputs, context, context_path, llm,
            )
            previous_outputs[step_name] = step_output

        final_output = previous_outputs[steps[-1]]
        report_path = USE_CASES_DIR / use_case / "final_report.md"
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
