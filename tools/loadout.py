"""Compatibility entry point for the Cats in the Shell equipment model."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from games.cats.models.equipment import conflicts, evaluate, main, placements, render, scores, search, validate

if __name__ == "__main__":
    main()
