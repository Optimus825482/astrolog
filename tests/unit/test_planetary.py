import pytest
from datetime import datetime
from services.astro_service import calculate_celestial_positions


def test_calculate_celestial_positions_basic():
    """Test planetary calculations for a known date/time."""
    # Example: Jan 1, 2000, 12:00 UTC+3 (9:00 UTC)
    dt = datetime(2000, 1, 1, 12, 0, 0)
    # Mock house cusps (simplified)
    house_cusps = {str(i): (i - 1) * 30 for i in range(1, 13)}
    celestial_bodies = {"Sun": 0}  # swe.SUN is 0

    positions = calculate_celestial_positions(dt, house_cusps, celestial_bodies)

    assert "Sun" in positions
    assert (
        280.0 <= positions["Sun"]["degree"] <= 281.0
    )  # Sun was around 280 deg on 2000-01-01
    assert positions["Sun"]["sign"] == "Oğlak"


def test_calculate_celestial_positions_retrograde():
    """Test detection of retrograde motion (e.g., Mercury)."""
    # Example: Mercury was retrograde around April 2024
    dt = datetime(2024, 4, 10, 12, 0, 0)
    house_cusps = {str(i): (i - 1) * 30 for i in range(1, 13)}
    celestial_bodies = {"Mercury": 2}  # swe.MERCURY is 2

    positions = calculate_celestial_positions(dt, house_cusps, celestial_bodies)

    assert positions["Mercury"]["retrograde"] is True


def test_calculate_celestial_positions_empty():
    """Test with empty celestial bodies list."""
    dt = datetime(2000, 1, 1, 12, 0, 0)
    house_cusps = {str(i): (i - 1) * 30 for i in range(1, 13)}
    positions = calculate_celestial_positions(dt, house_cusps, {})
    assert positions == {}
