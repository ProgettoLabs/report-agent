"""
Modular Agentic Pipeline Runner — LangChain Tool-Calling Implementation

For each step directory the pipeline runs a dedicated agent loop.
Each loop has access to read_step_output / write_step_output and decides:
  - which prior step outputs (if any) it needs to read first
  - when to write its own result

Keeping one agent per step bounds the context window regardless of pipeline length.

Requires Ollama running locally with the target model pulled.
"""

from pathlib import Path

from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from tools import read_input_data, read_step_output, write_step_output
from utils import PIPELINE_DIR


# ---------------------------------------------------------------------------
# System prompt — filled via .partial() with pipeline/step context.
# {input} and {agent_scratchpad} are handled by the ChatPromptTemplate.
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an AI assistant executing one step of a multi-step data pipeline.

## Pipeline Overview
{pipeline_md}

## Your Current Step: {step_name}  (step_number={step_number})

### Spec
{spec}

### Required Output Format
{output_format}

---

## Instructions
1. Decide whether you need outputs from any previous steps. If so, use
   read_step_output to fetch them (you may call it multiple times).
2. Produce the output described in the spec and output format above.
3. Call write_step_output to persist your result. Do NOT finish without writing.
4. Once all outputs are written, reply with a short confirmation message."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def discover_steps(pipeline_dir: Path) -> list[Path]:
    return sorted(
        d for d in pipeline_dir.iterdir()
        if d.is_dir() and d.name.startswith("step_")
    )


def read_file(path: Path) -> str:
    return path.read_text() if path.exists() else ""


# ---------------------------------------------------------------------------
# Per-step agent run
# ---------------------------------------------------------------------------

def run_step(step_dir: Path, pipeline_md: str, llm: ChatOllama) -> None:
    step_number = int(step_dir.name.split("_")[1])
    step_name = step_dir.name

    print(f"\n[{step_name}] starting ...")

    spec = read_file(step_dir / "spec.md")
    output_format = read_file(step_dir / "output.md")

    tools = [read_input_data, read_step_output, write_step_output]

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]).partial(
        pipeline_md=pipeline_md,
        step_name=step_name,
        step_number=step_number,
        spec=spec,
        output_format=output_format,
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=20,       # read(s) + up to 6 writes + reasoning headroom
    )

    executor.invoke({"input": f"Execute step {step_number} now."})
    print(f"[{step_name}] done")


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def run_pipeline(pipeline_dir: str) -> None:
    root = Path(pipeline_dir).resolve()
    pipeline_md = read_file(root / "pipeline.md")
    steps = discover_steps(root)

    if not steps:
        print("No step directories found.")
        return

    print(f"Pipeline : {root.name}")
    print(f"Steps    : {[s.name for s in steps]}")

    context_path = root / "context.json"
    context_path.write_text("{}")
    print("Cleared  : context.json")

    llm = ChatOllama(model="gemma4", num_ctx=65536, temperature=0)

    for step_dir in steps:
        run_step(step_dir, pipeline_md, llm)

    print(f"\nPipeline complete. Results in {root / 'context.json'}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if not PIPELINE_DIR.is_dir():
        print(f"Error: '{PIPELINE_DIR}' is not a directory")
        return
    run_pipeline(str(PIPELINE_DIR))


if __name__ == "__main__":
    main()
