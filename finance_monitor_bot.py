#!/usr/bin/env python3
"""
Financial & Crypto Monitoring Bot
Monitors OVH stock and Solana cryptocurrency with news alerts
"""

import requests
import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import sqlite3
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
import yfinance as yf
from newsapi import NewsApiClient
import schedule
import pytz
import os

# Create log directory - works on Railway, Render, local, etc.
if os.path.exists('/app'):  # Railway/Docker environment
    log_dir = '/app/logs'
elif os.path.exists('/opt/render'):  # Render environment  
    log_dir = '/opt/render/project/logs'
elif os.path.exists('/home'):  # PythonAnywhere environment
    log_dir = '/home/your_username/finance_bot'
else:  # Local environment
    log_dir = r'C:\Users\robin\Documents\EXPORT AI\Claude\Finance'

os.makedirs(log_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'finance_monitor.log')),
        logging.StreamHandler()  # Also log to console
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PriceAlert:
    symbol: str
    current_price: float
    threshold_high: float
    threshold_low: float
    change_percent: float
    alert_triggered: bool = False

@dataclass
class NewsItem:
    title: str
    source: str
    published_at: str
    url: str
    sentiment_score: Optional[float] = None

class FinanceMonitor:
    def __init__(self, config: Dict):
        self.config = config
        self.db_path = "finance_monitor.db"
        self.init_database()
        
        # Initialize News API
        self.news_api = NewsApiClient(api_key=config.get('news_api_key'))
        
        # Euronext Paris timezone
        self.paris_tz = pytz.timezone('Europe/Paris')
        
        # Exchange rate cache (updated every hour)
        self.usd_to_eur_rate = None
        self.last_rate_update = None
        
        # 2025 Euronext Paris holidays (market closed)
        self.market_holidays_2025 = [
            datetime(2025, 1, 1),   # New Year's Day
            datetime(2025, 4, 18),  # Good Friday
            datetime(2025, 4, 21),  # Easter Monday
            datetime(2025, 5, 1),   # Labour Day
            datetime(2025, 5, 8),   # Victory in Europe Day
            datetime(2025, 5, 29),  # Ascension Day
            datetime(2025, 6, 9),   # Whit Monday
            datetime(2025, 7, 14),  # Bastille Day
            datetime(2025, 8, 15),  # Assumption of Mary
            datetime(2025, 11, 1),  # All Saints' Day
            datetime(2025, 11, 11), # Armistice Day
            datetime(2025, 12, 25), # Christmas Day
            datetime(2025, 12, 26), # Boxing Day
        ]
    
    def init_database(self):
        """Initialize SQLite database for storing historical data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                market_type TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts_sent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_tracked (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                url TEXT NOT NULL,
                published_at DATETIME,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_usd_to_eur_rate(self) -> float:
        """Get current USD to EUR exchange rate (cached for 1 hour)"""
        now = datetime.now()
        
        # Check if we need to update the rate (every hour or if not cached)
        if (self.last_rate_update is None or 
            (now - self.last_rate_update).total_seconds() > 3600):
            
            try:
                # Using exchangerate-api.com (free tier: 1500 requests/month)
                url = "https://api.exchangerate-api.com/v4/latest/USD"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                self.usd_to_eur_rate = data['rates']['EUR']
                self.last_rate_update = now
                logger.info(f"Updated USD/EUR rate: {self.usd_to_eur_rate:.4f}")
                
            except Exception as e:
                logger.error(f"Error fetching exchange rate: {e}")
                # Fallback to approximate rate if API fails
                if self.usd_to_eur_rate is None:
                    self.usd_to_eur_rate = 0.92  # Approximate fallback rate
                    logger.warning("Using fallback USD/EUR rate: 0.92")
        
        return self.usd_to_eur_rate
    
    def usd_to_eur(self, usd_amount: float) -> float:
        """Convert USD amount to EUR"""
        if usd_amount is None:
            return None
        rate = self.get_usd_to_eur_rate()
        return usd_amount * rate
    
    def is_euronext_open(self) -> bool:
        """Check if Euronext Paris is currently open for trading"""
        now_paris = datetime.now(self.paris_tz)
        
        # Check if it's a weekend
        if now_paris.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check if it's a holiday
        today = now_paris.date()
        for holiday in self.market_holidays_2025:
            if holiday.date() == today:
                return False
        
        # Check trading hours (9:00 AM - 5:30 PM CET)
        market_open = now_paris.replace(hour=9, minute=0, second=0, microsecond=0)
        market_close = now_paris.replace(hour=17, minute=30, second=0, microsecond=0)
        
        return market_open <= now_paris <= market_close
    
    def get_next_market_open(self) -> datetime:
        """Get the next time Euronext Paris will be open"""
        now_paris = datetime.now(self.paris_tz)
        
        # Start with tomorrow if market is currently closed for the day
        next_day = now_paris.replace(hour=9, minute=0, second=0, microsecond=0)
        if now_paris.hour >= 17 or (now_paris.hour == 17 and now_paris.minute >= 30):
            next_day += timedelta(days=1)
        
        # Find next trading day
        while True:
            # Skip weekends
            if next_day.weekday() >= 5:
                next_day += timedelta(days=1)
                continue
            
            # Skip holidays
            is_holiday = False
            for holiday in self.market_holidays_2025:
                if holiday.date() == next_day.date():
                    is_holiday = True
                    break
            
            if is_holiday:
                next_day += timedelta(days=1)
                continue
            
            return next_day
    
    def get_ovh_price(self) -> Optional[Dict]:
        """Get OVH stock price from Yahoo Finance - only during market hours"""
        # Check if market is open
        if not self.is_euronext_open():
            next_open = self.get_next_market_open()
            logger.info(f"Euronext Paris is closed. Next market open: {next_open.strftime('%Y-%m-%d %H:%M %Z')}")
            return None
            
        try:
            # OVH is listed on Euronext Paris as OVH.PA
            ticker = yf.Ticker("OVH.PA")
            hist = ticker.history(period="1d", interval="1m")
            
            if hist.empty:
                logger.warning("No data found for OVH.PA")
                return None
                
            current_price = hist['Close'].iloc[-1]
            prev_close = ticker.info.get('previousClose', current_price)
            change_percent = ((current_price - prev_close) / prev_close) * 100
            
            return {
                'symbol': 'OVH.PA',
                'current_price': float(current_price),
                'previous_close': float(prev_close),
                'change_percent': float(change_percent),
                'volume': int(hist['Volume'].iloc[-1]),
                'timestamp': datetime.now().isoformat(),
                'market_open': True
            }
        except Exception as e:
            logger.error(f"Error fetching OVH price: {e}")
            return None
    
    def get_solana_price(self) -> Optional[Dict]:
        """Get Solana price from CoinGecko API (free) - converted to EUR"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'solana',
                'vs_currencies': 'usd,eur',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            sol_data = data.get('solana', {})
            
            # Get EUR price directly or convert from USD
            price_eur = sol_data.get('eur')
            if price_eur is None and sol_data.get('usd'):
                price_eur = self.usd_to_eur(sol_data.get('usd'))
            
            # Convert volume to EUR if needed
            volume_usd = sol_data.get('usd_24h_vol')
            volume_eur = self.usd_to_eur(volume_usd) if volume_usd else None
            
            return {
                'symbol': 'SOL',
                'current_price_eur': price_eur,
                'current_price_usd': sol_data.get('usd'),  # Keep USD for reference
                'change_percent_24h': sol_data.get('usd_24h_change'),
                'volume_24h_eur': volume_eur,
                'timestamp': datetime.now().isoformat(),
                'market_open': True,  # Crypto markets are always open
                'exchange_rate_used': self.get_usd_to_eur_rate()
            }
        except Exception as e:
            logger.error(f"Error fetching Solana price: {e}")
            return None
    
    def check_price_alerts(self, symbol: str, current_price: float, thresholds: Dict) -> List[str]:
        """Check if price alerts should be triggered"""
        alerts = []
        
        # Get previous price from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT price FROM price_history 
            WHERE symbol = ? 
            ORDER BY timestamp DESC LIMIT 1
        ''', (symbol,))
        
        result = cursor.fetchone()
        prev_price = result[0] if result else current_price
        
        # Calculate percentage change
        if prev_price > 0:
            change_percent = ((current_price - prev_price) / prev_price) * 100
        else:
            change_percent = 0
        
        # Check thresholds
        if current_price >= thresholds.get('high', float('inf')):
            alerts.append(f"🔴 {symbol} HIGH ALERT: Price reached €{current_price:.2f} (threshold: €{thresholds['high']:.2f})")
        
        if current_price <= thresholds.get('low', 0):
            alerts.append(f"🔵 {symbol} LOW ALERT: Price dropped to €{current_price:.2f} (threshold: €{thresholds['low']:.2f})")
        
        if abs(change_percent) >= thresholds.get('change_percent', 10):
            direction = "📈" if change_percent > 0 else "📉"
            alerts.append(f"{direction} {symbol} MOVEMENT: {change_percent:+.2f}% change (€{prev_price:.2f} → €{current_price:.2f})")
        
        conn.close()
        return alerts
    
    def get_news(self, query: str, language: str = 'en') -> List[NewsItem]:
        """Fetch news articles related to the query"""
        try:
            # Get news from the last 24 hours
            from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            articles = self.news_api.get_everything(
                q=query,
                from_param=from_date,
                language=language,
                sort_by='publishedAt',
                page_size=5
            )
            
            news_items = []
            for article in articles['articles']:
                news_items.append(NewsItem(
                    title=article['title'],
                    source=article['source']['name'],
                    published_at=article['publishedAt'],
                    url=article['url']
                ))
            
            return news_items
        except Exception as e:
            logger.error(f"Error fetching news for {query}: {e}")
            return []
    
    def store_price_data(self, symbol: str, price: float, market_type: str):
        """Store price data in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO price_history (symbol, price, market_type)
            VALUES (?, ?, ?)
        ''', (symbol, price, market_type))
        conn.commit()
        conn.close()
    
    def send_email_notification(self, subject: str, message: str):
        """Send email notification"""
        try:
            email_config = self.config.get('email', {})
            if not email_config.get('enabled', False):
                logger.info(f"Email disabled. Would send: {subject}")
                return
            
            msg = MIMEMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = email_config['to_email']
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['from_email'], email_config['password'])
            text = msg.as_string()
            server.sendmail(email_config['from_email'], email_config['to_email'], text)
            server.quit()
            
            logger.info(f"Email sent: {subject}")
        except Exception as e:
            logger.error(f"Error sending email: {e}")
    
    def send_slack_notification(self, message: str):
        """Send notification to Slack"""
        try:
            slack_config = self.config.get('slack', {})
            if not slack_config.get('enabled', False):
                logger.info(f"Slack disabled. Would send: {message[:100]}...")
                return
            
            webhook_url = slack_config.get('webhook_url')
            if not webhook_url:
                logger.error("Slack webhook URL not configured")
                return
            
            # Format message for Slack
            payload = {
                "text": "📊 Financial Monitor Alert",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "📊 Financial Monitoring Report"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```{message}```"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CET"
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("Slack notification sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
    
    def send_notification(self, subject: str, message: str, notification_type: str = "alert"):
        """Send notification via configured method"""
        full_message = f"{subject}\n\n{message}"
        
        if notification_type == "daily_report":
            # Daily reports go to email
            self.send_email_notification(subject, message)
        else:
            # Alerts go to Slack
            self.send_slack_notification(full_message)
    
    def should_run_now(self) -> Dict[str, bool]:
        """Determine what actions should run based on current time"""
        paris_now = datetime.now(self.paris_tz)
        current_hour = paris_now.hour
        current_minute = paris_now.minute
        
        # Check if we've already run certain tasks today
        today = paris_now.date()
        
        actions = {
            'monitor': False,
            'morning_report': False,
            'evening_report': False
        }
        
        # Always monitor (this is our main task)
        actions['monitor'] = True
        
        # Check for morning report (10:00 AM, only once per day)
        if current_hour == 10 and 0 <= current_minute <= 59:
            # Check if we already sent morning report today
            if not self.has_sent_report_today('morning', today):
                actions['morning_report'] = True
        
        # Check for evening report (6:00 PM, only once per day)
        elif current_hour == 18 and 0 <= current_minute <= 59:
            # Check if we already sent evening report today
            if not self.has_sent_report_today('evening', today):
                actions['evening_report'] = True
        
        return actions
    
    def has_sent_report_today(self, report_type: str, today_date) -> bool:
        """Check if we've already sent a report today"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if we sent this type of report today
            cursor.execute('''
                SELECT COUNT(*) FROM alerts_sent 
                WHERE alert_type = ? AND DATE(timestamp) = ?
            ''', (f'daily_report_{report_type}', today_date.isoformat()))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
        except Exception as e:
            logger.error(f"Error checking report history: {e}")
            return False
    
    def record_report_sent(self, report_type: str):
        """Record that we sent a report"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts_sent (symbol, alert_type, message)
                VALUES (?, ?, ?)
            ''', ('SYSTEM', f'daily_report_{report_type}', f'{report_type} report sent'))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error recording report: {e}")
        """Get daily summary of prices and changes"""
        summary = {
            'ovh_data': None,
            'sol_data': None,
            'market_status': [],
            'daily_changes': {}
        }
        
        # Check market status
        if self.is_euronext_open():
            summary['market_status'].append("🟢 Euronext Paris: OPEN")
        else:
            next_open = self.get_next_market_open()
            summary['market_status'].append(f"🔴 Euronext Paris: CLOSED (Next open: {next_open.strftime('%Y-%m-%d %H:%M %Z')})")
        
        summary['market_status'].append("🟢 Crypto Markets: ALWAYS OPEN")
        
        # Get current prices
        summary['ovh_data'] = self.get_ovh_price()
        summary['sol_data'] = self.get_solana_price()
        
        # Get daily changes from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get prices from 24 hours ago
        yesterday = datetime.now() - timedelta(days=1)
        
        for symbol in ['OVH.PA', 'SOL']:
            cursor.execute('''
                SELECT price FROM price_history 
                WHERE symbol = ? AND timestamp >= ? 
                ORDER BY timestamp ASC LIMIT 1
            ''', (symbol, yesterday.isoformat()))
            
            result = cursor.fetchone()
            if result:
                old_price = result[0]
                if symbol == 'OVH.PA' and summary['ovh_data']:
                    current_price = summary['ovh_data']['current_price']
                    change = ((current_price - old_price) / old_price) * 100
                    summary['daily_changes']['OVH'] = {
                        'old_price': old_price,
                        'current_price': current_price,
                        'change_percent': change
                    }
                elif symbol == 'SOL' and summary['sol_data']:
                    current_price = summary['sol_data']['current_price_eur']
                    change = ((current_price - old_price) / old_price) * 100
                    summary['daily_changes']['SOL'] = {
                        'old_price': old_price,
                        'current_price': current_price,
                        'change_percent': change
                    }
        
        conn.close()
        return summary
    
    def send_daily_report(self, report_type: str = "morning"):
        """Send daily email report"""
        logger.info(f"Generating {report_type} daily report...")
        
        summary = self.get_daily_summary()
        paris_time = datetime.now(self.paris_tz)
        
        if report_type == "morning":
            subject = f"🌅 Morning Financial Report - {paris_time.strftime('%Y-%m-%d')}"
            greeting = "Good morning! Here's your financial market update:"
        else:  # evening
            subject = f"🌆 Evening Financial Report - {paris_time.strftime('%Y-%m-%d')}"
            greeting = "Good evening! Here's your end-of-day financial summary:"
        
        message = f"{greeting}\n\n"
        message += "=" * 50 + "\n"
        message += f"📅 DAILY FINANCIAL REPORT - {paris_time.strftime('%A, %B %d, %Y')}\n"
        message += f"🕐 Generated at: {paris_time.strftime('%H:%M %Z')}\n"
        message += "=" * 50 + "\n\n"
        
        # Market status
        message += "📊 MARKET STATUS:\n"
        for status in summary['market_status']:
            message += f"  {status}\n"
        message += "\n"
        
        # Current prices
        message += "💰 CURRENT PRICES:\n"
        if summary['ovh_data']:
            message += f"  🏢 OVH (OVH.PA): €{summary['ovh_data']['current_price']:.2f}\n"
        else:
            message += "  🏢 OVH (OVH.PA): Market closed - no current price\n"
        
        if summary['sol_data']:
            message += f"  🪙 Solana (SOL): €{summary['sol_data']['current_price_eur']:.2f} [${summary['sol_data']['current_price_usd']:.2f} USD]\n"
        message += "\n"
        
        # Daily changes (if available)
        if summary['daily_changes']:
            message += "📈 24-HOUR CHANGES:\n"
            for symbol, change_data in summary['daily_changes'].items():
                direction = "📈" if change_data['change_percent'] > 0 else "📉" if change_data['change_percent'] < 0 else "➡️"
                message += f"  {direction} {symbol}: {change_data['change_percent']:+.2f}% "
                message += f"(€{change_data['old_price']:.2f} → €{change_data['current_price']:.2f})\n"
            message += "\n"
        
        # Recent news
        ovh_news = self.get_news("OVH cloud OR OVHcloud")
        sol_news = self.get_news("Solana cryptocurrency OR SOL crypto")
        
        if ovh_news:
            message += "📰 OVH NEWS (Last 24h):\n"
            for news in ovh_news[:2]:  # Limit to 2 articles for email
                message += f"  • {news.title}\n"
                message += f"    {news.source} | {news.url}\n"
            message += "\n"
        
        if sol_news:
            message += "📰 SOLANA NEWS (Last 24h):\n"
            for news in sol_news[:2]:  # Limit to 2 articles for email
                message += f"  • {news.title}\n"
                message += f"    {news.source} | {news.url}\n"
            message += "\n"
        
        # Footer
        message += "=" * 50 + "\n"
        message += "🤖 Automated Financial Monitor | Next report: "
        if report_type == "morning":
            message += "18:00 CET"
        else:
            message += "10:00 CET tomorrow"
        message += "\n" + "=" * 50
        
        # Send email report
        self.send_notification(subject, message, notification_type="daily_report")
        
        # Record that we sent this report
        self.record_report_sent(report_type)
        
        logger.info(f"{report_type.capitalize()} daily report sent")
        """Main monitoring function"""
        logger.info("Starting asset monitoring cycle...")
        
        alerts = []
        market_status = []
        
        # Check market status
        if self.is_euronext_open():
            market_status.append("🟢 Euronext Paris: OPEN")
        else:
            next_open = self.get_next_market_open()
            market_status.append(f"🔴 Euronext Paris: CLOSED (Next open: {next_open.strftime('%Y-%m-%d %H:%M %Z')})")
        
        market_status.append("🟢 Crypto Markets: ALWAYS OPEN")
        
        # Monitor OVH
        ovh_data = self.get_ovh_price()
        if ovh_data:
            self.store_price_data('OVH.PA', ovh_data['current_price'], 'stock')
            
            ovh_thresholds = self.config['thresholds']['OVH']
            ovh_alerts = self.check_price_alerts('OVH', ovh_data['current_price'], ovh_thresholds)
            alerts.extend(ovh_alerts)
            
            logger.info(f"OVH: €{ovh_data['current_price']:.2f} ({ovh_data['change_percent']:+.2f}%)")
        elif not self.is_euronext_open():
            logger.info("OVH monitoring skipped - market closed")
        
        # Monitor Solana
        sol_data = self.get_solana_price()
        if sol_data:
            # Store EUR price in database
            self.store_price_data('SOL', sol_data['current_price_eur'], 'crypto')
            
            sol_thresholds = self.config['thresholds']['SOL']
            sol_alerts = self.check_price_alerts('SOL', sol_data['current_price_eur'], sol_thresholds)
            alerts.extend(sol_alerts)
            
            logger.info(f"SOL: €{sol_data['current_price_eur']:.2f} ({sol_data['change_percent_24h']:+.2f}%) [Rate: {sol_data['exchange_rate_used']:.4f}]")
        
        # Get news
        ovh_news = self.get_news("OVH cloud OR OVHcloud")
        sol_news = self.get_news("Solana cryptocurrency OR SOL crypto")
        
        # Send notifications if alerts exist or if it's a regular update
        if alerts or ovh_news or sol_news or ovh_data or sol_data:
            subject = f"Financial Monitor Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            message = "=== FINANCIAL MONITORING REPORT ===\n\n"
            
            # Market status
            message += "📊 MARKET STATUS:\n"
            for status in market_status:
                message += f"  {status}\n"
            message += "\n"
            
            if alerts:
                message += "🚨 PRICE ALERTS:\n"
                for alert in alerts:
                    message += f"  {alert}\n"
                message += "\n"
            
            if ovh_data:
                message += f"📊 OVH (OVH.PA): €{ovh_data['current_price']:.2f} ({ovh_data['change_percent']:+.2f}%)\n"
            
            if sol_data:
                message += f"📊 Solana (SOL): €{sol_data['current_price_eur']:.2f} ({sol_data['change_percent_24h']:+.2f}%) [${sol_data['current_price_usd']:.2f} USD]\n"
            
            message += "\n"
            
            if ovh_news:
                message += "📰 OVH NEWS:\n"
                for news in ovh_news[:3]:  # Limit to 3 articles
                    message += f"  • {news.title} ({news.source})\n    {news.url}\n"
                message += "\n"
            
            if sol_news:
                message += "📰 SOLANA NEWS:\n"
                for news in sol_news[:3]:  # Limit to 3 articles
                    message += f"  • {news.title} ({news.source})\n    {news.url}\n"
            
            # Only send Slack alert if there are actual alerts or significant news
            if alerts or (ovh_news and len(ovh_news) > 0) or (sol_news and len(sol_news) > 0):
                self.send_notification(subject, message, notification_type="alert")
        
        logger.info("Monitoring cycle completed")

def main():
    # Configuration - use environment variables for production
    config = {
        'news_api_key': os.getenv('NEWS_API_KEY', 'cc793418193f491d9184ad7b00785f37'),
        'slack': {
            'enabled': True,
            'webhook_url': os.getenv('SLACK_WEBHOOK_URL', 'YOUR_SLACK_WEBHOOK_URL')
        },
        'email': {
            'enabled': True,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'from_email': os.getenv('EMAIL_FROM', 'robin.langeard@gmail.com'),
            'to_email': os.getenv('EMAIL_TO', 'robin.langeard@gmail.com'),
            'password': os.getenv('EMAIL_PASSWORD', 'YOUR_GMAIL_APP_PASSWORD')
        },
        'thresholds': {
            'OVH': {
                'high': float(os.getenv('OVH_HIGH', '20.0')),
                'low': float(os.getenv('OVH_LOW', '10.0')),
                'change_percent': float(os.getenv('OVH_CHANGE', '5.0'))
            },
            'SOL': {
                'high': float(os.getenv('SOL_HIGH', '180.0')),
                'low': float(os.getenv('SOL_LOW', '90.0')),
                'change_percent': float(os.getenv('SOL_CHANGE', '10.0'))
            }
        }
    }
    
    monitor = FinanceMonitor(config)
    
    # Check if we're running as a one-time task or continuous service
    run_mode = os.getenv('RUN_MODE', 'continuous')
    
    if run_mode == 'continuous':
        # Schedule monitoring every 20 minutes (optimized)
        schedule.every(20).minutes.do(monitor.monitor_assets)
        
        # Schedule daily email reports (Paris timezone)
        schedule.every().day.at("10:00").do(lambda: monitor.send_daily_report("morning"))
        schedule.every().day.at("18:00").do(lambda: monitor.send_daily_report("evening"))
        
        logger.info("🚀 Financial Monitor Bot started in CONTINUOUS mode")
        logger.info("📊 Monitoring OVH.PA and SOL every 20 minutes (optimized)")
        logger.info("📱 Slack alerts for urgent notifications")
        logger.info("📧 Daily email reports at 10:00 and 18:00 Paris time")
        
        # Run once immediately
        monitor.monitor_assets()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    else:
        # Single execution mode (for limited platforms like PythonAnywhere)
        paris_now = datetime.now(pytz.timezone('Europe/Paris'))
        current_hour = paris_now.hour
        
        logger.info(f"🤖 Daily Financial Monitor Execution (Single Run Mode)")
        logger.info(f"⏰ Running at {paris_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Always run monitoring
        monitor.monitor_assets()
        
        # Handle daily reports based on time
        today = paris_now.date()
        
        if current_hour >= 10 and not monitor.has_sent_report_today('morning', today):
            logger.info("🌅 Sending morning report...")
            monitor.send_daily_report("morning")
        
        if current_hour >= 18 and not monitor.has_sent_report_today('evening', today):
            logger.info("🌆 Sending evening report...")
            monitor.send_daily_report("evening")
        
        logger.info("✅ Single execution completed")

if __name__ == "__main__":
    main()
