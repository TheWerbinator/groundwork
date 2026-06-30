"""Command-line interface: `ingestion ingest` and `ingestion query`.

    uv run ingestion ingest
    uv run ingestion query "how does reciprocal rank fusion work?"
"""

from __future__ import annotations

import typer

from ingestion.config import get_settings
from ingestion.embeddings import build_embedder
from ingestion.pipeline import run_ingest
from ingestion.store import ChromaStore

app = typer.Typer(add_completion=False, help="Groundwork knowledge-base ingestion.")


@app.command()
def ingest() -> None:
    """Chunk, embed, and load the knowledge base into Chroma."""
    settings = get_settings()
    typer.echo(f"Embedder: {settings.embedding_provider}  KB: {settings.kb_path}")
    report = run_ingest(settings)
    typer.echo(
        f"Ingested {report.documents} docs -> {report.chunks} chunks "
        f"with {report.embedder}. Collection now holds {report.collection_count}."
    )


@app.command()
def query(
    text: str = typer.Argument(..., help="The question to search the KB for."),
    n: int = typer.Option(5, "--n", help="Number of chunks to return."),
) -> None:
    """Embed a query and print the nearest KB chunks (a smoke test for retrieval)."""
    settings = get_settings()
    embedder = build_embedder(settings)
    store = ChromaStore(settings)
    if store.count == 0:
        typer.echo("Collection is empty. Run `ingestion ingest` first.")
        raise typer.Exit(code=1)

    hits = store.query(embedder.embed_query(text), n_results=n)
    for i, hit in enumerate(hits, 1):
        source = hit.metadata.get("source", "?")
        heading = hit.metadata.get("heading", "")
        loc = f"{source} ({heading})" if heading else source
        preview = " ".join(hit.text.split())[:160]
        typer.echo(f"\n{i}. [{loc}]  cosine_distance={hit.distance:.4f}\n   {preview}...")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
