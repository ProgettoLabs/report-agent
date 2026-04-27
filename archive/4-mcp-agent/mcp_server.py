import json
import smtplib
import yaml
from email.message import EmailMessage
from pathlib import Path
from fastmcp import FastMCP

USE_CASES_DIR = Path(__file__).parent.parent / "use-cases"
CREDENTIALS_PATH = Path(__file__).parent / ".credentials" / "mail_credentials.yaml"

mcp = FastMCP("report-agent")


def _use_case_path(name: str) -> Path:
    path = USE_CASES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Use case '{name}' not found")
    return path


def _step_path(name: str, step: str) -> Path:
    path = _use_case_path(name) / step
    if not path.exists():
        raise FileNotFoundError(f"Step '{step}' not found in use case '{name}'")
    return path


@mcp.resource("use-cases://")
def list_use_cases() -> str:
    """List all available use case names."""
    names = sorted(p.name for p in USE_CASES_DIR.iterdir() if p.is_dir())
    return json.dumps(names, indent=2)


@mcp.resource("use-cases://{name}/steps")
def list_steps(name: str) -> str:
    """List all step folder names for a given use case."""
    base = _use_case_path(name)
    steps = sorted(
        (p.name for p in base.iterdir() if p.is_dir() and p.name.startswith("step_")),
        key=lambda name: int(name.split("_")[1]),
    )
    return json.dumps(steps, indent=2)


@mcp.resource("use-cases://{name}/task")
def get_task(name: str) -> str:
    """Return the agent task description for a use case."""
    return (_use_case_path(name) / "agent_task_description.md").read_text()


@mcp.resource("use-cases://{name}/input")
def get_input(name: str) -> str:
    """Return the input data for a use case."""
    return (_use_case_path(name) / "input_data.md").read_text()


@mcp.resource("use-cases://{name}/context")
def get_context(name: str) -> str:
    """Return the execution context (step outputs) for a use case."""
    return (_use_case_path(name) / "context.json").read_text()


@mcp.resource("use-cases://{name}/{step}/spec")
def get_step_spec(name: str, step: str) -> str:
    """Return the spec for a specific step in a use case."""
    return (_step_path(name, step) / "spec.md").read_text()


@mcp.resource("use-cases://{name}/{step}/output")
def get_step_output(name: str, step: str) -> str:
    """Return the output format definition for a specific step in a use case."""
    return (_step_path(name, step) / "output.md").read_text()


@mcp.resource("use-cases://{name}/{step}/prompt")
def get_step_prompt(name: str, step: str) -> str:
    """Return the pre-rendered prompt for a step (available in Bedrock use cases)."""
    prompt_file = _step_path(name, step) / "prompt.md"
    if not prompt_file.exists():
        raise FileNotFoundError(f"No prompt.md found for step '{step}' in use case '{name}'")
    return prompt_file.read_text()


def _load_email_credentials() -> dict:
    with open(CREDENTIALS_PATH) as f:
        return yaml.safe_load(f)


@mcp.tool()
def send_email(subject: str, body: str) -> str:
    """Send an email to the default recipient with the given subject and body."""
    creds = _load_email_credentials()

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = creds["email_user"]
    msg["To"] = creds["recipient_email"]

    try:
        with smtplib.SMTP(creds["smtp_host"], 587) as server:
            server.starttls()
            server.login(creds["email_user"], creds["email_password"])
            server.send_message(msg)
        return f"Successfully sent email to {creds['recipient_email']}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"


if __name__ == "__main__":
    mcp.run()
