
from modules.google_trends_signal.trends import GoogleTrendsSignal

def test_google_score_range():
    signaler = GoogleTrendsSignal(["Bitcoin"])
    score, triggered = signaler.get_signal()
    assert -1.0 <= score <= 1.0
    assert isinstance(triggered, list)
