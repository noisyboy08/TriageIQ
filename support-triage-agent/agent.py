import json
import sys
from openai import OpenAI
from config import BASE_URL, API_KEY, MODEL, SYSTEM_PROMPT
from tools import TOOL_DEFINITIONS, TriageState


def _make_client() -> OpenAI:
    if not BASE_URL:
        print(
            "ERROR: AI_INTEGRATIONS_OPENAI_BASE_URL is not set. "
            "Run setup or export the environment variable.",
            file=sys.stderr,
        )
        sys.exit(1)
    return OpenAI(base_url=BASE_URL, api_key=API_KEY)


def run_triage(ticket_text: str, verbose: bool = False) -> TriageState:
    client = _make_client()
    state = TriageState()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Please triage the following support ticket:\n\n---\n{ticket_text}\n---",
        },
    ]

    while not state.finalized:
        response = client.responses.create(
            model=MODEL,
            input=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="required",
        )

        output_items = response.output

        assistant_message = {"role": "assistant", "content": []}
        tool_results = []

        for item in output_items:
            if item.type == "message":
                for block in item.content:
                    if hasattr(block, "text"):
                        assistant_message["content"].append(
                            {"type": "text", "text": block.text}
                        )
                        if verbose:
                            print(f"[agent]: {block.text}")

            elif item.type == "function_call":
                args = json.loads(item.arguments)
                result = state.handle_tool_call(item.name, args)

                if verbose:
                    print(f"[tool:{item.name}] → {result}")

                assistant_message["content"].append(
                    {
                        "type": "function_call",
                        "call_id": item.call_id,
                        "name": item.name,
                        "arguments": item.arguments,
                    }
                )
                tool_results.append(
                    {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": result,
                    }
                )

        if assistant_message["content"]:
            messages.append(assistant_message)

        if tool_results:
            messages.append({"role": "tool", "content": tool_results})

        if not tool_results:
            break

    return state
