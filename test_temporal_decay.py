"""
Test Temporal Decay Reranking Implementation

This test verifies that the exponential temporal decay formula works correctly
without requiring the full server infrastructure.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path to import directly without package initialization
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import directly to avoid chromadb dependency
from modules.vector_storage.search.similarity_filter import SimilarityFilter


class MockSearchResult:
    """Mock SearchResult for testing"""
    def __init__(self, id: str, similarity: float, age_days: float):
        self.id = id
        self.similarity = similarity
        # Calculate timestamp from age_days
        current_time = datetime.utcnow()
        memory_time = current_time - timedelta(days=age_days)
        self.metadata = {"date": memory_time.timestamp()}


def test_temporal_decay_disabled():
    """Test that decay is skipped when disabled"""
    print("\n=== Test 1: Temporal Decay Disabled ===")

    results = [
        MockSearchResult("mem1", 0.9, age_days=60),
        MockSearchResult("mem2", 0.8, age_days=5),
    ]

    filter = SimilarityFilter()
    reranked = filter.apply_temporal_decay(
        results=results,
        enable_temporal_decay=False,
        half_life_days=30
    )

    # Similarity scores should be unchanged
    assert reranked[0].similarity == 0.9, "Similarity should be unchanged when disabled"
    assert reranked[1].similarity == 0.8, "Similarity should be unchanged when disabled"
    print("✅ PASS: Decay correctly skipped when disabled")


def test_temporal_decay_basic():
    """Test basic temporal decay with 30-day half-life"""
    print("\n=== Test 2: Basic Temporal Decay (30-day half-life) ===")

    # Create test results with different ages
    results = [
        MockSearchResult("mem1", 1.0, age_days=0),    # Brand new
        MockSearchResult("mem2", 1.0, age_days=15),   # 15 days old
        MockSearchResult("mem3", 1.0, age_days=30),   # 30 days old (1 half-life)
        MockSearchResult("mem4", 1.0, age_days=60),   # 60 days old (2 half-lives)
        MockSearchResult("mem5", 1.0, age_days=90),   # 90 days old (3 half-lives)
    ]

    filter = SimilarityFilter()
    reranked = filter.apply_temporal_decay(
        results=results,
        enable_temporal_decay=True,
        half_life_days=30.0
    )

    # Verify decay factors
    # Formula: decay = 0.5 ^ (age_days / half_life_days)

    # 0 days: 0.5^(0/30) = 0.5^0 = 1.0 (100%)
    assert abs(reranked[0].similarity - 1.0) < 0.01, f"Expected ~1.0, got {reranked[0].similarity}"
    print(f"  0 days old:  {reranked[0].similarity:.4f} (expected ~1.0000)")

    # 15 days: 0.5^(15/30) = 0.5^0.5 = ~0.707 (70.7%)
    assert abs(reranked[1].similarity - 0.707) < 0.01, f"Expected ~0.707, got {reranked[1].similarity}"
    print(f"  15 days old: {reranked[1].similarity:.4f} (expected ~0.7071)")

    # 30 days: 0.5^(30/30) = 0.5^1 = 0.5 (50%)
    assert abs(reranked[2].similarity - 0.5) < 0.01, f"Expected ~0.5, got {reranked[2].similarity}"
    print(f"  30 days old: {reranked[2].similarity:.4f} (expected ~0.5000)")

    # 60 days: 0.5^(60/30) = 0.5^2 = 0.25 (25%)
    assert abs(reranked[3].similarity - 0.25) < 0.01, f"Expected ~0.25, got {reranked[3].similarity}"
    print(f"  60 days old: {reranked[3].similarity:.4f} (expected ~0.2500)")

    # 90 days: 0.5^(90/30) = 0.5^3 = 0.125 (12.5%)
    assert abs(reranked[4].similarity - 0.125) < 0.01, f"Expected ~0.125, got {reranked[4].similarity}"
    print(f"  90 days old: {reranked[4].similarity:.4f} (expected ~0.1250)")

    print("✅ PASS: Decay factors match expected exponential curve")


def test_temporal_decay_reranking():
    """Test that older high-similarity memories can be outranked by newer ones"""
    print("\n=== Test 3: Reranking Effect ===")

    # Old memory with high similarity vs new memory with lower similarity
    results = [
        MockSearchResult("old_high", 0.9, age_days=90),   # 90 days old, 0.9 similarity
        MockSearchResult("new_low", 0.6, age_days=5),     # 5 days old, 0.6 similarity
    ]

    filter = SimilarityFilter()
    reranked = filter.apply_temporal_decay(
        results=results,
        enable_temporal_decay=True,
        half_life_days=30.0
    )

    # Calculate expected scores:
    # old_high: 0.9 × 0.5^(90/30) = 0.9 × 0.125 = 0.1125
    # new_low:  0.6 × 0.5^(5/30)  = 0.6 × 0.891 = 0.5346

    print(f"  Old (90d, 0.9 sim): {reranked[1].similarity:.4f} (expected ~0.1125)")
    print(f"  New (5d, 0.6 sim):  {reranked[0].similarity:.4f} (expected ~0.5346)")

    # After reranking, newer memory should be first
    assert reranked[0].id == "new_low", "Newer memory should be ranked higher"
    assert reranked[1].id == "old_high", "Older memory should be ranked lower"

    print("✅ PASS: Reranking correctly promotes recent memories")


def test_different_half_lives():
    """Test different half-life parameters"""
    print("\n=== Test 4: Different Half-Life Values ===")

    filter = SimilarityFilter()

    # Test with 15-day half-life (faster decay)
    results_fast = [MockSearchResult("mem", 1.0, age_days=30)]
    fast_decay = filter.apply_temporal_decay(
        results=results_fast,
        enable_temporal_decay=True,
        half_life_days=15.0
    )
    # 30 days with 15-day half-life: 0.5^(30/15) = 0.5^2 = 0.25
    print(f"  15-day half-life: {fast_decay[0].similarity:.4f} (expected ~0.2500)")
    assert abs(fast_decay[0].similarity - 0.25) < 0.01

    # Test with 60-day half-life (slower decay) - create fresh object
    results_slow = [MockSearchResult("mem", 1.0, age_days=30)]
    slow_decay = filter.apply_temporal_decay(
        results=results_slow,
        enable_temporal_decay=True,
        half_life_days=60.0
    )
    # 30 days with 60-day half-life: 0.5^(30/60) = 0.5^0.5 = 0.707
    print(f"  60-day half-life: {slow_decay[0].similarity:.4f} (expected ~0.7071)")
    assert abs(slow_decay[0].similarity - 0.707) < 0.01

    print("✅ PASS: Different half-life values produce expected decay rates")


def test_metadata_preservation():
    """Test that decay metadata is added to results"""
    print("\n=== Test 5: Metadata Preservation ===")

    results = [
        MockSearchResult("mem1", 0.8, age_days=30),
    ]

    filter = SimilarityFilter()
    reranked = filter.apply_temporal_decay(
        results=results,
        enable_temporal_decay=True,
        half_life_days=30.0
    )

    # Check that debugging metadata was added
    assert hasattr(reranked[0], 'original_similarity'), "Should have original_similarity"
    assert hasattr(reranked[0], 'decay_factor'), "Should have decay_factor"
    assert hasattr(reranked[0], 'age_days'), "Should have age_days"

    assert reranked[0].original_similarity == 0.8, "Original similarity should be preserved"
    assert abs(reranked[0].decay_factor - 0.5) < 0.01, "Decay factor should be ~0.5 for 30 days"
    assert abs(reranked[0].age_days - 30) < 1, "Age should be ~30 days"

    print(f"  Original similarity: {reranked[0].original_similarity}")
    print(f"  Decay factor: {reranked[0].decay_factor:.4f}")
    print(f"  Age (days): {reranked[0].age_days:.2f}")
    print(f"  New similarity: {reranked[0].similarity:.4f}")

    print("✅ PASS: Metadata correctly preserved for transparency")


if __name__ == "__main__":
    print("=" * 60)
    print("TEMPORAL DECAY RERANKING TEST SUITE")
    print("=" * 60)

    try:
        test_temporal_decay_disabled()
        test_temporal_decay_basic()
        test_temporal_decay_reranking()
        test_different_half_lives()
        test_metadata_preservation()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\nTemporal decay reranking is working correctly!")
        print("Formula: final_score = similarity × (0.5 ^ (age_in_days / half_life_days))")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
