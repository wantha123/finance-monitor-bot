# core/utils.py
"""
Utilitaires partagés pour le monitoring financier.
Gestion des fuseaux horaires, formatage, calculs auxiliaires.
"""

import pytz
from datetime import datetime, timedelta
from typing import Union, Tuple, List
import logging

logger = logging.getLogger(__name__)

# Timezone Euronext Paris
PARIS_TZ = pytz.timezone('Europe/Paris')

# Mapping CoinGecko IDs - VERSION COMPLÈTE avec toutes les 61 cryptomonnaies
CRYPTO_ID_MAPPING = {
    # Top Market Cap
    'ETH': 'ethereum',
    'SOL': 'solana',
    'DOGE': 'dogecoin',
    'ADA': 'cardano',
    'LINK': 'chainlink',
    'ZEC': 'zcash',
    'PEPE': 'pepe',
    'UNI': 'uniswap',
    'CRO': 'crypto-com-chain',
    'MNT': 'mantle',
    'RENDER': 'render-token',
    'FET': 'fetch-ai',
    'ARB': 'arbitrum',
    'FIL': 'filecoin',
    'ALGO': 'algorand',
    'MKR': 'maker',
    'GRT': 'the-graph',
    'ENS': 'ethereum-name-service',
    'GALA': 'gala',
    'FLOW': 'flow',
    'MANA': 'decentraland',
    
    # Layer 2 & New Technologies
    'STRK': 'starknet',
    'EIGEN': 'eigenlayer',
    'EGLD': 'elrond-erd-2',  # MultiversX
    'MOVE': 'move-protocol',
    'LPT': 'livepeer',
    'MOG': 'mog-coin',
    'MASK': 'mask-network',
    'MINA': 'mina-protocol',
    
    # Utility & Platform Tokens
    'BAT': 'basic-attention-token',
    'ENJ': 'enjin-coin',
    'COTI': 'coti',
    'BAND': 'band-protocol',
    'UMA': 'uma',
    'BICO': 'biconomy',
    'KEEP': 'keep-network',
    'POWR': 'power-ledger',
    'AUDIO': 'audius',
    'RLC': 'iexec-rlc',
    
    # Gaming & Emerging
    'SAGA': 'saga-2',
    'CTSI': 'cartesi',
    'SCRT': 'secret',
    'TNSR': 'tensor',
    'C98': 'coin98',
    'OGN': 'origin-protocol',
    'RAD': 'radworks',
    'NYM': 'nym',
    'ARPA': 'arpa',
    'ALCX': 'alchemix',
    
    # Gaming Ecosystems
    'ATLAS': 'star-atlas',
    'POLIS': 'star-atlas-dao',
    
    # DeFi & Advanced
    'PERP': 'perpetual-protocol',
    'STEP': 'step-finance',
    'RBN': 'robonomics-network',
    'KP3R': 'keep3rv1',
    'KEY': 'selfkey',
    
    # Privacy & Infrastructure
    'KILT': 'kilt-protocol',
    'TEER': 'integritee',
    'CRU': 'crust-network',
    'ZEUS': 'zeus-network',
    'MC': 'merit-circle'
}

def get_paris_time() -> datetime:
    """Retourne l'heure actuelle à Paris."""
    return datetime.now(PARIS_TZ)

def format_price(price: float, currency: str = "EUR") -> str:
    """
    Formate un prix avec le bon nombre de décimales.
    - >= 1 : 2 décimales
    - >= 0.01 : 4 décimales  
    - < 0.01 : 6 décimales
    """
    symbol = "€" if currency == "EUR" else "$"
    
    if price >= 1:
        return f"{symbol}{price:.2f}"
    elif price >= 0.01:
        return f"{symbol}{price:.4f}"
    else:
        return f"{symbol}{price:.6f}"

def format_percent_change(change: float) -> str:
    """Formate un pourcentage avec emoji selon la direction."""
    if change > 0:
        return f"📈 +{change:.2f}%"
    elif change < 0:
        return f"📉 {change:.2f}%"
    else:
        return f"➡️ {change:.2f}%"

def get_trend_emoji(change: float) -> str:
    """Retourne l'emoji correspondant à la tendance."""
    if change > 0:
        return "📈"
    elif change < 0:
        return "📉"
    else:
        return "➡️"

def get_asset_emoji(asset_type: str) -> str:
    """Retourne l'emoji pour le type d'actif."""
    return "🏢" if asset_type == "stock" else "🪙"

def is_euronext_open() -> bool:
    """Vérifie si Euronext Paris est ouvert."""
    now = get_paris_time()
    
    # Weekend
    if now.weekday() >= 5:
        return False
    
    # Jours fériés (simplifiés, à étendre)
    if is_french_holiday(now):
        return False
    
    # Heures d'ouverture : 9h00 - 17h30
    market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now.replace(hour=17, minute=30, second=0, microsecond=0)
    
    return market_open <= now <= market_close

def is_french_holiday(date: datetime) -> bool:
    """
    Vérifie si la date est un jour férié français.
    Version simplifiée - à étendre avec calcul Pâques, etc.
    """
    fixed_holidays = [
        (1, 1),   # Nouvel An
        (5, 1),   # Fête du Travail
        (5, 8),   # Victoire 1945
        (7, 14),  # Fête Nationale
        (8, 15),  # Assomption
        (11, 1),  # Toussaint
        (11, 11), # Armistice 1918
        (12, 25), # Noël
        (12, 26), # Saint-Étienne
    ]
    
    return (date.month, date.day) in fixed_holidays

def get_next_market_open() -> datetime:
    """Calcule la prochaine ouverture d'Euronext."""
    now = get_paris_time()
    next_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Si marché fermé aujourd'hui, passer au lendemain
    if now.hour >= 17 or (now.hour == 17 and now.minute >= 30):
        next_open += timedelta(days=1)
    
    # Avancer jusqu'au prochain jour ouvré
    max_days = 14
    days_checked = 0
    
    while days_checked < max_days:
        if next_open.weekday() < 5 and not is_french_holiday(next_open):
            return next_open
        next_open += timedelta(days=1)
        days_checked += 1
    
    return next_open

def calculate_percentage_change(old_price: float, new_price: float) -> float:
    """Calcule le changement en pourcentage entre deux prix."""
    if old_price == 0:
        return 0.0
    return ((new_price - old_price) / old_price) * 100

def chunk_list(lst: list, chunk_size: int) -> List[list]:
    """Divise une liste en chunks de taille donnée."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def safe_get(dictionary: dict, *keys, default=None):
    """Accès sécurisé aux clés imbriquées d'un dictionnaire."""
    value = dictionary
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
    return value if value is not None else default
    