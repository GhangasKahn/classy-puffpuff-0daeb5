"""
MEUFT Brain — single-agent PrimeAgent / WFX graph (Phase-1).

Run (with OPENAI_API_KEY or configured LLM):
  source /workspace/.venv-primeagent/bin/activate
  python -c "from lpros_agents_bootstrap import *; ..."

Or import this module after placing package on PYTHONPATH / installing editable.

This graph is the programmatic twin of `Meuft Brain Agent.json`.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM_PROMPT = (Path(__file__).parent / "SYSTEM_PROMPT.md").read_text()
AGENT_DESCRIPTION = (
    "MEUFT Brain is the LPROS orchestration authority for profitable, high-ticket "
    "eBay product research. Mission → Economics Engine → Uncertainty/Evidence → "
    "Factor Verification → Task-contracts & Conditioning. Cash is truth. Fail-closed. "
    "Soldiers offline in Phase-1."
)


def load_system_prompt() -> str:
    return SYSTEM_PROMPT


def meuft_brain_graph():
    """Build a Simple-Agent-style graph with MEUFT Brain conditioning."""
    from wfx.graph import Graph
    from wfx.components.input_output import ChatInput, ChatOutput

    # Agent component path differs by package version; try PrimeAgent then wfx
    try:
        from primeagent.components.agents.agent import AgentComponent
    except Exception:  # noqa: BLE001
        from wfx.components.agents.agent import AgentComponent  # type: ignore

    try:
        from wfx.components.processing.calculator import CalculatorComponent
    except Exception:  # noqa: BLE001
        CalculatorComponent = None  # type: ignore

    chat_input = ChatInput()
    chat_output = ChatOutput()
    agent = AgentComponent()

    agent_kwargs = dict(
        system_prompt=SYSTEM_PROMPT,
        agent_description=AGENT_DESCRIPTION,
        agent_llm="OpenAI",
        max_iterations=20,
        handle_parsing_errors=True,
        input_value=chat_input.message_response,
    )

    # Optional calculator — Economics-adjacent arithmetic aid (still not ledger authority)
    tools = []
    if CalculatorComponent is not None:
        calc = CalculatorComponent()
        tools.append(calc.build_tool)
        agent_kwargs["tools"] = tools

    agent.set(**agent_kwargs)
    chat_output.set(input_value=agent.message_response)

    return Graph(chat_input, chat_output)


def prompt_card() -> dict:
    """Export prompt bundle for non-graph runners (Ollama/Hermes/Crew)."""
    conditioning = (Path(__file__).parent / "CONDITIONING.md").read_text()
    agents_md = (ROOT / "AGENTS.md").read_text()
    return {
        "name": "MEUFT Brain",
        "role": "Brain",
        "phase": "single_agent",
        "system_prompt": SYSTEM_PROMPT,
        "agent_description": AGENT_DESCRIPTION,
        "conditioning": conditioning,
        "constitution": agents_md,
        "output_contract": "MEUFT BRIEF",
    }


if __name__ == "__main__":
    card = prompt_card()
    print(f"Agent: {card['name']} ({card['role']}) phase={card['phase']}")
    print(f"System prompt: {len(card['system_prompt'])} chars")
    print(f"Constitution: {len(card['constitution'])} chars")
    print("OK — prompt bundle ready. Import Meuft Brain Agent.json into PrimeAgent UI.")
