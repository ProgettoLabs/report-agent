import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule

from fastmcp import Client
from mcp_server import mcp

console = Console()

INTRO = """\
[bold white]Resource URIs[/bold white]

  [yellow]use-cases://[/yellow]
    List all use case names

  [yellow]use-cases://{name}/steps[/yellow]
    List steps for a use case

  [yellow]use-cases://{name}/task[/yellow]
    Agent task description

  [yellow]use-cases://{name}/context[/yellow]
    Execution context (step outputs)

  [yellow]use-cases://{name}/{step}/spec[/yellow]
    Step spec

  [yellow]use-cases://{name}/{step}/output[/yellow]
    Step output format

  [yellow]use-cases://{name}/{step}/prompt[/yellow]
    Pre-rendered prompt (Bedrock use cases only)

[dim]Type a URI to fetch it.  [white]h[/white] = show this help.  [white]q[/white] = quit.[/dim]
"""

EXAMPLES = """\
[dim]Examples:
  use-cases://
  use-cases://1-quarterly-report/steps
  use-cases://1-quarterly-report/task
  use-cases://1-quarterly-report/step_01_data_structuring/spec[/dim]"""


def _display(text: str) -> None:
    try:
        parsed = json.loads(text)
        console.print(Syntax(json.dumps(parsed, indent=2), "json", theme="github-dark"))
    except (json.JSONDecodeError, ValueError):
        console.print(text)


async def main() -> None:
    async with Client(mcp) as client:
        console.print()
        console.print(Panel(INTRO, title="[bold cyan]report-agent MCP client[/bold cyan]", border_style="cyan", padding=(0, 2)))
        console.print(EXAMPLES)
        console.print()

        while True:
            try:
                uri = console.input("[cyan]uri >[/cyan] ").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]bye[/dim]")
                break

            if not uri:
                continue
            if uri in ("q", "quit", "exit"):
                console.print("[dim]bye[/dim]")
                break
            if uri in ("h", "help"):
                console.print(Panel(INTRO, border_style="cyan", padding=(0, 2)))
                console.print(EXAMPLES)
                console.print()
                continue

            console.print(Rule(style="dim"))
            try:
                contents = await client.read_resource(uri)
                for item in contents:
                    _display(item.text)
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
            console.print(Rule(style="dim"))
            console.print()


if __name__ == "__main__":
    asyncio.run(main())
