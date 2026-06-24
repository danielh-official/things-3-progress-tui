"""Self-check for the pure layers (no Things/Textual needed). Run: python test_data.py"""
from data import group_todos, things_url, NO_HEADING
from radial import ring_cell, W, H


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

    # Radial fill extremes.
    full = [ring_cell(c, r, 1.0) for r in range(H) for c in range(W)]
    none = [ring_cell(c, r, 0.0) for r in range(H) for c in range(W)]
    ring = [x for x in full if x is not None]
    assert ring and all(x == "filled" for x in ring), "progress=1.0 must fill ring"
    ring0 = [x for x in none if x is not None]
    assert ring0 and all(x == "empty" for x in ring0), "progress=0.0 must empty ring"

    # Compact (sidebar) radial geometry still forms a ring and fills fully.
    cw, ch = 13, 7
    comp = [ring_cell(c, r, 1.0, cw, ch) for r in range(ch) for c in range(cw)]
    cring = [x for x in comp if x is not None]
    assert cring and all(x == "filled" for x in cring), "compact ring must fill"

    assert things_url("ABC123") == "things:///show?id=ABC123"

    print("self-check OK")


if __name__ == "__main__":
    test()
