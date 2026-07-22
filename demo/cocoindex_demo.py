"""Standalone demo: shows every request and response when using cocoindex-code
(the semantic/embedding-based MCP alternative to code-index-mcp) against a tiny
sample project.

This does NOT need the FastAPI backend or Ollama running — it talks to the
cocoindex-code MCP server directly, so you can see exactly what it does in
isolation before trusting it inside the full review pipeline.

Prerequisites (install once, separately from this project's own dependencies):

    uv tool install --force "cocoindex-code[full]"

Usage:

    uv run --with mcp python demo/cocoindex_demo.py

What it does, in order, printing the full input and output of each step:
  1. `ccc init -f`   - initializes cocoindex-code for demo/sample_project
  2. `ccc index`     - builds the semantic index (downloads an embedding model
                        on first run - needs real internet access)
  3. MCP initialize  - starts `ccc mcp` over stdio, does the MCP handshake
  4. tools/list      - lists the tools cocoindex-code exposes
  5. tools/call search - runs a natural-language query against the indexed code
"""

import asyncio
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SAMPLE_PROJECT = Path(__file__).parent / "sample_project"


def show(arrow: str, label: str, payload) -> None:
    print(f"\n{arrow} {label}")
    print("-" * len(f"{arrow} {label}"))
    try:
        print(json.dumps(payload, indent=2, default=str))
    except TypeError:
        print(str(payload))


async def run_subprocess_step(args: list[str]) -> None:
    show("==>", f"subprocess: {' '.join(args)}  (cwd={SAMPLE_PROJECT})", {})
    proc = await asyncio.create_subprocess_exec(
        *args,
        cwd=str(SAMPLE_PROJECT),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    show("<==", f"subprocess result: {' '.join(args)}", out.decode(errors="ignore"))


async def main() -> None:
    print("=" * 70)
    print("STEP 1-2: build the semantic index (ccc init + ccc index)")
    print("=" * 70)
    await run_subprocess_step(["ccc", "init", "-f"])
    await run_subprocess_step(["ccc", "index"])

    print("\n" + "=" * 70)
    print("STEP 3: MCP handshake (spawn `ccc mcp`, initialize the session)")
    print("=" * 70)
    params = StdioServerParameters(command="ccc", args=["mcp"], cwd=str(SAMPLE_PROJECT))
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        show("==>", "initialize", {})
        init_result = await session.initialize()
        show("<==", "initialize result", init_result.model_dump())

        print("\n" + "=" * 70)
        print("STEP 4: tools/list — what can this MCP server do?")
        print("=" * 70)
        show("==>", "tools/list", {})
        tools = await session.list_tools()
        show(
            "<==",
            "tools/list result",
            [{"name": t.name, "description": t.description} for t in tools.tools],
        )

        print("\n" + "=" * 70)
        print("STEP 5: tools/call search — a natural-language query")
        print("=" * 70)
        queries = [
            "function that verifies a user's password",
            "how are todos removed",
        ]
        for query in queries:
            args = {"query": query, "limit": 3}
            show("==>", "tools/call search", args)
            result = await session.call_tool("search", args)
            text = "\n".join(b.text for b in result.content if getattr(b, "type", None) == "text")
            show("<==", "tools/call search result", text)

    print("\n" + "=" * 70)
    print("Done. Compare this to demo/EXAMPLE_OUTPUT.md for a real captured run.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
