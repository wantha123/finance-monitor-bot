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
            greeting = "Bonjour ! Voici votre point
