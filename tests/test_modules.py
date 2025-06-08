
import pytest
#from modules.price_trend_analyzer.analyzer import calculate_moving_averages
#from modules.volatility_monitor.monitor import compute_atr
#from modules.orderbook_analyzer.analyzer import analyze_orderbook
from finance_monitor.modules.google_trends_signal.trends import GoogleTrendsSignal
from finance_monitor.modules.strategy_engine.strategy import compute_strategy_score

def test_moving_average_calculation():
    import pandas as pd
    prices = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    result = calculate_moving_averages(prices, short=3, long=5)
    assert 'short_ma' in result and 'long_ma' in result
    assert not result['short_ma'].isnull().all()
    assert not result['long_ma'].isnull().all()

def test_volatility_monitor():
    import pandas as pd
    high = pd.Series([10, 12, 14, 13, 15])
    low = pd.Series([5, 6, 7, 6, 8])
    close = pd.Series([7, 10, 13, 12, 14])
    atr = compute_atr(high, low, close)
    assert atr > 0

def test_orderbook_analysis():
    sample_orderbook = {
        "bids": [[100.0, 2.0], [99.5, 1.5]],
        "asks": [[100.5, 2.5], [101.0, 1.0]]
    }
    score = analyze_orderbook(sample_orderbook)
    assert isinstance(score, float)

def test_google_trends_signal():
    signaler = GoogleTrendsSignal(["Bitcoin", "BTC"])
    score, keywords = signaler.get_signal()
    assert -1.0 <= score <= 1.0
    assert isinstance(keywords, list)

def test_strategy_engine():
    tech, sent, book = 0.3, 0.2, -0.1
    keywords = ["Ethereum", "ETH"]
    score, keywords_hit = compute_strategy_score(tech, sent, book, keywords)
    assert isinstance(score, float)
    assert -1.0 <= score <= 1.0
