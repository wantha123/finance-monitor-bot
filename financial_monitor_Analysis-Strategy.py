# analysis/strategy.py
"""
Stratégies d'analyse et de recommandation basées sur les indicateurs techniques.
Court terme (intraday), moyen terme (swing), long terme (position).
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from enum import Enum

from analysis.indicators import TechnicalIndicators
from core.utils import format_price, format_percent_change

logger = logging.getLogger(__name__)


class TimeFrame(Enum):
    """Horizons temporels d'investissement."""
    INTRADAY = "intraday"       # Quelques heures
    SHORT_TERM = "court_terme"   # 1-5 jours
    MEDIUM_TERM = "moyen_terme"  # 1-4 semaines
    LONG_TERM = "long_terme"     # 1+ mois


class Signal(Enum):
    """Types de signaux de trading."""
    STRONG_BUY = "achat_fort"
    BUY = "achat"
    NEUTRAL = "neutre"
    SELL = "vente"
    STRONG_SELL = "vente_forte"


class TradingStrategy:
    """Stratégies de trading basées sur l'analyse technique."""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def analyze_asset(self, symbol: str, asset_type: str = "stock") -> Dict:
        """
        Analyse complète d'un actif avec recommandations multi-horizons.
        
        Args:
            symbol: Symbole de l'actif
            asset_type: Type d'actif (stock/crypto)
            
        Returns:
            Dict avec analyses et recommandations
        """
        logger.info(f"Analyse stratégique de {symbol}")
        
        # Calculer tous les indicateurs
        indicators = self.indicators.calculate_all_indicators(symbol, days=60)
        
        if not indicators:
            logger.warning(f"Pas assez de données pour analyser {symbol}")
            return {
                'symbol': symbol,
                'error': 'Données insuffisantes',
                'recommendations': {}
            }
        
        # Obtenir les signaux de base
        signals = self.indicators.get_indicator_signals(indicators)
        
        # Analyses par horizon temporel
        analysis = {
            'symbol': symbol,
            'asset_type': asset_type,
            'timestamp': datetime.now().isoformat(),
            'indicators': indicators,
            'signals': signals,
            'recommendations': {}
        }
        
        # Intraday (crypto uniquement ou stocks pendant les heures de marché)
        if asset_type == "crypto" or self._is_market_hours():
            analysis['recommendations'][TimeFrame.INTRADAY] = self._analyze_intraday(indicators, signals)
        
        # Court terme
        analysis['recommendations'][TimeFrame.SHORT_TERM] = self._analyze_short_term(indicators, signals)
        
        # Moyen terme
        analysis['recommendations'][TimeFrame.MEDIUM_TERM] = self._analyze_medium_term(indicators, signals)
        
        # Long terme
        analysis['recommendations'][TimeFrame.LONG_TERM] = self._analyze_long_term(indicators, signals)
        
        # Score global
        analysis['overall_score'] = self._calculate_overall_score(analysis['recommendations'])
        
        return analysis
    
    def _analyze_intraday(self, indicators: Dict, signals: Dict) -> Dict:
        """
        Analyse pour trading intraday (scalping/day trading).
        Basée sur RSI, Stochastique, Bollinger Bands.
        """
        score = 0
        factors = []
        
        # RSI
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            if rsi < 30:
                score += 2
                factors.append(f"RSI survendu ({rsi:.1f})")
            elif rsi > 70:
                score -= 2
                factors.append(f"RSI suracheté ({rsi:.1f})")
            
        # Stochastique
        if 'stoch_k' in indicators:
            stoch = indicators['stoch_k']
            if stoch < 20:
                score += 2
                factors.append(f"Stochastique survendu ({stoch:.1f})")
            elif stoch > 80:
                score -= 2
                factors.append(f"Stochastique suracheté ({stoch:.1f})")
        
        # Position Bollinger
        if 'bb_position' in indicators:
            bb_pos = indicators['bb_position']
            if bb_pos < 0.1:
                score += 2
                factors.append("Prix près de la bande inférieure")
            elif bb_pos > 0.9:
                score -= 2
                factors.append("Prix près de la bande supérieure")
        
        # Volatilité (ATR)
        if 'atr_pct' in indicators:
            if indicators['atr_pct'] > 3:
                factors.append(f"Forte volatilité ({indicators['atr_pct']:.1f}%)")
        
        # Déterminer le signal
        if score >= 4:
            signal = Signal.STRONG_BUY
        elif score >= 2:
            signal = Signal.BUY
        elif score <= -4:
            signal = Signal.STRONG_SELL
        elif score <= -2:
            signal = Signal.SELL
        else:
            signal = Signal.NEUTRAL
        
        return {
            'signal': signal,
            'score': score,
            'factors': factors,
            'timeframe': 'Quelques heures',
            'risk_level': 'Élevé',
            'recommendation': self._get_recommendation_text(signal, TimeFrame.INTRADAY)
        }
    
    def _analyze_short_term(self, indicators: Dict, signals: Dict) -> Dict:
        """
        Analyse court terme (1-5 jours).
        Basée sur MACD, RSI, moyennes mobiles courtes.
        """
        score = 0
        factors = []
        
        # MACD
        if 'macd_bullish' in indicators:
            if indicators['macd_bullish']:
                score += 3
                factors.append("MACD haussier")
            else:
                score -= 3
                factors.append("MACD baissier")
        
        # RSI
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            if 35 <= rsi <= 65:
                factors.append(f"RSI neutre ({rsi:.1f})")
            elif rsi < 35:
                score += 1
                factors.append(f"RSI bas ({rsi:.1f})")
            elif rsi > 65:
                score -= 1
                factors.append(f"RSI élevé ({rsi:.1f})")
        
        # Croisement moyennes mobiles
        if all(k in indicators for k in ['price_current', 'sma_10', 'sma_20']):
            if indicators['sma_10'] > indicators['sma_20']:
                score += 2
                factors.append("SMA10 > SMA20 (tendance haussière)")
            else:
                score -= 2
                factors.append("SMA10 < SMA20 (tendance baissière)")
        
        # Momentum sur 24h
        if 'price_change_24h' in indicators:
            change = indicators['price_change_24h']
            if abs(change) > 5:
                if change > 0:
                    score += 1
                    factors.append(f"Momentum positif 24h ({change:+.1f}%)")
                else:
                    score -= 1
                    factors.append(f"Momentum négatif 24h ({change:+.1f}%)")
        
        # Déterminer le signal
        if score >= 5:
            signal = Signal.STRONG_BUY
        elif score >= 2:
            signal = Signal.BUY
        elif score <= -5:
            signal = Signal.STRONG_SELL
        elif score <= -2:
            signal = Signal.SELL
        else:
            signal = Signal.NEUTRAL
        
        return {
            'signal': signal,
            'score': score,
            'factors': factors,
            'timeframe': '1-5 jours',
            'risk_level': 'Moyen-Élevé',
            'recommendation': self._get_recommendation_text(signal, TimeFrame.SHORT_TERM)
        }
    
    def _analyze_medium_term(self, indicators: Dict, signals: Dict) -> Dict:
        """
        Analyse moyen terme (1-4 semaines).
        Basée sur tendances, supports/résistances, moyennes mobiles.
        """
        score = 0
        factors = []
        
        # Tendance générale (SMA)
        if 'trend' in signals:
            if signals['trend'] == 'buy':
                score += 3
                factors.append("Tendance haussière confirmée")
            elif signals['trend'] == 'sell':
                score -= 3
                factors.append("Tendance baissière confirmée")
        
        # Position par rapport aux moyennes
        if all(k in indicators for k in ['price_current', 'sma_20', 'sma_50']):
            price = indicators['price_current']
            sma20 = indicators['sma_20']
            sma50 = indicators['sma_50'] or sma20
            
            if price > sma20 > sma50:
                score += 2
                factors.append("Prix > SMA20 > SMA50")
            elif price < sma20 < sma50:
                score -= 2
                factors.append("Prix < SMA20 < SMA50")
        
        # Support et résistance
        if all(k in indicators for k in ['price_current', 'support', 'resistance']):
            price = indicators['price_current']
            support = indicators['support']
            resistance = indicators['resistance']
            
            # Position relative
            position = (price - support) / (resistance - support) if resistance > support else 0.5
            
            if position < 0.3:
                score += 2
                factors.append("Prix proche du support")
            elif position > 0.7:
                score -= 1
                factors.append("Prix proche de la résistance")
        
        # Performance sur 7 jours
        if 'price_change_7d' in indicators:
            change = indicators['price_change_7d']
            if change > 10:
                score += 1
                factors.append(f"Performance 7j forte ({change:+.1f}%)")
            elif change < -10:
                score -= 1
                factors.append(f"Performance 7j faible ({change:+.1f}%)")
        
        # Volume (OBV)
        if 'obv_trend' in indicators:
            if indicators['obv_trend'] == 'up':
                score += 1
                factors.append("Volume en hausse (OBV)")
            else:
                score -= 1
                factors.append("Volume en baisse (OBV)")
        
        # Déterminer le signal
        if score >= 6:
            signal = Signal.STRONG_BUY
        elif score >= 3:
            signal = Signal.BUY
        elif score <= -6:
            signal = Signal.STRONG_SELL
        elif score <= -3:
            signal = Signal.SELL
        else:
            signal = Signal.NEUTRAL
        
        return {
            'signal': signal,
            'score': score,
            'factors': factors,
            'timeframe': '1-4 semaines',
            'risk_level': 'Moyen',
            'recommendation': self._get_recommendation_text(signal, TimeFrame.MEDIUM_TERM)
        }
    
    def _analyze_long_term(self, indicators: Dict, signals: Dict) -> Dict:
        """
        Analyse long terme (1+ mois).
        Basée sur tendances de fond, moyennes longues, fondamentaux.
        """
        score = 0
        factors = []
        
        # Tendance long terme
        if 'sma_50' in indicators and indicators['sma_50']:
            if indicators['price_current'] > indicators['sma_50']:
                score += 3
                factors.append("Prix au-dessus de SMA50")
            else:
                score -= 3
                factors.append("Prix en-dessous de SMA50")
        
        # Performance globale
        if all(k in indicators for k in ['price_change_7d', 'price_change_24h']):
            # Moyenne pondérée des performances
            perf_score = (indicators['price_change_7d'] * 0.7 + indicators['price_change_24h'] * 0.3)
            
            if perf_score > 5:
                score += 2
                factors.append("Performance positive soutenue")
            elif perf_score < -5:
                score -= 2
                factors.append("Performance négative persistante")
        
        # Volatilité (pour le risque)
        if 'atr_pct' in indicators:
            if indicators['atr_pct'] < 2:
                factors.append("Volatilité faible (bon pour long terme)")
            elif indicators['atr_pct'] > 5:
                factors.append("Volatilité élevée (risqué)")
                score -= 1
        
        # RSI moyen terme
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            if 40 <= rsi <= 60:
                score += 1
                factors.append("RSI équilibré")
            elif rsi < 30 or rsi > 70:
                factors.append("RSI extrême (attention)")
        
        # Consensus des autres timeframes
        # (En production, on pourrait ajouter des données fondamentales ici)
        
        # Déterminer le signal
        if score >= 4:
            signal = Signal.STRONG_BUY
        elif score >= 2:
            signal = Signal.BUY
        elif score <= -4:
            signal = Signal.STRONG_SELL
        elif score <= -2:
            signal = Signal.SELL
        else:
            signal = Signal.NEUTRAL
        
        return {
            'signal': signal,
            'score': score,
            'factors': factors,
            'timeframe': '1+ mois',
            'risk_level': 'Faible-Moyen',
            'recommendation': self._get_recommendation_text(signal, TimeFrame.LONG_TERM)
        }
    
    def _calculate_overall_score(self, recommendations: Dict) -> Dict:
        """Calcule un score global basé sur toutes les analyses."""
        scores = []
        weights = {
            TimeFrame.INTRADAY: 0.1,
            TimeFrame.SHORT_TERM: 0.25,
            TimeFrame.MEDIUM_TERM: 0.35,
            TimeFrame.LONG_TERM: 0.3
        }
        
        weighted_score = 0
        total_weight = 0
        
        for timeframe, analysis in recommendations.items():
            if 'score' in analysis:
                weight = weights.get(timeframe, 0.25)
                weighted_score += analysis['score'] * weight
                total_weight += weight
        
        final_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # Déterminer la recommandation globale
        if final_score >= 3:
            overall_signal = Signal.STRONG_BUY
        elif final_score >= 1:
            overall_signal = Signal.BUY
        elif final_score <= -3:
            overall_signal = Signal.STRONG_SELL
        elif final_score <= -1:
            overall_signal = Signal.SELL
        else:
            overall_signal = Signal.NEUTRAL
        
        return {
            'score': final_score,
            'signal': overall_signal,
            'confidence': self._calculate_confidence(recommendations)
        }
    
    def _calculate_confidence(self, recommendations: Dict) -> str:
        """Calcule le niveau de confiance basé sur la cohérence des signaux."""
        signals = [r.get('signal') for r in recommendations.values() if 'signal' in r]
        
        if not signals:
            return "Faible"
        
        # Compter les types de signaux
        buy_signals = sum(1 for s in signals if s in [Signal.BUY, Signal.STRONG_BUY])
        sell_signals = sum(1 for s in signals if s in [Signal.SELL, Signal.STRONG_SELL])
        
        # Cohérence
        if buy_signals == len(signals) or sell_signals == len(signals):
            return "Très élevée"
        elif buy_signals >= len(signals) * 0.75 or sell_signals >= len(signals) * 0.75:
            return "Élevée"
        elif buy_signals >= len(signals) * 0.5 or sell_signals >= len(signals) * 0.5:
            return "Moyenne"
        else:
            return "Faible"
    
    def _get_recommendation_text(self, signal: Signal, timeframe: TimeFrame) -> str:
        """Génère un texte de recommandation selon le signal et l'horizon."""
        recommendations = {
            Signal.STRONG_BUY: {
                TimeFrame.INTRADAY: "🟢 Opportunité d'achat immédiate - Surveillez de près",
                TimeFrame.SHORT_TERM: "🟢 Fort potentiel haussier à court terme",
                TimeFrame.MEDIUM_TERM: "🟢 Excellente opportunité d'entrée pour swing trading",
                TimeFrame.LONG_TERM: "🟢 Très bon point d'entrée pour investissement"
            },
            Signal.BUY: {
                TimeFrame.INTRADAY: "🟡 Légèrement haussier - Prudence recommandée",
                TimeFrame.SHORT_TERM: "🟡 Potentiel haussier modéré",
                TimeFrame.MEDIUM_TERM: "🟡 Tendance positive, surveillez l'évolution",
                TimeFrame.LONG_TERM: "🟡 Perspective favorable à long terme"
            },
            Signal.NEUTRAL: {
                TimeFrame.INTRADAY: "⚪ Pas de signal clair - Attendre",
                TimeFrame.SHORT_TERM: "⚪ Marché indécis - Patience recommandée",
                TimeFrame.MEDIUM_TERM: "⚪ Consolidation en cours - Observer",
                TimeFrame.LONG_TERM: "⚪ Tendance neutre - Pas d'urgence"
            },
            Signal.SELL: {
                TimeFrame.INTRADAY: "🟠 Légèrement baissier - Envisager des prises de profit",
                TimeFrame.SHORT_TERM: "🟠 Pression vendeuse modérée",
                TimeFrame.MEDIUM_TERM: "🟠 Tendance négative, prudence",
                TimeFrame.LONG_TERM: "🟠 Réviser la position si détenue"
            },
            Signal.STRONG_SELL: {
                TimeFrame.INTRADAY: "🔴 Signal de vente fort - Sortie recommandée",
                TimeFrame.SHORT_TERM: "🔴 Fort potentiel baissier imminent",
                TimeFrame.MEDIUM_TERM: "🔴 Tendance baissière confirmée - Éviter",
                TimeFrame.LONG_TERM: "🔴 Perspectives négatives - Ne pas investir"
            }
        }
        
        return recommendations.get(signal, {}).get(timeframe, "Signal non défini")
    
    def _is_market_hours(self) -> bool:
        """Vérifie si les marchés sont ouverts pour le trading intraday."""
        from core.utils import is_euronext_open
        return is_euronext_open()
    
    def generate_strategy_report(self, analyses: List[Dict]) -> str:
        """
        Génère un rapport de stratégie pour plusieurs actifs.
        
        Args:
            analyses: Liste des analyses d'actifs
            
        Returns:
            Rapport formaté en texte
        """
        lines = [
            "📊 RAPPORT D'ANALYSE STRATÉGIQUE",
            "=" * 60,
            f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "",
            "🎯 RÉSUMÉ DES RECOMMANDATIONS",
            "-" * 40
        ]
        
        # Trier par score global
        analyses_sorted = sorted(
            analyses,
            key=lambda x: x.get('overall_score', {}).get('score', 0),
            reverse=True
        )
        
        # Top opportunités
        strong_buys = [a for a in analyses_sorted 
                      if a.get('overall_score', {}).get('signal') == Signal.STRONG_BUY]
        
        if strong_buys:
            lines.append("\n🟢 FORTES OPPORTUNITÉS D'ACHAT:")
            for analysis in strong_buys[:5]:
                symbol = analysis['symbol']
                score = analysis['overall_score']['score']
                confidence = analysis['overall_score']['confidence']
                lines.append(f"  • {symbol}: Score {score:.1f} - Confiance: {confidence}")
        
        # Alertes de vente
        strong_sells = [a for a in analyses_sorted 
                       if a.get('overall_score', {}).get('signal') == Signal.STRONG_SELL]
        
        if strong_sells:
            lines.append("\n🔴 ALERTES DE VENTE:")
            for analysis in strong_sells[:5]:
                symbol = analysis['symbol']
                score = analysis['overall_score']['score']
                confidence = analysis['overall_score']['confidence']
                lines.append(f"  • {symbol}: Score {score:.1f} - Confiance: {confidence}")
        
        # Détails par actif (top 10)
        lines.append("\n\n📈 ANALYSES DÉTAILLÉES")
        lines.append("=" * 60)
        
        for analysis in analyses_sorted[:10]:
            lines.extend(self._format_asset_analysis(analysis))
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_asset_analysis(self, analysis: Dict) -> List[str]:
        """Formate l'analyse d'un actif pour le rapport."""
        lines = []
        
        symbol = analysis['symbol']
        asset_type = analysis['asset_type']
        overall = analysis.get('overall_score', {})
        
        # En-tête
        emoji = "🏢" if asset_type == "stock" else "🪙"
        lines.append(f"\n{emoji} {symbol}")
        lines.append("-" * 30)
        
        # Score global
        if overall:
            signal_emoji = self._get_signal_emoji(overall.get('signal'))
            lines.append(f"Score global: {overall['score']:.1f} {signal_emoji}")
            lines.append(f"Confiance: {overall['confidence']}")
        
        # Indicateurs clés
        indicators = analysis.get('indicators', {})
        if indicators:
            lines.append("\nIndicateurs clés:")
            
            if 'rsi' in indicators:
                lines.append(f"  • RSI: {indicators['rsi']:.1f}")
            
            if 'price_change_24h' in indicators:
                lines.append(f"  • Variation 24h: {indicators['price_change_24h']:+.1f}%")
            
            if 'price_change_7d' in indicators:
                lines.append(f"  • Variation 7j: {indicators['price_change_7d']:+.1f}%")
        
        # Recommandations par horizon
        recommendations = analysis.get('recommendations', {})
        if recommendations:
            lines.append("\nRecommandations:")
            
            for timeframe in [TimeFrame.SHORT_TERM, TimeFrame.MEDIUM_TERM, TimeFrame.LONG_TERM]:
                if timeframe in recommendations:
                    rec = recommendations[timeframe]
                    signal_emoji = self._get_signal_emoji(rec.get('signal'))
                    lines.append(f"  • {rec['timeframe']}: {signal_emoji} {rec['recommendation']}")
        
        return lines
    
    def _get_signal_emoji(self, signal: Signal) -> str:
        """Retourne l'emoji correspondant au signal."""
        emoji_map = {
            Signal.STRONG_BUY: "🟢🟢",
            Signal.BUY: "🟢",
            Signal.NEUTRAL: "⚪",
            Signal.SELL: "🔴",
            Signal.STRONG_SELL: "🔴🔴"
        }
        return emoji_map.get(signal, "❓")


