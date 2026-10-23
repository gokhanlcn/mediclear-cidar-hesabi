import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from physics.symbols import PARAMS  # noqa: E402
from physics.units import to_si  # noqa: E402

# Testlerde kullanılan film formülü (programda kullanıcı seçer)
TEST_FILM_MODEL = "D7a"


@pytest.fixture
def nominal():
    """Örnek değerler, SI."""
    return {k: to_si(p.example, p.unit) for k, p in PARAMS.items() if p.example is not None}
