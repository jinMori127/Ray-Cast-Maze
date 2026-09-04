"""How many levels have been cleared, kept in a file beside the game so unlocks persist."""

import json
import os

from src.levels import LEVELS

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "progress.json")


def load():
    """Cleared-level count read from disk, clamped to the levels that actually exist."""
    try:
        with open(PATH, encoding="utf-8") as handle:
            return max(0, min(int(json.load(handle)["cleared"]), len(LEVELS)))
    except (OSError, TypeError, ValueError, KeyError):
        return 0  # absent, unreadable or hand-edited into nonsense — start from the first level


def save(cleared):
    """Write the cleared count, staying quiet when the folder is not writable."""
    try:
        with open(PATH, "w", encoding="utf-8") as handle:
            json.dump({"cleared": cleared}, handle)
    except OSError:
        pass


def unlocked(cleared):
    """How many levels are playable: every cleared one, plus the next still to beat."""
    return min(cleared + 1, len(LEVELS))
