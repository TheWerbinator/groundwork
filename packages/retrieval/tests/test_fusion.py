"""Reciprocal Rank Fusion tests. Pure function, no network."""

from __future__ import annotations

from retrieval.fusion import reciprocal_rank_fusion


def test_single_ranking_preserves_order():
    fused = reciprocal_rank_fusion([["a", "b", "c"]], k=60)
    assert [doc for doc, _ in fused] == ["a", "b", "c"]


def test_score_uses_one_based_rank():
    # Top of a single list scores 1/(k+1).
    fused = dict(reciprocal_rank_fusion([["a", "b"]], k=60))
    assert fused["a"] == 1.0 / 61
    assert fused["b"] == 1.0 / 62


def test_item_in_both_lists_outranks_items_seen_once():
    # The core value of fusion: "c" is only 2nd in each list but appears in BOTH, while "a"
    # and "b" are each 1st in one list and absent from the other.
    dense = ["a", "c"]
    sparse = ["b", "c"]
    fused = reciprocal_rank_fusion([dense, sparse], k=60)
    # c: 1/62 + 1/62 = 0.03226 beats a: 1/61 and b: 1/61 = 0.01639 each.
    assert fused[0][0] == "c"


def test_item_in_one_list_only_still_scores():
    fused = dict(reciprocal_rank_fusion([["a"], ["b"]], k=60))
    assert fused["a"] == 1.0 / 61
    assert fused["b"] == 1.0 / 61


def test_smaller_k_sharpens_top_rank_advantage():
    # With small k, rank-1 dominates more strongly than with large k.
    small = dict(reciprocal_rank_fusion([["a", "b"]], k=1))
    large = dict(reciprocal_rank_fusion([["a", "b"]], k=1000))
    assert small["a"] / small["b"] > large["a"] / large["b"]