class PortfolioOptimizer:
    """
    Optimise la répartition du portfolio basée sur les analyses.
    (Extension future pour la gestion de portfolio)
    """
    
    def __init__(self, strategy: TradingStrategy):
        self.strategy = strategy
    
    def optimize_allocation(self, portfolio: Dict[str, float], 
                          analyses: List[Dict], 
                          total_capital: float) -> Dict[str, float]:
        """
        Suggère une allocation optimale du capital.
        
        Args:
            portfolio: Portfolio actuel {symbol: quantité}
            analyses: Analyses de tous les actifs
            total_capital: Capital total disponible
            
        Returns:
            Nouvelle allocation suggérée
        """
        # TODO: Implémenter l'optimisation de portfolio
        # - Diversification
        # - Risk management
        # - Rebalancing
        # - Tax optimization
        
        return portfolio
    
    def calculate_risk_metrics(self, portfolio: Dict[str, float]) -> Dict:
        """
        Calcule les métriques de risque du portfolio.
        
        Returns:
            Value at Risk, Sharpe Ratio, Beta, etc.
        """
        # TODO: Implémenter les calculs de risque
        return {
            'var_95': 0.0,
            'sharpe_ratio': 0.0,
            'beta': 0.0,
            'max_drawdown': 0.0
        }