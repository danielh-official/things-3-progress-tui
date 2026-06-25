"""
Self-check for the pure layers (no Things/Textual needed). 
Run: `.venv/bin/python -m tests.test_data`
"""

from lib.data import group_todos, things_url, NO_HEADING
from lib.progress import render_bar


def _sample_grouping_input():
    """Return representative data for grouped progress calculations."""
    todos = [
        {"status": "completed", "heading_title": "Design"},
        {"status": "incomplete", "heading_title": "Design"},
        {"status": "canceled", "heading_title": "Design"},  # excluded from total
        {"status": "completed", "heading_title": None},  # -> "No heading"
        {"status": "completed", "heading_title": "Ship"},
    ]
    headings = [{"title": "Empty"}]  # heading with no todos
    return todos, headings


def test_group_todos_tracks_done_total_ratio_per_heading():
    """group_todos should compute per-heading progress and ignore canceled items."""
    todos, headings = _sample_grouping_input()
    buckets, _ = group_todos(todos, headings)
    by = {b["title"]: b for b in buckets}

    assert by["Design"]["done"] == 1 and by["Design"]["total"] == 2, by["Design"]
    assert by["Design"]["ratio"] == 0.5
    assert by[NO_HEADING]["done"] == 1 and by[NO_HEADING]["total"] == 1
    assert by["Ship"]["ratio"] == 1.0
    assert by["Empty"]["total"] == 0 and by["Empty"]["ratio"] == 0.0


def test_group_todos_reports_correct_overall_progress():
    """group_todos should aggregate overall done/total/ratio from active todos."""
    todos, headings = _sample_grouping_input()
    _, overall = group_todos(todos, headings)

    # overall: done = Design1 + None1 + Ship1 = 3; total = 2+1+1 = 4
    assert overall["done"] == 3 and overall["total"] == 4, overall
    assert overall["ratio"] == 0.75


def test_group_todos_returns_zero_progress_for_canceled_only_input():
    """Canceled-only projects should return zero progress without crashing."""
    _, ov2 = group_todos([{"status": "canceled", "heading_title": None}], [])
    assert ov2 == {"done": 0, "total": 0, "ratio": 0.0}, ov2


def test_render_bar_fills_completely_at_ratio_one():
    """render_bar should produce a fully filled bar at ratio=1.0."""
    assert render_bar(1.0, "", 10).plain.startswith("█" * 10), "ratio=1.0 must fill bar"


def test_render_bar_is_empty_at_ratio_zero():
    """render_bar should produce no filled blocks at ratio=0.0."""
    assert "█" not in render_bar(0.0, "", 10).plain, "ratio=0.0 must empty bar"


def test_render_bar_half_fills_at_ratio_half():
    """render_bar should split evenly between filled and empty blocks at ratio=0.5."""
    assert render_bar(0.5, "", 10).plain.startswith("█" * 5 + "░" * 5), "ratio=0.5 must half-fill"


def test_things_url_builds_expected_deep_link():
    """things_url should create a Things deep-link URL for the given UUID."""
    assert things_url("ABC123") == "things:///show?id=ABC123"


def run_self_check():
    """Compatibility entrypoint for direct module execution."""
    test_group_todos_tracks_done_total_ratio_per_heading()
    test_group_todos_reports_correct_overall_progress()
    test_group_todos_returns_zero_progress_for_canceled_only_input()
    test_render_bar_fills_completely_at_ratio_one()
    test_render_bar_is_empty_at_ratio_zero()
    test_render_bar_half_fills_at_ratio_half()
    test_things_url_builds_expected_deep_link()
    print("self-check OK")


if __name__ == "__main__":
    run_self_check()
