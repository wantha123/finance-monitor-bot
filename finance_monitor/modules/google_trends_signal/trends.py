
from pytrends.request import TrendReq
from typing import List, Tuple

class GoogleTrendsSignal:
    def __init__(self, keywords: List[str]):
        self.keywords = keywords
        self.pytrends = TrendReq(hl='en-US', tz=360)

    def fetch_scores(self) -> List[Tuple[str, int]]:
        self.pytrends.build_payload(self.keywords, cat=0, timeframe='now 7-d', geo='', gprop='')
        data = self.pytrends.interest_over_time()
        if data.empty:
            return [(kw, 0) for kw in self.keywords]
        return [(kw, int(data[kw].iloc[-1])) for kw in self.keywords]

    def get_signal(self, threshold: int = 80) -> Tuple[float, List[str]]:
        scores = self.fetch_scores()
        values = [score for _, score in scores]
        triggered_keywords = [kw for kw, val in scores if val >= threshold]
        if not values:
            return 0.0, []
        mean_score = sum(values) / len(values)
        normalized = (mean_score - 50) / 50
        return round(normalized, 3), triggered_keywords
