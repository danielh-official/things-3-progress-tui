"""Self-check for the pure layers (no Things/Textual needed). Run: python test_data.py"""
from lib.data import group_todos, things_url, NO_HEADING
from lib.progress import render_bar


def test():
    todos = [
        {"status": "completed", "heading_title": "Design"},
        {"status": "incomplete", "heading_title": "Design"},
        {"status": "canceled", "heading_title": "Design"},  # excluded from total
        {"status": "completed", "heading_title": None},  # -> "No heading"
        {"status": "completed", "heading_title": "Ship"},
    ]
    headings = [{"title": "Empty"}]  # heading with no todos
    buckets, overall = group_todos(todos, headings)
    by = {b["title"]: b for b in buckets}

    assert by["Design"]["done"] == 1 and by["Design"]["total"] == 2, by["Design"]
    assert by["Design"]["ratio"] == 0.5
    assert by[NO_HEADING]["done"] == 1 and by[NO_HEADING]["total"] == 1
    assert by["Ship"]["ratio"] == 1.0
    assert by["Empty"]["total"] == 0 and by["Empty"]["ratio"] == 0.0
    # overall: done = Design1 + None1 + Ship1 = 3; total = 2+1+1 = 4
    assert overall["done"] == 3 and overall["total"] == 4, overall
    assert overall["ratio"] == 0.75

    # canceled-only / empty project -> ratio 0, no crash
    _, ov2 = group_todos([{"status": "canceled", "heading_title": None}], [])
    assert ov2 == {"done": 0, "total": 0, "ratio": 0.0}, ov2

    # Bar fill extremes and a midpoint.
    assert render_bar(1.0, "", 10).plain.startswith("█" * 10), "ratio=1.0 must fill bar"
    assert "█" not in render_bar(0.0, "", 10).plain, "ratio=0.0 must empty bar"
    assert render_bar(0.5, "", 10).plain.startswith("█" * 5 + "░" * 5), "ratio=0.5 must half-fill"

    assert things_url("ABC123") == "things:///show?id=ABC123"

    print("self-check OK")


if __name__ == "__main__":
    test()
