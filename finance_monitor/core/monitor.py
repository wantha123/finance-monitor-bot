# core/monitor.py
"""
Orchestrateur principal du monitoring financier.
Coordonne la récupération des données, l'analyse, les alertes et les rapports.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time

from config import CONFIG
from core.utils import (
    get_paris_time, is_euronext_open, get_next_market_open,
    format_price, format_percent_change
)
from core.alerting import AlertChecker, AlertFormatter, AlertAggregator
from core.summary import PortfolioSummary, ReportBuilder
from data.database import DB_PATH, init_database
from data.fetchers import StockFetcher, CryptoFetcher, NewsFetcher
from alerts.email import send_email
from alerts.slack import send_slack

logger = logging.getLogger(__name__)


class FinanceMonitor:
    """Classe principale de monitoring financier."""
    
    def __init__(self):
        """Initialise le moniteur avec la configuration."""
        self.config = CONFIG
        self.db_path = DB_PATH
        
        # Initialiser la base de données
        init_database()
        
        # Initialiser les fetchers
        self.stock_fetcher = StockFetcher()
        self.crypto_fetcher = CryptoFetcher()
        self.news_fetcher = NewsFetcher(CONFIG.get('news_api_key'))
        
        # Initialiser les alertes
        self.alert_checker = AlertChecker(self._get_all_thresholds())
        self.alert_aggregator = AlertAggregator()
        
        # État du monitoring
        self.last_report_sent = {'morning': None, 'evening': None}
        
        logger.info("🚀 Finance Monitor initialisé")
    
    def _get_all_thresholds(self) -> Dict[str, Dict]:
        """Compile tous les seuils depuis la config."""
        thresholds = {}
        
        # Seuils stocks
        for symbol, stock_config in self.config.get('stocks', {}).items():
            thresholds[symbol] = stock_config.get('thresholds', {})
        
        # Seuils crypto
        for symbol, crypto_config in self.config.get('crypto', {}).items():
            thresholds[symbol] = crypto_config.get('thresholds', {})
        
        return thresholds
    
    def monitor_assets(self):
        """
        Fonction principale de monitoring.
        Récupère les prix, vérifie les alertes, envoie les notifications.
        """
        logger.info("=" * 60)
        logger.info("🔄 Début du cycle de monitoring")
        logger.info("=" * 60)
        
        # Vérifier si c'est l'heure d'un rapport quotidien
        self._check_daily_reports()
        
        # Données collectées
        stock_data = {}
        crypto_data = {}
        alerts = []
        
        # 1. Monitoring des stocks
        if is_euronext_open():
            logger.info("📊 Euronext Paris OUVERT - Monitoring des stocks")
            stock_data = self._monitor_stocks()
        else:
            next_open = get_next_market_open()
            logger.info(f"📊 Euronext Paris FERMÉ - Prochaine ouverture: {next_open.strftime('%d/%m %H:%M')}")
        
        # 2. Monitoring des cryptos (24/7)
        logger.info("🪙 Monitoring des cryptomonnaies")
        crypto_data = self._monitor_crypto()
        
        # 3. Vérifier les news (optionnel, pour économiser l'API)
        news_items = []
        if self._should_check_news():
            logger.info("📰 Vérification des actualités")
            news_items = self._check_news(stock_data, crypto_data)
        
        # 4. Envoyer les alertes si nécessaire
        if self.alert_aggregator.should_send_notification():
            self._send_alerts(stock_data, crypto_data, news_items)
        
        # 5. Log du résumé
        self._log_monitoring_summary(stock_data, crypto_data, alerts)
        
        logger.info("✅ Cycle de monitoring terminé\n")
    
    def _monitor_stocks(self) -> Dict[str, Dict]:
        """Monitore tous les stocks configurés."""
        stock_data = {}
        stock_symbols = self.config.get('stocks', {})
        
        logger.info(f"📈 Monitoring de {len(stock_symbols)} actions...")
        
        for symbol, stock_config in stock_symbols.items():
            try:
                # Récupérer le prix
                data = self.stock_fetcher.get_stock_price(symbol)
                if not data:
                    continue
                
                # Enrichir avec le nom de la config
                data['name'] = stock_config['name']
                stock_data[symbol] = data
                
                # Stocker en base
                self._store_price(symbol, data['current_price'], 'stock')
                
                # Vérifier les alertes
                previous_price = self._get_previous_price(symbol)
                alerts = self.alert_checker.check_price_alerts(
                    symbol, 
                    data['current_price'],
                    previous_price,
                    'stock'
                )
                self.alert_aggregator.add_alerts(alerts)
                
                # Log
                logger.info(
                    f"  {stock_config['name']} ({symbol}): "
                    f"{format_price(data['current_price'])} "
                    f"({format_percent_change(data['change_percent'])})"
                )
                
            except Exception as e:
                logger.error(f"❌ Erreur monitoring {symbol}: {e}")
        
        return stock_data
    
    def _monitor_crypto(self) -> Dict[str, Dict]:
        """Monitore toutes les cryptos configurées."""
        crypto_symbols = list(self.config.get('crypto', {}).keys())
        
        logger.info(f"💎 Monitoring de {len(crypto_symbols)} cryptomonnaies...")
        
        # Récupération en lot (optimisé pour CoinGecko)
        all_crypto_data = self.crypto_fetcher.get_all_crypto_prices(crypto_symbols)
        
        # Traiter chaque crypto
        for symbol, data in all_crypto_data.items():
            if not data or not data.get('current_price_eur'):
                continue
            
            try:
                crypto_config = self.config['crypto'][symbol]
                price = data['current_price_eur']
                
                # Stocker en base
                self._store_price(symbol, price, 'crypto')
                
                # Vérifier les alertes
                previous_price = self._get_previous_price(symbol)
                alerts = self.alert_checker.check_price_alerts(
                    symbol,
                    price,
                    previous_price,
                    'crypto'
                )
                self.alert_aggregator.add_alerts(alerts)
                
                # Log
                logger.info(
                    f"  {crypto_config['name']} ({symbol}): "
                    f"{format_price(price)} "
                    f"({format_percent_change(data.get('change_percent_24h', 0))})"
                )
                
            except Exception as e:
                logger.error(f"❌ Erreur traitement {symbol}: {e}")
        
        return all_crypto_data
    
    def _check_news(self, stock_data: Dict, crypto_data: Dict) -> List[Dict]:
        """Vérifie les actualités pour les actifs importants."""
        news_items = []
        
        # Limiter aux top movers pour économiser l'API
        all_assets = []
        
        for symbol, data in stock_data.items():
            if data:
                all_assets.append({
                    'symbol': symbol,
                    'name': data.get('name', symbol),
                    'change': abs(data.get('change_percent', 0)),
                    'type': 'stock'
                })
        
        for symbol, data in crypto_data.items():
            if data and data.get('current_price_eur'):
                all_assets.append({
                    'symbol': symbol,
                    'name': self.config['crypto'][symbol]['name'],
                    'change': abs(data.get('change_percent_24h', 0)),
                    'type': 'crypto'
                })
        
        # Trier par mouvement absolu et prendre le top 5
        all_assets.sort(key=lambda x: x['change'], reverse=True)
        top_movers = all_assets[:5]
        
        for asset in top_movers:
            query = f"{asset['name']} {asset['type']}"
            try:
                news = self.news_fetcher.get_news(query)
                if news:
                    news_items.extend(news[:2])  # Max 2 news par actif
            except Exception as e:
                logger.warning(f"Erreur récupération news pour {query}: {e}")
        
        return news_items
    
    def _should_check_news(self) -> bool:
        """Détermine si on doit vérifier les news (pour économiser l'API)."""
        current_minute = datetime.now().minute
        # Vérifier les news seulement toutes les heures (minute 0)
        return is_euronext_open() and current_minute == 0
    
    def _store_price(self, symbol: str, price: float, market_type: str):
        """Stocke un prix en base de données."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO price_history (symbol, price, market_type)
                VALUES (?, ?, ?)
            ''', (symbol, price, market_type))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Erreur stockage prix {symbol}: {e}")
    
    def _get_previous_price(self, symbol: str) -> float:
        """Récupère le dernier prix stocké pour un symbole."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT price FROM price_history 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT 1 OFFSET 1
            ''', (symbol,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 0.0
            
        except Exception as e:
            logger.error(f"Erreur récupération prix précédent {symbol}: {e}")
            return 0.0
    
    def _send_alerts(self, stock_data: Dict, crypto_data: Dict, news_items: List):
        """Envoie les alertes consolidées."""
        alerts_summary = self.alert_aggregator.get_summary()
        
        logger.info(f"🚨 Envoi des alertes: {alerts_summary['total']} notifications")
        
        # Créer le message
        subject = f"🚨 Alerte Portfolio - {alerts_summary['total']} notifications"
        
        # Version texte simple
        plain_message = self._create_alert_message_plain(
            stock_data, crypto_data, news_items
        )
        
        # Version HTML enrichie
        html_message = self._create_alert_message_html(
            stock_data, crypto_data, news_items
        )
        
        # Envoyer par email
        send_email(subject, plain_message, html_message)
        
        # Envoyer sur Slack (version simplifiée)
        slack_message = self._create_alert_message_slack()
        send_slack(slack_message)
        
        # Enregistrer l'envoi
        self._record_alerts_sent()
        
        # Nettoyer pour le prochain cycle
        self.alert_aggregator.clear()
    
    def _create_alert_message_plain(self, stock_data: Dict, 
                                   crypto_data: Dict, news_items: List) -> str:
        """Crée le message d'alerte en texte brut."""
        lines = [
            "🚨 ALERTE MONITORING FINANCIER",
            "=" * 50,
            "",
            f"📅 {get_paris_time().strftime('%d/%m/%Y %H:%M')} (Paris)",
            ""
        ]
        
        # Alertes groupées
        grouped = self.alert_aggregator.get_grouped_alerts()
        
        for alert_type, alerts in grouped.items():
            if alerts:
                lines.append(f"\n{alert_type.replace('_', ' ').title()} ({len(alerts)}):")
                lines.append("-" * 40)
                
                for alert in alerts[:5]:  # Max 5 par type
                    symbol = alert['symbol']
                    name = self._get_asset_name(symbol)
                    formatted = AlertFormatter.format_alert_detailed(alert, name)
                    lines.append(formatted)
                    lines.append("")
        
        # Top movers
        summary = PortfolioSummary(stock_data, crypto_data)
        top_movers = summary.get_biggest_movers(5)
        
        if top_movers:
            lines.append("\n🔥 PLUS GROS MOUVEMENTS:")
            lines.append("-" * 40)
            for asset in top_movers:
                emoji = asset['emoji']
                name = asset['name']
                symbol = asset['symbol']
                price = format_price(asset['price'])
                change = format_percent_change(asset['change'])
                lines.append(f"{emoji} {name} ({symbol}): {price} {change}")
        
        # News (si disponibles)
        if news_items:
            lines.append("\n📰 ACTUALITÉS:")
            lines.append("-" * 40)
            for news in news_items[:3]:
                lines.append(f"• {news['title']}")
                lines.append(f"  Source: {news['source']}")
                lines.append("")
        
        lines.extend([
            "",
            "=" * 50,
            "🤖 Finance Monitor Bot"
        ])
        
        return "\n".join(lines)
    
    def _create_alert_message_html(self, stock_data: Dict,
                                  crypto_data: Dict, news_items: List) -> str:
        """Crée le message d'alerte en HTML."""
        # Utiliser les mêmes sections que le plain text
        # mais avec formatage HTML enrichi
        
        html_parts = []
        
        # Section alertes
        grouped = self.alert_aggregator.get_grouped_alerts()
        for alert_type, alerts in grouped.items():
            if alerts:
                html_parts.append(f'<div class="alert-section">')
                html_parts.append(f'<h3>{alert_type.replace("_", " ").title()}</h3>')
                
                for alert in alerts[:5]:
                    symbol = alert['symbol']
                    name = self._get_asset_name(symbol)
                    alert_html = AlertFormatter.format_alert_html(alert, name)
                    html_parts.append(alert_html)
                
                html_parts.append('</div>')
        
        # Section top movers
        summary = PortfolioSummary(stock_data, crypto_data)
        top_movers = summary.get_biggest_movers(5)
        
        if top_movers:
            html_parts.append('<div class="movers-section">')
            html_parts.append('<h3>🔥 Plus Gros Mouvements</h3>')
            
            for asset in top_movers:
                change_class = 'gain' if asset['change'] > 0 else 'loss'
                html_parts.append(f'''
                <div class="asset-row {change_class}">
                    <span class="asset-name">{asset['emoji']} {asset['name']} ({asset['symbol']})</span>
                    <span class="asset-price">{format_price(asset['price'])}</span>
                    <span class="asset-change">{format_percent_change(asset['change'])}</span>
                </div>
                ''')
            
            html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _create_alert_message_slack(self) -> str:
        """Crée un message simplifié pour Slack."""
        summary = self.alert_aggregator.get_summary()
        grouped = self.alert_aggregator.get_grouped_alerts()
        
        lines = [
            f"🚨 *Alerte Portfolio* - {summary['total']} notifications",
            f"__{get_paris_time().strftime('%H:%M')} Paris__",
            ""
        ]
        
        # Résumé par type
        for alert_type, alerts in grouped.items():
            if alerts:
                emoji_map = {
                    'HIGH_THRESHOLD': '🔴',
                    'LOW_THRESHOLD': '🔵',
                    'SIGNIFICANT_MOVE': '⚡'
                }
                emoji = emoji_map.get(alert_type, '📊')
                lines.append(f"{emoji} {len(alerts)} {alert_type.replace('_', ' ').lower()}")
        
        lines.append("\n_Détails complets envoyés par email_")
        
        return '\n'.join(lines)
    
    def _get_asset_name(self, symbol: str) -> str:
        """Récupère le nom d'un actif depuis la config."""
        # Chercher dans les stocks
        if symbol in self.config.get('stocks', {}):
            return self.config['stocks'][symbol]['name']
        
        # Chercher dans les cryptos
        if symbol in self.config.get('crypto', {}):
            return self.config['crypto'][symbol]['name']
        
        return symbol
    
    def _record_alerts_sent(self):
        """Enregistre les alertes envoyées en base."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for alert in self.alert_aggregator.alerts:
                cursor.execute('''
                    INSERT INTO alerts_sent (symbol, alert_type, message)
                    VALUES (?, ?, ?)
                ''', (
                    alert['symbol'],
                    alert['type'],
                    AlertFormatter.format_alert_simple(alert)
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur enregistrement alertes: {e}")
    
    def _check_daily_reports(self):
        """Vérifie s'il faut envoyer un rapport quotidien."""
        paris_time = get_paris_time()
        current_hour = paris_time.hour
        current_minute = paris_time.minute
        today = paris_time.date()
        
        # Rapport du matin : 9h30 - 10h30
        if 9 <= current_hour <= 10:
            if (current_hour == 9 and current_minute >= 30) or (current_hour == 10 and current_minute <= 30):
                if self.last_report_sent['morning'] != today:
                    self._send_daily_report('morning')
                    self.last_report_sent['morning'] = today
        
        # Rapport du soir : 17h30 - 18h30
        if 17 <= current_hour <= 18:
            if (current_hour == 17 and current_minute >= 30) or (current_hour == 18 and current_minute <= 30):
                if self.last_report_sent['evening'] != today:
                    self._send_daily_report('evening')
                    self.last_report_sent['evening'] = today
    
    def _send_daily_report(self, report_type: str):
        """Envoie un rapport quotidien."""
        logger.info(f"📧 Génération du rapport {report_type}")
        
        # Récupérer toutes les données actuelles
        stock_data = {}
        crypto_data = {}
        
        # Stocks (même si marché fermé, on prend les dernières valeurs)
        for symbol in self.config.get('stocks', {}):
            data = self.stock_fetcher.get_stock_price(symbol)
            if data:
                data['name'] = self.config['stocks'][symbol]['name']
                stock_data[symbol] = data
        
        # Cryptos
        crypto_symbols = list(self.config.get('crypto', {}).keys())
        crypto_data = self.crypto_fetcher.get_all_crypto_prices(crypto_symbols)
        
        # Créer le rapport
        summary = PortfolioSummary(stock_data, crypto_data)
        builder = ReportBuilder(summary)
        
        report = builder.build_daily_report(report_type)
        
        # Envoyer par email
        subject = report['subject']
        send_email(subject, report['plain'], report['html'])
        
        logger.info(f"✅ Rapport {report_type} envoyé")
    
    def _log_monitoring_summary(self, stock_data: Dict, 
                               crypto_data: Dict, alerts: List):
        """Log un résumé du cycle de monitoring."""
        total_stocks = len(stock_data)
        total_crypto = len(crypto_data)
        total_alerts = len(self.alert_aggregator.alerts)
        
        logger.info("📊 RÉSUMÉ DU MONITORING:")
        logger.info(f"  • Stocks actifs: {total_stocks}/{len(self.config.get('stocks', {}))}")
        logger.info(f"  • Cryptos actives: {total_crypto}/{len(self.config.get('crypto', {}))}")
        logger.info(f"  • Alertes déclenchées: {total_alerts}")
        
        if total_alerts > 0:
            summary = self.alert_aggregator.get_summary()
            logger.info(f"  • Par type: {summary['by_type']}")


def run_monitoring_cycle():
    """Fonction helper pour exécuter un cycle de monitoring."""
    try:
        monitor = FinanceMonitor()
        monitor.monitor_assets()
    except Exception as e:
        logger.error(f"❌ Erreur critique dans le monitoring: {e}", exc_info=True)
        # Optionnel : envoyer une alerte d'erreur
        try:
            send_email(
                "❌ Erreur Finance Monitor",
                f"Une erreur critique s'est produite:\n\n{str(e)}",
                None
            )
        except:
            pass
