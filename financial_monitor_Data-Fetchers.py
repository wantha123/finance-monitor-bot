# data/fetchers.py
"""
Wrappers pour les APIs externes : Yahoo Finance, CoinGecko, NewsAPI.
Gestion du cache, conversions devises, rate limiting.
"""

import yfinance as yf
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import time
from core.utils import chunk_list, CRYPTO_ID_MAPPING, safe_get

logger = logging.getLogger(__name__)

class ExchangeRateCache:
    """Cache pour les taux de change."""
    def __init__(self):
        self.usd_to_eur: Optional[float] = None
        self.last_update: Optional[datetime] = None
        self.cache_duration = timedelta(hours=1)
    
    def get_usd_to_eur_rate(self) -> float:
        """Récupère le taux USD/EUR avec cache."""
        now = datetime.now()
        
        if (self.last_update is None or 
            now - self.last_update > self.cache_duration):
            try:
                url = "https://api.exchangerate-api.com/v4/latest/USD"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                self.usd_to_eur = data['rates']['EUR']
                self.last_update = now
                logger.info(f"Taux USD/EUR mis à jour: {self.usd_to_eur:.4f}")
                
            except Exception as e:
                logger.error(f"Erreur récupération taux de change: {e}")
                if self.usd_to_eur is None:
                    self.usd_to_eur = 0.92  # Fallback
        
        return self.usd_to_eur

# Instance globale du cache
exchange_cache = ExchangeRateCache()

class StockFetcher:
    """Récupération des données stocks via Yahoo Finance."""
    
    @staticmethod
    def get_stock_price(symbol: str) -> Optional[Dict[str, Any]]:
        """Récupère le prix d'une action."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d", interval="1m")
            
            if hist.empty:
                logger.warning(f"Pas de données pour {symbol}")
                return None
            
            current_price = float(hist['Close'].iloc[-1])
            prev_close = float(info.get('previousClose', current_price))
            currency = info.get('currency', 'EUR')
            
            # Conversion en EUR si nécessaire
            if currency == 'USD':
                rate = exchange_cache.get_usd_to_eur_rate()
                current_price *= rate
                prev_close *= rate
                currency = 'EUR'
            
            change_percent = ((current_price - prev_close) / prev_close * 100 
                             if prev_close > 0 else 0)
            
            return {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'current_price': current_price,
                'previous_close': prev_close,
                'change_percent': change_percent,
                'volume': int(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0,
                'currency': currency,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération {symbol}: {e}")
            return None

class CryptoFetcher:
    """Récupération des données crypto via CoinGecko."""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache = {}
        self.last_update = None
        self.cache_duration = timedelta(minutes=5)
    
    def get_all_crypto_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """Récupère tous les prix crypto en une seule requête."""
        now = datetime.now()
        
        # Utiliser le cache si récent
        if (self.last_update and 
            now - self.last_update < self.cache_duration):
            logger.info("Utilisation du cache crypto")
            return self.cache
        
        # Mapper les symboles vers CoinGecko IDs
        coingecko_ids = []
        symbol_to_id = {}
        
        for symbol in symbols:
            if symbol in CRYPTO_ID_MAPPING:
                cg_id = CRYPTO_ID_MAPPING[symbol]
                coingecko_ids.append(cg_id)
                symbol_to_id[cg_id] = symbol
        
        logger.info(f"Récupération de {len(coingecko_ids)} cryptos...")
        
        all_data = {}
        
        # Diviser en chunks pour respecter les limites
        for chunk in chunk_list(coingecko_ids, 100):
            try:
                params = {
                    'ids': ','.join(chunk),
                    'vs_currencies': 'usd,eur',
                    'include_24hr_change': 'true',
                    'include_24hr_vol': 'true',
                    'include_market_cap': 'true'
                }
                
                response = requests.get(
                    f"{self.base_url}/simple/price",
                    params=params,
                    timeout=15
                )
                
                if response.status_code == 429:
                    logger.warning("Rate limit CoinGecko, attente...")
                    time.sleep(10)
                    continue
                
                response.raise_for_status()
                chunk_data = response.json()
                all_data.update(chunk_data)
                
                time.sleep(2)  # Respecter le rate limit
                
            except Exception as e:
                logger.error(f"Erreur CoinGecko: {e}")
        
        # Convertir au format attendu
        crypto_data = {}
        rate = exchange_cache.get_usd_to_eur_rate()
        
        for cg_id, data in all_data.items():
            if cg_id in symbol_to_id:
                symbol = symbol_to_id[cg_id]
                
                price_eur = data.get('eur')
                if price_eur is None and data.get('usd'):
                    price_eur = data.get('usd') * rate
                
                crypto_data[symbol] = {
                    'symbol': symbol,
                    'current_price_eur': price_eur,
                    'current_price_usd': data.get('usd'),
                    'change_percent_24h': data.get('usd_24h_change', 0),
                    'volume_24h_eur': (data.get('usd_24h_vol', 0) * rate 
                                      if data.get('usd_24h_vol') else None),
                    'market_cap_eur': (data.get('usd_market_cap', 0) * rate
                                      if data.get('usd_market_cap') else None),
                    'timestamp': datetime.now().isoformat()
                }
        
        self.cache = crypto_data
        self.last_update = now
        
        logger.info(f"Récupéré {len(crypto_data)} prix crypto")
        return crypto_data

class NewsFetcher:
    """Récupération des news via NewsAPI."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
    
    def get_news(self, query: str, language: str = 'en') -> List[Dict]:
        """Récupère les dernières news pour une requête."""
        try:
            from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            params = {
                'q': query,
                'from': from_date,
                'language': language,
                'sortBy': 'publishedAt',
                'pageSize': 5,
                'apiKey': self.api_key
            }
            
            response = requests.get(
                f"{self.base_url}/everything",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            articles = response.json().get('articles', [])
            
            return [{
                'title': article.get('title'),
                'source': safe_get(article, 'source', 'name'),
                'published_at': article.get('publishedAt'),
                'url': article.get('url'),
                'description': article.get('description')
            } for article in articles]
            
        except Exception as e:
            logger.error(f"Erreur récupération news pour {query}: {e}")
            return []