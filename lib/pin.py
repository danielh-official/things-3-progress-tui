"""Pin label helper for the pin/unpin button."""


@staticmethod
def pin_label(pinned: bool) -> str:
    """Return the label for the pin/unpin button based on whether the project is pinned."""
    return "★ Unpin" if pinned else "☆ Pin to sidebar"
