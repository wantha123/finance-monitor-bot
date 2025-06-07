# core/alerting.py
"""
Module de gestion des alertes : vérification des seuils,
formatage des messages, préparation pour email/Slack.
"""

from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging
from core.utils import (
    format_price, format_percent_change, 
    get_trend_emoji, get_asset_emoji
)

logger = logging.getLogger(__name__)

class AlertChecker:
    """Vérifie les seuils et génère les alertes."""
    
    def __init__(self, thresholds: Dict[str, Dict]):
        self.thresholds = thresholds
    
    def check_price_alerts(
        self, 
        symbol: str, 
        current_price: float, 
        previous_price: float,
        asset_type: str = "crypto"
    ) -> List[Dict]:
        """
        Vérifie si le prix déclenche des alertes selon les seuils.
        Retourne une liste d'alertes structurées.
        """
        alerts = []
        
        if symbol not in self.thresholds:
            return alerts
        
        threshold = self.thresholds[symbol]
        
        # Calcul du changement
        change_percent = 0
        if previous_price > 0:
            change_percent = ((current_price - previous_price) / previous_price) * 100
        
        # Alerte seuil haut
        if current_price >= threshold.get('high', float('inf')):
            alerts.append({
                'type': 'HIGH_THRESHOLD',
                'symbol': symbol,
                'current_price': current_price,
                'previous_price': previous_price,
                'threshold': threshold['high'],
                'change_percent': change_percent,
                'asset_type': asset_type,
                'emoji': '🔴',
                'severity': 'high'
            })
        
        # Alerte seuil bas
        if current_price <= threshold.get('low', 0):
            alerts.append({
                'type': 'LOW_THRESHOLD',
                'symbol': symbol,
                'current_price': current_price,
                'previous_price': previous_price,
                'threshold': threshold['low'],
                'change_percent': change_percent,
                'asset_type': asset_type,
                'emoji': '🔵',
                'severity': 'high'
            })
        
        # Alerte mouvement significatif
        if abs(change_percent) >= threshold.get('change_percent', 10):
            alerts.append({
                'type': 'SIGNIFICANT_MOVE',
                'symbol': symbol,
                'current_price': current_price,
                'previous_price': previous_price,
                'change_percent': change_percent,
                'asset_type': asset_type,
                'emoji': '⚡',
                'severity': 'medium'
            })
        
        return alerts

class AlertFormatter:
    """Formate les alertes pour différents canaux."""
    
    @staticmethod
    def format_alert_simple(alert: Dict) -> str:
        """Format simple pour logs ou Slack."""
        emoji = alert['emoji']
        asset_emoji = get_asset_emoji(alert['asset_type'])
        symbol = alert['symbol']
        
        if alert['type'] == 'HIGH_THRESHOLD':
            return (f"{emoji} {asset_emoji} {symbol} - Seuil HAUT atteint: "
                   f"{format_price(alert['current_price'])} "
                   f"(seuil: {format_price(alert['threshold'])})")
        
        elif alert['type'] == 'LOW_THRESHOLD':
            return (f"{emoji} {asset_emoji} {symbol} - Seuil BAS atteint: "
                   f"{format_price(alert['current_price'])} "
                   f"(seuil: {format_price(alert['threshold'])})")
        
        else:  # SIGNIFICANT_MOVE
            trend = get_trend_emoji(alert['change_percent'])
            return (f"{emoji} {asset_emoji} {symbol} - Mouvement significatif: "
                   f"{trend} {alert['change_percent']:+.2f}%")
    
    @staticmethod
    def format_alert_detailed(alert: Dict, asset_name: str) -> str:
        """Format détaillé avec before/after pour emails."""
        emoji = alert['emoji']
        asset_emoji = get_asset_emoji(alert['asset_type'])
        
        lines = [
            f"{emoji} {alert['type'].replace('_', ' ').title()}",
            f"{asset_emoji} {asset_name} ({alert['symbol']})",
            f"💰 {format_price(alert['previous_price'])} → {format_price(alert['current_price'])}",
            f"{get_trend_emoji(alert['change_percent'])} {alert['change_percent']:+.2f}%"
        ]
        
        return "\n".join(lines)
    
    @staticmethod
    def format_alert_html(alert: Dict, asset_name: str) -> str:
        """Format HTML pour emails riches."""
        color_map = {
            'HIGH_THRESHOLD': '#dc3545',
            'LOW_THRESHOLD': '#17a2b8', 
            'SIGNIFICANT_MOVE': '#ffc107'
        }
        
        color = color_map.get(alert['type'], '#6c757d')
        change_class = 'gain' if alert['change_percent'] > 0 else 'loss'
        
        return f"""
        <div class="alert-box" style="border-left-color: {color};">
            <h3>{alert['emoji']} {alert['type'].replace('_', ' ').title()}</h3>
            <div class="asset-info">
                <strong>{asset_name} ({alert['symbol']})</strong>
            </div>
            <div class="price-info">
                <span class="before">{format_price(alert['previous_price'])}</span>
                <span class="arrow">→</span>
                <span class="after">{format_price(alert['current_price'])}</span>
            </div>
            <div class="change {change_class}">
                {format_percent_change(alert['change_percent'])}
            </div>
        </div>
        """

class AlertAggregator:
    """Agrège et priorise les alertes."""
    
    def __init__(self):
        self.alerts = []
    
    def add_alerts(self, alerts: List[Dict]):
        """Ajoute des alertes à la liste."""
        self.alerts.extend(alerts)
    
    def get_grouped_alerts(self) -> Dict[str, List[Dict]]:
        """Groupe les alertes par type."""
        grouped = {
            'HIGH_THRESHOLD': [],
            'LOW_THRESHOLD': [],
            'SIGNIFICANT_MOVE': []
        }
        
        for alert in self.alerts:
            alert_type = alert['type']
            if alert_type in grouped:
                grouped[alert_type].append(alert)
        
        return grouped
    
    def get_summary(self) -> Dict:
        """Résumé des alertes pour décision d'envoi."""
        return {
            'total': len(self.alerts),
            'high_severity': len([a for a in self.alerts if a['severity'] == 'high']),
            'by_type': {
                alert_type: len(alerts) 
                for alert_type, alerts in self.get_grouped_alerts().items()
            }
        }
    
    def should_send_notification(self) -> bool:
        """Détermine si on doit envoyer une notification."""
        # Envoyer si au moins une alerte haute sévérité
        return any(a['severity'] == 'high' for a in self.alerts)
    
    def clear(self):
        """Vide la liste des alertes."""
        self.alerts = []