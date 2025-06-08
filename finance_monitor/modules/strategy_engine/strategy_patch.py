
from modules.google_trends_signal.trends import GoogleTrendsSignal

def compute_strategy_score(tech_score: float, sentiment_score: float, orderbook_score: float, keywords: list) -> float:
    trends_signal, keywords_triggered = GoogleTrendsSignal(keywords).get_signal()

    score = (
        0.5 * tech_score +
        0.2 * sentiment_score +
        0.2 * orderbook_score +
        0.1 * trends_signal
    )
    return round(score, 3), keywords_triggered
