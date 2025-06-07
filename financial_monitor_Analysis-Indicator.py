# analysis/indicators.py
"""
Calcul des indicateurs techniques pour l'analyse financière.
RSI, moyennes mobiles, bandes de Bollinger, MACD, etc.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime, timedelta
import sqlite3
from data.database import DB_PATH

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calcule différents indicateurs techniques sur les données de prix."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
    
    def get_price_history(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """
        Récupère l'historique des prix depuis la base de données.
        Retourne un DataFrame pandas avec colonnes: timestamp, price.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Récupérer les données des N derniers jours
            since_date = datetime.now() - timedelta(days=days)
            
            query = """
                SELECT timestamp, price 
                FROM price_history 
                WHERE symbol = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """
            
            df = pd.read_sql_query(
                query, 
                conn, 
                params=(symbol, since_date.isoformat()),
                parse_dates=['timestamp']
            )
            
            conn.close()
            
            if df.empty:
                logger.warning(f"Pas d'historique pour {symbol} sur {days} jours")
                return pd.DataFrame()
            
            # Définir timestamp comme index
            df.set_index('timestamp', inplace=True)
            
            # Resampler à intervalles réguliers (1H) et forward-fill
            df = df.resample('1H').last().ffill()
            
            return df
            
        except Exception as e:
            logger.error(f"Erreur récupération historique {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calcule la moyenne mobile simple (SMA).
        
        Args:
            prices: Série des prix
            period: Nombre de périodes pour la moyenne
            
        Returns:
            Série des valeurs SMA
        """
        return prices.rolling(window=period).mean()
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calcule la moyenne mobile exponentielle (EMA).
        
        Args:
            prices: Série des prix
            period: Nombre de périodes pour la moyenne
            
        Returns:
            Série des valeurs EMA
        """
        return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calcule le Relative Strength Index (RSI).
        
        RSI = 100 - (100 / (1 + RS))
        RS = Moyenne des gains / Moyenne des pertes
        
        Args:
            prices: Série des prix
            period: Période de calcul (défaut: 14)
            
        Returns:
            Série des valeurs RSI (0-100)
        """
        if len(prices) < period + 1:
            return pd.Series(dtype=float)
        
        # Calculer les variations
        delta = prices.diff()
        
        # Séparer gains et pertes
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Moyennes mobiles des gains et pertes
        avg_gains = gains.rolling(window=period).mean()
        avg_losses = losses.rolling(window=period).mean()
        
        # Relative Strength
        rs = avg_gains / avg_losses
        
        # RSI
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_bollinger_bands(self, prices: pd.Series, 
                                 period: int = 20, 
                                 std_dev: float = 2) -> Dict[str, pd.Series]:
        """
        Calcule les bandes de Bollinger.
        
        Args:
            prices: Série des prix
            period: Période pour la SMA (défaut: 20)
            std_dev: Nombre d'écarts-types (défaut: 2)
            
        Returns:
            Dict avec 'upper', 'middle', 'lower' bands
        """
        # Bande du milieu = SMA
        middle_band = self.calculate_sma(prices, period)
        
        # Écart-type mobile
        rolling_std = prices.rolling(window=period).std()
        
        # Bandes supérieure et inférieure
        upper_band = middle_band + (std_dev * rolling_std)
        lower_band = middle_band - (std_dev * rolling_std)
        
        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band
        }
    
    def calculate_macd(self, prices: pd.Series,
                      fast_period: int = 12,
                      slow_period: int = 26,
                      signal_period: int = 9) -> Dict[str, pd.Series]:
        """
        Calcule le MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Série des prix
            fast_period: Période courte (défaut: 12)
            slow_period: Période longue (défaut: 26)
            signal_period: Période du signal (défaut: 9)
            
        Returns:
            Dict avec 'macd', 'signal', 'histogram'
        """
        # EMA rapide et lente
        ema_fast = self.calculate_ema(prices, fast_period)
        ema_slow = self.calculate_ema(prices, slow_period)
        
        # Ligne MACD
        macd_line = ema_fast - ema_slow
        
        # Ligne de signal
        signal_line = self.calculate_ema(macd_line, signal_period)
        
        # Histogramme
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series,
                           k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """
        Calcule l'oscillateur stochastique.
        
        Args:
            high: Série des plus hauts
            low: Série des plus bas
            close: Série des clôtures
            k_period: Période pour %K (défaut: 14)
            d_period: Période pour %D (défaut: 3)
            
        Returns:
            Dict avec '%K' et '%D'
        """
        # Plus bas et plus haut sur la période
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        # %K
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        
        # %D (moyenne mobile de %K)
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            '%K': k_percent,
            '%D': d_percent
        }
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series,
                     period: int = 14) -> pd.Series:
        """
        Calcule l'Average True Range (ATR) - mesure de volatilité.
        
        Args:
            high: Série des plus hauts
            low: Série des plus bas
            close: Série des clôtures
            period: Période de calcul (défaut: 14)
            
        Returns:
            Série des valeurs ATR
        """
        # True Range
        high_low = high - low
        high_close = abs(high - close.shift(1))
        low_close = abs(low - close.shift(1))
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # ATR = moyenne mobile du True Range
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    def calculate_obv(self, prices: pd.Series, volumes: pd.Series) -> pd.Series:
        """
        Calcule l'On-Balance Volume (OBV).
        
        Args:
            prices: Série des prix
            volumes: Série des volumes
            
        Returns:
            Série des valeurs OBV
        """
        # Direction du prix (1 si hausse, -1 si baisse, 0 si stable)
        price_direction = np.sign(prices.diff())
        
        # Volume signé
        signed_volume = volumes * price_direction
        
        # OBV = somme cumulative
        obv = signed_volume.cumsum()
        
        return obv
    
    def calculate_all_indicators(self, symbol: str, days: int = 30) -> Dict[str, any]:
        """
        Calcule tous les indicateurs disponibles pour un symbole.
        
        Args:
            symbol: Symbole de l'actif
            days: Nombre de jours d'historique
            
        Returns:
            Dict avec tous les indicateurs calculés
        """
        logger.info(f"Calcul des indicateurs pour {symbol} sur {days} jours")
        
        # Récupérer l'historique
        df = self.get_price_history(symbol, days)
        
        if df.empty:
            return {}
        
        prices = df['price']
        
        # Pour certains indicateurs, on simule high/low/volume
        # En production, il faudrait récupérer ces données réelles
        high = prices * 1.01  # Simulation
        low = prices * 0.99   # Simulation
        volumes = pd.Series(100000, index=prices.index)  # Volume fixe simulé
        
        indicators = {}
        
        try:
            # Moyennes mobiles
            indicators['sma_10'] = self.calculate_sma(prices, 10).iloc[-1]
            indicators['sma_20'] = self.calculate_sma(prices, 20).iloc[-1]
            indicators['sma_50'] = self.calculate_sma(prices, 50).iloc[-1] if len(prices) >= 50 else None
            
            indicators['ema_10'] = self.calculate_ema(prices, 10).iloc[-1]
            indicators['ema_20'] = self.calculate_ema(prices, 20).iloc[-1]
            
            # RSI
            rsi_values = self.calculate_rsi(prices)
            if not rsi_values.empty:
                indicators['rsi'] = rsi_values.iloc[-1]
                indicators['rsi_oversold'] = indicators['rsi'] < 30
                indicators['rsi_overbought'] = indicators['rsi'] > 70
            
            # Bandes de Bollinger
            bb = self.calculate_bollinger_bands(prices)
            if not bb['upper'].empty:
                indicators['bb_upper'] = bb['upper'].iloc[-1]
                indicators['bb_middle'] = bb['middle'].iloc[-1]
                indicators['bb_lower'] = bb['lower'].iloc[-1]
                
                # Position du prix par rapport aux bandes
                current_price = prices.iloc[-1]
                bb_position = (current_price - bb['lower'].iloc[-1]) / (bb['upper'].iloc[-1] - bb['lower'].iloc[-1])
                indicators['bb_position'] = bb_position  # 0 = bande basse, 1 = bande haute
            
            # MACD
            macd = self.calculate_macd(prices)
            if not macd['macd'].empty:
                indicators['macd'] = macd['macd'].iloc[-1]
                indicators['macd_signal'] = macd['signal'].iloc[-1]
                indicators['macd_histogram'] = macd['histogram'].iloc[-1]
                indicators['macd_bullish'] = indicators['macd'] > indicators['macd_signal']
            
            # Stochastique
            stoch = self.calculate_stochastic(high, low, prices)
            if not stoch['%K'].empty:
                indicators['stoch_k'] = stoch['%K'].iloc[-1]
                indicators['stoch_d'] = stoch['%D'].iloc[-1]
                indicators['stoch_oversold'] = indicators['stoch_k'] < 20
                indicators['stoch_overbought'] = indicators['stoch_k'] > 80
            
            # ATR (volatilité)
            atr_values = self.calculate_atr(high, low, prices)
            if not atr_values.empty:
                indicators['atr'] = atr_values.iloc[-1]
                indicators['atr_pct'] = (indicators['atr'] / prices.iloc[-1]) * 100
            
            # OBV
            obv_values = self.calculate_obv(prices, volumes)
            if not obv_values.empty:
                indicators['obv'] = obv_values.iloc[-1]
                indicators['obv_trend'] = 'up' if obv_values.iloc[-1] > obv_values.iloc[-5] else 'down'
            
            # Tendances générales
            indicators['price_current'] = prices.iloc[-1]
            indicators['price_change_24h'] = ((prices.iloc[-1] - prices.iloc[-24]) / prices.iloc[-24] * 100) if len(prices) > 24 else 0
            indicators['price_change_7d'] = ((prices.iloc[-1] - prices.iloc[-168]) / prices.iloc[-168] * 100) if len(prices) > 168 else 0
            
            # Support et résistance simples
            indicators['support'] = prices.tail(20).min()
            indicators['resistance'] = prices.tail(20).max()
            
        except Exception as e:
            logger.error(f"Erreur calcul indicateurs pour {symbol}: {e}")
        
        return indicators
    
    def get_indicator_signals(self, indicators: Dict) -> Dict[str, str]:
        """
        Interprète les indicateurs pour générer des signaux simples.
        
        Args:
            indicators: Dict des indicateurs calculés
            
        Returns:
            Dict des signaux (buy/sell/neutral)
        """
        signals = {}
        
        # Signal RSI
        if 'rsi' in indicators:
            if indicators.get('rsi_oversold'):
                signals['rsi'] = 'buy'
            elif indicators.get('rsi_overbought'):
                signals['rsi'] = 'sell'
            else:
                signals['rsi'] = 'neutral'
        
        # Signal MACD
        if 'macd_bullish' in indicators:
            signals['macd'] = 'buy' if indicators['macd_bullish'] else 'sell'
        
        # Signal Bollinger
        if 'bb_position' in indicators:
            if indicators['bb_position'] < 0.2:
                signals['bollinger'] = 'buy'
            elif indicators['bb_position'] > 0.8:
                signals['bollinger'] = 'sell'
            else:
                signals['bollinger'] = 'neutral'
        
        # Signal Stochastique
        if 'stoch_k' in indicators:
            if indicators.get('stoch_oversold'):
                signals['stochastic'] = 'buy'
            elif indicators.get('stoch_overbought'):
                signals['stochastic'] = 'sell'
            else:
                signals['stochastic'] = 'neutral'
        
        # Signal de tendance (moyennes mobiles)
        if all(k in indicators for k in ['price_current', 'sma_20', 'sma_50']):
            if indicators['sma_50']:  # Si on a assez de données
                if (indicators['price_current'] > indicators['sma_20'] > indicators['sma_50']):
                    signals['trend'] = 'buy'
                elif (indicators['price_current'] < indicators['sma_20'] < indicators['sma_50']):
                    signals['trend'] = 'sell'
                else:
                    signals['trend'] = 'neutral'
        
        # Signal global (consensus)
        buy_signals = sum(1 for s in signals.values() if s == 'buy')
        sell_signals = sum(1 for s in signals.values() if s == 'sell')
        
        if buy_signals > sell_signals and buy_signals >= 2:
            signals['consensus'] = 'buy'
        elif sell_signals > buy_signals and sell_signals >= 2:
            signals['consensus'] = 'sell'
        else:
            signals['consensus'] = 'neutral'
        
        return signals