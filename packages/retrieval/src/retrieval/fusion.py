"""Reciprocal Rank Fusion.

Dense and sparse search produce two ranked lists whose scores are not comparable (a cosine
distance and a BM25 score live on different scales), so they cannot be merged by adding scores.
RRF merges by RANK instead: each item scores the sum over the lists of 1 / (k + rank). An item
that ranks well in either list rises, and the constant k (60 by convention, from Cormack et al.
2009) dampens how much a single first-place finish dominates. No score calibration, no tuning.

See packages/kb/hybrid-search.md.
"""

from __future__ import annotations


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Fuse ranked id lists into one list of (id, rrf_score), best first.

    Args:
        rankings: each inner list is ids ordered best-first by one retriever.
        k: the RRF constant; larger k flattens the contribution of top ranks.
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):  # rank is 0-based
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda p: p[1], reverse=True)
