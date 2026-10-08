import locale
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(autouse=True)
def c_numeric_locale(qapp):
    """libmpv refuses to start unless LC_NUMERIC is "C"; QApplication resets it from the environment."""
    locale.setlocale(locale.LC_NUMERIC, "C")
