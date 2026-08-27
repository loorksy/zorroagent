"""B3.2 similar cases never fake a % below the floor; schema WAIT."""

from app.agent.pipeline import SimilarCases
from app.enums import AnalyticalBias, Direction


def test_similar_past_cases_n_below_floor_never_emits_fake_percent():
    card = SimilarCases(count=12, sample_floor=30, items=[{"outcome": "win_tp1"}] * 12).card_payload()
    assert card["win_rate"] is None
    assert card["label"] == "Insufficient data"


def test_wait_not_in_analytical_bias_enum():
    assert "WAIT" not in {m.value for m in AnalyticalBias}
    assert list(Direction) == [Direction.BUY, Direction.SELL]
