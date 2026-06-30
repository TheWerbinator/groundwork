"""Command-line interface for retrieval.

    uv run retrieval search "how does reciprocal rank fusion work?"

Shows the dense leg, the sparse leg, and the fused hybrid result side by side so the value of
fusion over either method alone is visible.
"""

from __future__ import annotations

import typer

from ingestion.config import get_settings

from retrieval.hybrid import HybridRetriever

app = typer.Typer(add_completion=False, help="Groundwork hybrid retrieval.")


@app.callback()
def _root() -> None:
    """Keep `search` as a named subcommand (Typer collapses single-command apps otherwise)."""


@app.command()
def search(
    query: str = typer.Argument(..., help="The question to retrieve for."),
    n: int = typer.Option(5, "--n", help="Results to show per method."),
) -> None:
    """Compare dense, sparse, and hybrid retrieval for one query."""
    settings = get_settings()
    retriever = HybridRetriever(settings)

    typer.echo(f"\nQuery: {query}\n")

    typer.echo("DENSE (vector):")
    for i, cid in enumerate(retriever.vector_search(query, n), 1):
        typer.echo(f"  {i}. {retriever.location(cid)}")

    typer.echo("\nSPARSE (BM25):")
    for i, cid in enumerate(retriever.sparse_search(query, n), 1):
        typer.echo(f"  {i}. {retriever.location(cid)}")

    typer.echo("\nHYBRID (RRF fused + reranked):")
    for i, hit in enumerate(retriever.retrieve(query, top_k=n), 1):
        loc = f"{hit.source} ({hit.heading})" if hit.heading else hit.source
        typer.echo(f"  {i}. {loc}  rrf={hit.score:.4f}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
