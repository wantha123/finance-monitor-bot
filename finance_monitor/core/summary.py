# core/summary.py
"""
Génération des rapports quotidiens : snapshots portfolio,
top/flop performers, statistiques.
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from collections import defaultdict
from core.utils import (
    format_price, format_percent_change,
    get_asset_emoji, get_paris_time
)

logger = logging.getLogger(__name__)

class PortfolioSummary:
    """Génère les résumés de portfolio."""
    
    def __init__(self, stocks_data: Dict, crypto_data: Dict):
        self.stocks_data = stocks_data
        self.crypto_data = crypto_data
        self.all_assets = self._combine_assets()
    
    def _combine_assets(self) -> List[Dict]:
        """Combine stocks et crypto dans une liste unifiée."""
        assets = []
        
        # Ajouter les stocks
        for symbol, data in self.stocks_data.items():
            if data:
                assets.append({
                    'symbol': symbol,
                    'name': data.get('name', symbol),
                    'price': data['current_price'],
                    'change': data.get('change_percent', 0),
                    'type': 'stock',
                    'emoji': '🏢',
                    'volume': data.get('volume', 0)
                })
        
        # Ajouter les cryptos
        for symbol, data in self.crypto_data.items():
            if data and data.get('current_price_eur'):
                assets.append({
                    'symbol': symbol,
                    'name': symbol,  # À enrichir depuis CONFIG
                    'price': data['current_price_eur'],
                    'change': data.get('change_percent_24h', 0),
                    'type': 'crypto',
                    'emoji': '🪙',
                    'volume': data.get('volume_24h_eur', 0)
                })
        
        return assets
    
    def get_top_performers(self, limit: int = 5) -> List[Dict]:
        """Retourne les meilleures performances."""
        sorted_assets = sorted(
            self.all_assets, 
            key=lambda x: x['change'], 
            reverse=True
        )
        return sorted_assets[:limit]
    
    def get_worst_performers(self, limit: int = 5) -> List[Dict]:
        """Retourne les pires performances."""
        sorted_assets = sorted(
            self.all_assets, 
            key=lambda x: x['change']
        )
        return sorted_assets[:limit]
    
    def get_biggest_movers(self, limit: int = 5) -> List[Dict]:
        """Retourne les plus gros mouvements (absolus)."""
        sorted_assets = sorted(
            self.all_assets,
            key=lambda x: abs(x['change']),
            reverse=True
        )
        return sorted_assets[:limit]
    
    def get_statistics(self) -> Dict:
        """Calcule les statistiques du portfolio."""
        if not self.all_assets:
            return {
                'total_assets': 0,
                'gainers': 0,
                'losers': 0,
                'unchanged': 0,
                'stocks_count': 0,
                'crypto_count': 0
            }
        
        gainers = len([a for a in self.all_assets if a['change'] > 0])
        losers = len([a for a in self.all_assets if a['change'] < 0])
        unchanged = len(self.all_assets) - gainers - losers
        
        stocks_count = len([a for a in self.all_assets if a['type'] == 'stock'])
        crypto_count = len([a for a in self.all_assets if a['type'] == 'crypto'])
        
        return {
            'total_assets': len(self.all_assets),
            'gainers': gainers,
            'gainers_pct': (gainers / len(self.all_assets) * 100) if self.all_assets else 0,
            'losers': losers,
            'losers_pct': (losers / len(self.all_assets) * 100) if self.all_assets else 0,
            'unchanged': unchanged,
            'unchanged_pct': (unchanged / len(self.all_assets) * 100) if self.all_assets else 0,
            'stocks_count': stocks_count,
            'crypto_count': crypto_count
        }
    
    def get_market_status(self) -> List[str]:
        """Retourne le statut des marchés."""
        from core.utils import is_euronext_open, get_next_market_open
        
        status = []
        
        if is_euronext_open():
            status.append("🟢 Euronext Paris: OUVERT")
        else:
            next_open = get_next_market_open()
            status.append(f"🔴 Euronext Paris: FERMÉ (prochaine ouverture: {next_open.strftime('%d/%m %H:%M')})")
        
        status.append("🟢 Marchés Crypto: TOUJOURS OUVERTS")
        
        return status

class ReportBuilder:
    """Construit les rapports formatés."""
    
    def __init__(self, summary: PortfolioSummary):
        self.summary = summary
        self.paris_time = get_paris_time()
    
    def build_daily_report(self, report_type: str = "morning") -> Dict[str, str]:
        """
        Construit un rapport quotidien complet.
        Retourne un dict avec 'plain' et 'html' versions.
        """
        is_morning = report_type == "morning"
        
        # En-tête
        if is_morning:
            subject = f"🌅 Rapport Matinal - {self.paris_time.strftime('%d/%m/%Y')}"
            greeting = "Bonjour ! Voici votre point matinal sur les marchés financiers."
        else:
            subject = f"🌆 Rapport du Soir - {self.paris_time.strftime('%d/%m/%Y')}"
            greeting = "Bonsoir ! Voici votre résumé de fin de journée des marchés financiers."
        
        # Obtenir les données
        top_performers = self.summary.get_top_performers(5)
        worst_performers = self.summary.get_worst_performers(5)
        statistics = self.summary.get_statistics()
        market_status = self.summary.get_market_status()
        
        # Version texte brut
        plain_lines = [
            f"{subject}",
            "=" * 60,
            f"📅 {self.paris_time.strftime('%d/%m/%Y %H:%M')} (Paris)",
            "",
            greeting,
            "",
            "📊 STATUT DES MARCHÉS:",
            "-" * 30
        ]
        
        for status in market_status:
            plain_lines.append(f"  {status}")
        
        plain_lines.extend([
            "",
            "📈 TOP PERFORMERS:",
            "-" * 30
        ])
        
        for asset in top_performers:
            plain_lines.append(
                f"  {asset['emoji']} {asset['name']} ({asset['symbol']}): "
                f"{format_price(asset['price'])} {format_percent_change(asset['change'])}"
            )
        
        plain_lines.extend([
            "",
            "📉 WORST PERFORMERS:",
            "-" * 30
        ])
        
        for asset in worst_performers:
            plain_lines.append(
                f"  {asset['emoji']} {asset['name']} ({asset['symbol']}): "
                f"{format_price(asset['price'])} {format_percent_change(asset['change'])}"
            )
        
        if statistics['total_assets'] > 0:
            plain_lines.extend([
                "",
                "📊 STATISTIQUES DU PORTFOLIO:",
                "-" * 30,
                f"  📈 En hausse: {statistics['gainers']} ({statistics['gainers_pct']:.1f}%)",
                f"  📉 En baisse: {statistics['losers']} ({statistics['losers_pct']:.1f}%)",
                f"  ➡️ Inchangés: {statistics['unchanged']} ({statistics['unchanged_pct']:.1f}%)",
                f"  📊 Total actifs: {statistics['total_assets']} ({statistics['stocks_count']} actions + {statistics['crypto_count']} cryptos)"
            ])
        
        plain_lines.extend([
            "",
            "=" * 60,
            "🤖 Finance Monitor Bot - Rapport Quotidien",
            "=" * 60
        ])
        
        plain_text = "\n".join(plain_lines)
        
        # Version HTML (simplifiée)
        html_content = f"""
        <h1>{subject}</h1>
        <p><em>{greeting}</em></p>
        
        <h2>📊 Statut des Marchés</h2>
        <ul>
        """
        
        for status in market_status:
            color = "green" if "OUVERT" in status else "red"
            html_content += f"<li style='color: {color}; font-weight: bold;'>{status}</li>"
        
        html_content += """
        </ul>
        
        <h2>📈 Top Performers</h2>
        <ul>
        """
        
        for asset in top_performers:
            html_content += f"""
            <li style='color: green;'>
                {asset['emoji']} {asset['name']} ({asset['symbol']}): 
                {format_price(asset['price'])} {format_percent_change(asset['change'])}
            </li>
            """
        
        html_content += """
        </ul>
        
        <h2>📉 Worst Performers</h2>
        <ul>
        """
        
        for asset in worst_performers:
            html_content += f"""
            <li style='color: red;'>
                {asset['emoji']} {asset['name']} ({asset['symbol']}): 
                {format_price(asset['price'])} {format_percent_change(asset['change'])}
            </li>
            """
        
        html_content += "</ul>"
        
        if statistics['total_assets'] > 0:
            html_content += f"""
            <h2>📊 Statistiques du Portfolio</h2>
            <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0;'>
                <div style='text-align: center; padding: 15px; background: #e8f5e9; border-radius: 8px;'>
                    <div style='font-size: 24px; font-weight: bold; color: #2e7d32;'>{statistics['gainers']}</div>
                    <div>En hausse ({statistics['gainers_pct']:.1f}%)</div>
                </div>
                <div style='text-align: center; padding: 15px; background: #ffebee; border-radius: 8px;'>
                    <div style='font-size: 24px; font-weight: bold; color: #c62828;'>{statistics['losers']}</div>
                    <div>En baisse ({statistics['losers_pct']:.1f}%)</div>
                </div>
                <div style='text-align: center; padding: 15px; background: #f3e5f5; border-radius: 8px;'>
                    <div style='font-size: 24px; font-weight: bold; color: #7b1fa2;'>{statistics['unchanged']}</div>
                    <div>Inchangés ({statistics['unchanged_pct']:.1f}%)</div>
                </div>
            </div>
            <p><strong>Total:</strong> {statistics['total_assets']} actifs ({statistics['stocks_count']} actions + {statistics['crypto_count']} cryptos)</p>
            """
        
        return {
            'subject': subject,
            'plain': plain_text,
            'html': html_content
        }
    
    def build_alert_summary(self, alerts: List[str], additional_data: Dict = None) -> Dict[str, str]:
        """
        Construit un résumé d'alertes formaté.
        
        Args:
            alerts: Liste des alertes
            additional_data: Données additionnelles (movers, news, etc.)
            
        Returns:
            Dict avec versions texte et HTML
        """
        subject = f"🚨 Alerte Portfolio - {len(alerts)} notification(s)"
        
        # Version texte
        plain_lines = [
            "🚨 ALERTE MONITORING FINANCIER",
            "=" * 50,
            f"📅 {self.paris_time.strftime('%d/%m/%Y %H:%M')} (Paris)",
            "",
            f"🚨 ALERTES DE PRIX ({len(alerts)}):",
            "-" * 30
        ]
        
        for i, alert in enumerate(alerts, 1):
            plain_lines.extend([
                f"\nALERTE #{i}:",
                alert
            ])
        
        # Ajouter les plus gros mouvements si disponibles
        if additional_data and 'biggest_movers' in additional_data:
            plain_lines.extend([
                "",
                "🔥 PLUS GROS MOUVEMENTS:",
                "-" * 30
            ])
            
            for mover in additional_data['biggest_movers'][:5]:
                plain_lines.append(
                    f"  {mover['emoji']} {mover['name']} ({mover['symbol']}): "
                    f"{format_price(mover['price'])} {format_percent_change(mover['change'])}"
                )
        
        plain_lines.extend([
            "",
            "=" * 50,
            "🤖 Finance Monitor Bot"
        ])
        
        plain_text = "\n".join(plain_lines)
        
        # Version HTML basique
        html_content = f"""
        <h1>{subject}</h1>
        <p><em>Généré le {self.paris_time.strftime('%d/%m/%Y à %H:%M')} (Paris)</em></p>
        
        <h2>🚨 Alertes de Prix ({len(alerts)})</h2>
        """
        
        for i, alert in enumerate(alerts, 1):
            html_content += f"""
            <div style='margin: 15px 0; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 5px;'>
                <h3>Alerte #{i}</h3>
                <pre style='white-space: pre-wrap; font-family: inherit;'>{alert}</pre>
            </div>
            """
        
        return {
            'subject': subject,
            'plain': plain_text,
            'html': html_content
        }
