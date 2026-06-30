"""Command-line interface for the agent.

    uv run groundwork-api ask "how does reciprocal rank fusion work?"
    uv run groundwork-api ask "..." --trace      # watch the state change node by node
    uv run groundwork-api serve                  # run the REST API

`--trace` is a teaching tool: it streams one event per node (stream_mode="updates") and prints
the state update each node produced, so the graph stops being abstract. Read it top to bottom and
you see planning, then retrieval, then drafting, with the `notes` list growing via its reducer.
"""

from __future__ import annotations

import typer

from ingestion.config import get_settings

from groundwork_api.service import build_service

app = typer.Typer(add_completion=False, help="Groundwork agent CLI.")


def _preview(value: object, width: int = 80) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= width else text[:width] + "..."


@app.command()
def ask(
    question: str = typer.Argument(..., help="The question to answer."),
    trace: bool = typer.Option(False, "--trace", help="Print the state after each node."),
) -> None:
    """Ask the agent a question. With --trace, watch the graph run node by node."""
    service = build_service(get_settings())

    if not trace:
        state = service.answer(question)
        _print_answer(state)
        return

    typer.echo(f"\nQuestion: {question}\n")
    typer.echo("=== graph trace (one block per node) ===")
    final: dict = {}
    for event in service.stream(question):
        for node_name, update in event.items():
            typer.echo(f"\n[{node_name}]")
            for key, value in update.items():
                if key == "notes":
                    for note in value:
                        typer.echo(f"   note: {note}")
                elif key == "chunks":
                    typer.echo(f"   chunks: {len(value)} retrieved")
                else:
                    typer.echo(f"   {key}: {_preview(value)}")
            final.update(update)
    typer.echo("\n=== final ===")
    _print_answer(final)


def _print_answer(state: dict) -> None:
    typer.echo(f"\n{state.get('answer', '(no answer)')}\n")
    citations = state.get("citations", [])
    if citations:
        typer.echo("Sources:")
        for c in citations:
            loc = f"{c['source']} ({c['heading']})" if c.get("heading") else c["source"]
            typer.echo(f"  - {loc}")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host."),
    port: int = typer.Option(8000, help="Bind port."),
) -> None:
    """Run the REST API (uvicorn)."""
    import uvicorn

    uvicorn.run("groundwork_api.app:app", host=host, port=port, reload=False)


def main() -> None:
    # Windows consoles default to cp1252, which crashes when a model's answer contains
    # characters like U+202F (narrow no-break space). Force UTF-8 so output never raises.
    import sys

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")
    app()


if __name__ == "__main__":
    main()
