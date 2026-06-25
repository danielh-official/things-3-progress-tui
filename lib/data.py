# ---------------------------------------------------------------------------
# Data layer (pure where possible)
# ---------------------------------------------------------------------------

NO_HEADING = "Root"  # bucket for to-dos with no heading


def group_todos(todos, headings=None):
    """Bucket to-dos by heading title and compute completion ratios.

    Pure function: takes lists of things.py-style dicts, returns
    (heading_buckets, overall). A bucket is {title, done, total, ratio}.
    `status == 'completed'` counts as done; `'canceled'` is excluded from total.
    Empty headings (passed in `headings`) appear with total 0.
    """
    buckets = {}  # title -> {"done": int, "total": int}
    order = []  # preserve first-seen order; "No heading" forced first

    def bucket(title):
        if title not in buckets:
            buckets[title] = {"done": 0, "total": 0}
            order.append(title)
        return buckets[title]

    bucket(NO_HEADING)  # always exists, shown first
    for h in headings or []:
        bucket(h.get("title") or h.get("heading_title") or NO_HEADING)

    for t in todos:
        if t.get("status") == "canceled":
            continue
        b = bucket(t.get("heading_title") or NO_HEADING)
        b["total"] += 1
        if t.get("status") == "completed":
            b["done"] += 1

    # Drop the "No heading" bucket if it ended up empty and other headings exist.
    if buckets[NO_HEADING]["total"] == 0 and len(order) > 1:
        order.remove(NO_HEADING)
        del buckets[NO_HEADING]

    out = []
    done_sum = total_sum = 0
    for title in order:
        d, tot = buckets[title]["done"], buckets[title]["total"]
        done_sum += d
        total_sum += tot
        out.append({"title": title, "done": d, "total": tot, "ratio": _ratio(d, tot)})

    overall = {"done": done_sum, "total": total_sum, "ratio": _ratio(done_sum, total_sum)}
    return out, overall


def _ratio(done, total):
    return done / total if total else 0.0


def _progress_for(uuid):
    """Grouped progress for a project uuid -> (buckets, overall)."""
    # pylint: disable=import-outside-toplevel
    import things  # imported here so the self-check runs without Things installed

    todos = things.todos(project=uuid, status=None)  # status=None -> include completed/canceled
    headings = things.tasks(type="heading", project=uuid)
    return group_todos(todos, headings)


def fetch_project(name):
    """Look up a project by name in Things and return its grouped progress.

    Returns (uuid, title, heading_buckets, overall). Raises ValueError with a
    friendly message if not found / DB unreadable.
    """
    # pylint: disable=import-outside-toplevel
    import things

    name_l = name.strip().lower()
    matches = [p for p in things.projects() if p.get("title", "").lower() == name_l]
    if not matches:
        # fall back to substring match for convenience
        matches = [p for p in things.projects() if name_l in p.get("title", "").lower()]
    if not matches:
        raise ValueError(f"No project matching {name!r}.")

    proj = matches[0]
    buckets, overall = _progress_for(proj["uuid"])
    return proj["uuid"], proj["title"], buckets, overall


def fetch_by_uuid(uuid):
    """Grouped progress for a known project uuid -> (title, buckets, overall)."""
    # pylint: disable=import-outside-toplevel
    import things

    proj = things.get(uuid)
    if not proj:
        raise ValueError(f"Project {uuid!r} not found in Things.")
    buckets, overall = _progress_for(uuid)
    return proj.get("title", uuid), buckets, overall # type: ignore


def things_url(uuid):
    """Things 3 URL scheme link that opens the project in the app."""
    return f"things:///show?id={uuid}"
