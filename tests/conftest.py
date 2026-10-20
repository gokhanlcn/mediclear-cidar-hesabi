import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from physics.symbols import PARAMS  # noqa: E402
from physics.units import to_si  # noqa: E402


@pytest.fixture
def nominal():
    """Örnek (YAKLAŞIK) nominal değerler, SI."""
    return {k: to_si(p.example[1], p.unit) for k, p in PARAMS.items() if p.example}
