#!/usr/bin/env python3
"""
Financial & Crypto Monitoring Bot
Monitors OVH stock and Solana cryptocurrency with news alerts
Updated to use Google Finance for stock data
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
from newsapi import NewsApiClient
import schedule
import pytz
import os
from bs4 import BeautifulSoup
import re

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
        
        # Google Finance user agent to avoid blocking
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
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
    
    def parse_google_finance_price(self, html_content: str) -> Optional[Dict]:
        """Parse stock price data from Google Finance HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find price - Google Finance uses specific class names
            price_elem = soup.find('div', class_='YMlKec fxKbKc')
            if not price_elem:
                # Try alternative selector
                price_elem = soup.find('div', attrs={'data-last-price': True})
            
            if not price_elem:
                logger.warning("Could not find price element in Google Finance HTML")
                return None
            
            # Extract price
            price_text = price_elem.text.strip()
            # Remove currency symbols and convert to float
            price_text = re.sub(r'[€$,]', '', price_text)
            current_price = float(price_text)
            
            # Find price change
            change_elem = soup.find('div', class_='JwB6zf')
            if not change_elem:
                # Try to find percentage in parentheses
                change_elem = soup.find('span', class_='NydbP')
            
            change_percent = 0.0
            if change_elem:
                change_text = change_elem.text.strip()
                # Extract percentage from text like "(+1.23%)" or "-1.23%"
                match = re.search(r'[+-]?\d+\.?\d*%', change_text)
                if match:
                    change_percent = float(match.group().replace('%', ''))
            
            # Find previous close
            prev_close_elem = soup.find('div', string=re.compile('Previous close'))
            prev_close = current_price  # Default to current if not found
            if prev_close_elem:
                prev_value = prev_close_elem.find_next_sibling()
                if prev_value:
                    prev_text = re.sub(r'[€$,]', '', prev_value.text.strip())
                    try:
                        prev_close = float(prev_text)
                    except:
                        pass
            
            # Calculate change if not found
            if change_percent == 0.0 and prev_close != current_price:
                change_percent = ((current_price - prev_close) / prev_close) * 100
            
            return {
                'current_price': current_price,
                'previous_close': prev_close,
                'change_percent': change_percent,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing Google Finance HTML: {e}")
            return None
    
    def get_stock_price_google(self, symbol: str) -> Optional[Dict]:
        """Get stock price from Google Finance"""
        # Check if market is open for European stocks
        if symbol.endswith('.PA') and not self.is_euronext_open():
            next_open = self.get_next_market_open()
            logger.info(f"Euronext Paris is closed. Next market open: {next_open.strftime('%Y-%m-%d %H:%M %Z')}")
            return None
        
        try:
            # Convert symbol format for Google Finance
            # Remove .PA suffix and use exchange prefix
            google_symbol = symbol.replace('.PA', '')
            
            # Google Finance URL
            url = f"https://www.google.com/finance/quote/{google_symbol}:EPA"
            
            # Add delay to avoid rate limiting
            time.sleep(0.5)
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML
            price_data = self.parse_google_finance_price(response.text)
            
            if price_data:
                price_data['symbol'] = symbol
                price_data['market_open'] = True
                return price_data
            else:
                logger.warning(f"Could not parse data for {symbol} from Google Finance")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching {symbol} from Google Finance: {e}")
            return None

    def get_solana_price(self) -> Optional[Dict]:
        """Get Solana price from CoinGecko API (free) - converted to EUR"""
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                url = "https://api.coingecko.com/api/v3/simple/price"
                params = {
                    'ids': 'solana',
                    'vs_currencies': 'usd,eur',
                    'include_24hr_change': 'true',
                    'include_24hr_vol': 'true'
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 429:  # Rate limited
                    logger.warning(f"Rate limited by CoinGecko, retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:  # Don't sleep on last attempt
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        logger.error("Max retries reached for CoinGecko API")
                        return None
                
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
                logger.error(f"Error fetching Solana price (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None
        
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
    
    def test_email_configuration(self):
        """Test email configuration by sending a test message"""
        try:
            subject = "🧪 Financial Monitor - Email Test"
            message = """This is a test email from your Financial Monitor Bot.

If you receive this message, your email configuration is working correctly!

✅ SMTP Server: Connected
✅ Authentication: Successful  
✅ Email Delivery: Working

Your morning reports will be sent around 10:00 AM Paris time.
Your evening reports will be sent around 6:00 PM Paris time.

---
Financial Monitor Bot (Google Finance Edition)
"""
            
            self.send_email_notification(subject, message)
            logger.info("📧 Test email sent successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Email test failed: {e}")
            return False
    
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
    
    def get_daily_summary(self) -> Dict:
        """Get daily summary of prices and changes for all assets"""
        summary = {
            'stock_data': {},
            'crypto_data': {},
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
        
        # Get current prices for all stocks
        stock_symbols = self.config.get('stocks', {})
        for symbol, stock_config in stock_symbols.items():
            data = self.get_stock_price_google(symbol)
            if data:
                summary['stock_data'][symbol] = data
        
        # Get current prices for all crypto
        crypto_symbols = self.config.get('crypto', {})
        for symbol, crypto_config in crypto_symbols.items():
            if symbol == 'SOL':
                data = self.get_solana_price()
                if data:
                    summary['crypto_data'][symbol] = data
        
        # Get daily changes from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get prices from 24 hours ago
        yesterday = datetime.now() - timedelta(days=1)
        
        # Check all tracked symbols
        all_symbols = list(stock_symbols.keys()) + list(crypto_symbols.keys())
        for symbol in all_symbols:
            cursor.execute('''
                SELECT price FROM price_history 
                WHERE symbol = ? AND timestamp >= ? 
                ORDER BY timestamp ASC LIMIT 1
            ''', (symbol, yesterday.isoformat()))
            
            result = cursor.fetchone()
            if result:
                old_price = result[0]
                current_price = None
                
                # Get current price
                if symbol in summary['stock_data']:
                    current_price = summary['stock_data'][symbol]['current_price']
                elif symbol in summary['crypto_data']:
                    current_price = summary['crypto_data'][symbol]['current_price_eur']
                
                if current_price:
                    change = ((current_price - old_price) / old_price) * 100
                    asset_name = stock_symbols.get(symbol, crypto_symbols.get(symbol, {})).get('name', symbol)
                    summary['daily_changes'][symbol] = {
                        'name': asset_name,
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
        
        # Show top performing and worst performing assets
        all_assets = []
        
        # Add stocks
        for symbol, data in summary['stock_data'].items():
            stock_config = self.config['stocks'][symbol]
            all_assets.append({
                'name': stock_config['name'],
                'symbol': symbol,
                'price': data['current_price'],
                'change': data['change_percent'],
                'type': '🏢'
            })
        
        # Add crypto
        for symbol, data in summary['crypto_data'].items():
            crypto_config = self.config['crypto'][symbol]
            all_assets.append({
                'name': crypto_config['name'],
                'symbol': symbol,
                'price': data['current_price_eur'],
                'change': data['change_percent_24h'],
                'type': '🪙'
            })
        
        # Sort by change percentage (best to worst)
        all_assets.sort(key=lambda x: x['change'], reverse=True)
        
        # Show top 5 performers and bottom 5
        message += "  📈 TOP PERFORMERS:\n"
        for asset in all_assets[:5]:
            message += f"    {asset['type']} {asset['name']}: €{asset['price']:.2f} ({asset['change']:+.2f}%)\n"
        
        if len(all_assets) > 5:
            message += "  📉 WORST PERFORMERS:\n"
            for asset in all_assets[-3:]:
                message += f"    {asset['type']} {asset['name']}: €{asset['price']:.2f} ({asset['change']:+.2f}%)\n"
        
        message += "\n"
        
        # Daily changes (if available)
        if summary['daily_changes']:
            message += "📈 24-HOUR CHANGES:\n"
            
            # Sort by absolute change percentage
            changes_sorted = sorted(summary['daily_changes'].items(), 
                                  key=lambda x: abs(x[1]['change_percent']), reverse=True)
            
            for symbol, change_data in changes_sorted[:10]:  # Show top 10 changes
                direction = "📈" if change_data['change_percent'] > 0 else "📉" if change_data['change_percent'] < 0 else "➡️"
                message += f"  {direction} {change_data['name']}: {change_data['change_percent']:+.2f}% "
                message += f"(€{change_data['old_price']:.2f} → €{change_data['current_price']:.2f})\n"
            message += "\n"
        
        # Recent news - focus on top assets
        priority_assets = ['OVH.PA', 'STMPA.PA', 'STLAP.PA']  # Most important assets
        news_found = False
        
        for symbol in priority_assets:
            if symbol in self.config.get('stocks', {}):
                stock_config = self.config['stocks'][symbol]
                news_items = self.get_news(f"{stock_config['name']} stock")
                if news_items:
                    if not news_found:
                        message += "📰 PORTFOLIO NEWS (Last 24h):\n"
                        news_found = True
                    for news in news_items[:1]:  # Limit to 1 article per major stock
                        message += f"  • {stock_config['name']}: {news.title}\n"
                        message += f"    {news.source} | {news.url}\n"
        
        # Add Solana news
        sol_news = self.get_news("Solana cryptocurrency OR SOL crypto")
        if sol_news:
            if not news_found:
                message += "📰 PORTFOLIO NEWS (Last 24h):\n"
            for news in sol_news[:1]:  # Limit to 1 article
                message += f"  • Solana: {news.title}\n"
                message += f"    {news.source} | {news.url}\n"
        
        if news_found:
            message += "\n"
        
        # Footer
        message += "=" * 50 + "\n"
        message += "🤖 Automated Financial Monitor (Google Finance) | Next report: "
        if report_type == "morning":
            message += "around 18:00 CET"
        else:
            message += "around 10:00 CET tomorrow"
        message += "\n" + "=" * 50
        
        # Send email report
        self.send_notification(subject, message, notification_type="daily_report")
        
        # Record that we sent this report
        self.record_report_sent(report_type)
        
        logger.info(f"{report_type.capitalize()} daily report sent")
    
    def should_send_daily_report(self) -> Optional[str]:
        """Check if it's time to send a daily report"""
        paris_now = datetime.now(self.paris_tz)
        current_hour = paris_now.hour
        current_minute = paris_now.minute
        today = paris_now.date()
        
        # Morning report window: 9:30 AM - 10:30 AM
        if 9 <= current_hour <= 10 and current_minute >= 30 if current_hour == 9 else current_hour == 10 and current_minute <= 30:
            if not self.has_sent_report_today('morning', today):
                return 'morning'
        
        # Evening report window: 5:30 PM - 6:30 PM
        if 17 <= current_hour <= 18 and current_minute >= 30 if current_hour == 17 else current_hour == 18 and current_minute <= 30:
            if not self.has_sent_report_today('evening', today):
                return 'evening'
        
        return None
    
    def monitor_assets(self):
        """Main monitoring function for multiple assets"""
        logger.info("Starting comprehensive asset monitoring cycle...")
        
        # Check if we should send a daily report during this monitoring cycle
        report_type = self.should_send_daily_report()
        if report_type:
            logger.info(f"📧 Time for {report_type} daily report!")
            self.send_daily_report(report_type)
        
        alerts = []
        market_status = []
        stock_data = {}
        crypto_data = {}
        
        # Check market status
        if self.is_euronext_open():
            market_status.append("🟢 Euronext Paris: OPEN")
        else:
            next_open = self.get_next_market_open()
            market_status.append(f"🔴 Euronext Paris: CLOSED (Next open: {next_open.strftime('%Y-%m-%d %H:%M %Z')})")
        
        market_status.append("🟢 Crypto Markets: ALWAYS OPEN")
        
        # Monitor all stocks from configuration
        stock_symbols = self.config.get('stocks', {})
        logger.info(f"Monitoring {len(stock_symbols)} stocks via Google Finance...")
        
        batch_count = 0
        for symbol, stock_config in stock_symbols.items():
            try:
                # Rate limiting - pause every 5 stocks
                if batch_count > 0 and batch_count % 5 == 0:
                    logger.info(f"Rate limiting pause after {batch_count} stocks...")
                    time.sleep(2)
                
                data = self.get_stock_price_google(symbol)
                if data:
                    # Store price data
                    self.store_price_data(symbol, data['current_price'], 'stock')
                    
                    # Check alerts
                    thresholds = stock_config.get('thresholds', {})
                    stock_alerts = self.check_price_alerts(symbol, data['current_price'], thresholds)
                    alerts.extend(stock_alerts)
                    
                    # Store for reporting
                    stock_data[symbol] = data
                    
                    logger.info(f"{stock_config['name']} ({symbol}): €{data['current_price']:.2f} ({data['change_percent']:+.2f}%)")
                elif symbol.endswith('.PA') and not self.is_euronext_open():
                    logger.info(f"{stock_config['name']} ({symbol}): Market closed")
                else:
                    logger.warning(f"Failed to get data for {symbol}")
                
                batch_count += 1
                    
            except Exception as e:
                logger.error(f"Error monitoring {symbol}: {e}")
                continue
        
        # Monitor cryptocurrencies
        crypto_symbols = self.config.get('crypto', {})
        logger.info(f"Monitoring {len(crypto_symbols)} cryptocurrencies...")
        
        for symbol, crypto_config in crypto_symbols.items():
            try:
                if symbol == 'SOL':
                    data = self.get_solana_price()
                    if data:
                        # Store EUR price in database
                        self.store_price_data(symbol, data['current_price_eur'], 'crypto')
                        
                        thresholds = crypto_config.get('thresholds', {})
                        crypto_alerts = self.check_price_alerts(symbol, data['current_price_eur'], thresholds)
                        alerts.extend(crypto_alerts)
                        
                        # Store for reporting
                        crypto_data[symbol] = data
                        
                        logger.info(f"{crypto_config['name']} ({symbol}): €{data['current_price_eur']:.2f} ({data['change_percent_24h']:+.2f}%) [Rate: {data['exchange_rate_used']:.4f}]")
                
            except Exception as e:
                logger.error(f"Error monitoring {symbol}: {e}")
                continue
        
        # Get news - highly optimized for 37 stocks
        current_minute = datetime.now().minute
        should_check_news = (
            self.is_euronext_open() and current_minute == 0  # Only once per hour during market hours
        )
        
        news_items = []
        if should_check_news:
            logger.info("Checking news for priority assets (API optimized)...")
            # Only check news for top 5 most important assets to save API calls
            priority_stocks = ['OVH.PA', 'STMPA.PA', 'STLAP.PA', 'MT.PA', 'ENGI.PA']
            for symbol in priority_stocks:
                if symbol in stock_data:
                    stock_config = stock_symbols[symbol]
                    try:
                        news_query = f"{stock_config['name']} stock"
                        symbol_news = self.get_news(news_query)
                        if symbol_news:
                            news_items.extend(symbol_news[:1])  # Max 1 news per stock
                    except Exception as e:
                        logger.warning(f"News fetch failed for {symbol}: {e}")
                        continue
        else:
            logger.info("Skipping news check (preserving API limits for 37-stock portfolio)")
        
        # Send notifications if there are alerts
        if alerts:
            subject = f"🚨 Portfolio Alert - {len(alerts)} notifications from {len(stock_symbols)} stocks"
            
            message = "=== 37-STOCK PORTFOLIO MONITORING ALERT ===\n\n"
            
            # Market status
            message += "📊 MARKET STATUS:\n"
            for status in market_status:
                message += f"  {status}\n"
            message += "\n"
            
            # Price alerts
            message += f"🚨 PRICE ALERTS ({len(alerts)}):\n"
            for alert in alerts:
                message += f"  {alert}\n"
            message += "\n"
            
            # Portfolio performance summary
            if stock_data or crypto_data:
                message += "📈 PORTFOLIO PERFORMANCE:\n"
                
                # Combine and sort by absolute change
                all_assets = []
                for symbol, data in stock_data.items():
                    all_assets.append((symbol, data, stock_symbols[symbol]['name'], 'stock'))
                for symbol, data in crypto_data.items():
                    all_assets.append((symbol, data, crypto_symbols[symbol]['name'], 'crypto'))
                
                # Sort by absolute change percentage
                all_assets.sort(key=lambda x: abs(x[1].get('change_percent', x[1].get('change_percent_24h', 0))), reverse=True)
                
                # Show top 3 gainers and top 3 losers
                message += "  🔥 TOP GAINERS:\n"
                gainers = [a for a in all_assets if (a[1].get('change_percent', a[1].get('change_percent_24h', 0)) > 0)][:3]
                for symbol, data, name, type_asset in gainers:
                    change = data.get('change_percent', data.get('change_percent_24h', 0))
                    if type_asset == 'crypto':
                        price = data['current_price_eur']
                    else:
                        price = data['current_price']
                    message += f"    📈 {name}: €{price:.2f} (+{change:.1f}%)\n"
                
                message += "  🩸 TOP LOSERS:\n"
                losers = [a for a in all_assets if (a[1].get('change_percent', a[1].get('change_percent_24h', 0)) < 0)][:3]
                for symbol, data, name, type_asset in losers:
                    change = data.get('change_percent', data.get('change_percent_24h', 0))
                    if type_asset == 'crypto':
                        price = data['current_price_eur']
                    else:
                        price = data['current_price']
                    message += f"    📉 {name}: €{price:.2f} ({change:.1f}%)\n"
                message += "\n"
            
            # News (if any)
            if news_items:
                message += "📰 PRIORITY NEWS:\n"
                for news in news_items[:3]:  # Max 3 news items
                    message += f"  • {news.title} ({news.source})\n"
                message += "\n"
            
            message += f"📊 Portfolio: {len(stock_data)} stocks active + {len(crypto_data)} crypto\n"
            message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CET"
            
            self.send_notification(subject, message, notification_type="alert")
        
        # Summary logging
        total_monitored = len([d for d in stock_data.values() if d]) + len([d for d in crypto_data.values() if d])
        total_errors = len(stock_symbols) + len(crypto_symbols) - total_monitored
        logger.info(f"📊 Monitoring cycle completed:")
        logger.info(f"   ✅ {total_monitored} assets successfully monitored")
        logger.info(f"   ⚠️ {total_errors} assets failed/skipped") 
        logger.info(f"   🚨 {len(alerts)} alerts generated")
        logger.info(f"   📰 {len(news_items)} news items collected")

def main():
    # YOUR 37 SPECIFIC STOCKS - Update thresholds based on your investment strategy
    default_stocks = {
        # Tech & Gaming
        "PARRO.PA": {"name": "Parrot", "thresholds": {"high": 15.0, "low": 3.0, "change_percent": 15.0}},
        "STMPA.PA": {"name": "STMicroelectronics", "thresholds": {"high": 35.0, "low": 15.0, "change_percent": 8.0}},
        "ALCJ.PA": {"name": "CROSSJECT", "thresholds": {"high": 2.0, "low": 0.5, "change_percent": 20.0}},
        "UBI.PA": {"name": "Ubisoft", "thresholds": {"high": 25.0, "low": 8.0, "change_percent": 12.0}},
        "ALDNE.PA": {"name": "DON'T NOD", "thresholds": {"high": 30.0, "low": 10.0, "change_percent": 15.0}},
        "ALLDL.PA": {"name": "Groupe LDLC", "thresholds": {"high": 60.0, "low": 30.0, "change_percent": 10.0}},
        "ALLIX.PA": {"name": "Wallix Group SA", "thresholds": {"high": 20.0, "low": 5.0, "change_percent": 15.0}},
        "DEEZR.PA": {"name": "Deezer SA", "thresholds": {"high": 5.0, "low": 1.0, "change_percent": 20.0}},
        "AL2SI.PA": {"name": "2CRSi", "thresholds": {"high": 10.0, "low": 3.0, "change_percent": 15.0}},
        
        # Green Energy & Environment
        "ALEUP.PA": {"name": "Europlasma", "thresholds": {"high": 1.0, "low": 0.05, "change_percent": 25.0}},
        "ALDRV.PA": {"name": "Drone Volt SA", "thresholds": {"high": 0.5, "low": 0.05, "change_percent": 20.0}},
        "ALHRS.PA": {"name": "Hydrogen Refueling Solutions", "thresholds": {"high": 5.0, "low": 1.0, "change_percent": 20.0}},
        "ALDLT.PA": {"name": "Delta Drone SA", "thresholds": {"high": 1.0, "low": 0.1, "change_percent": 20.0}},
        "ALLHY.PA": {"name": "Lhyfe SA", "thresholds": {"high": 15.0, "low": 5.0, "change_percent": 15.0}},
        "ALCRB.PA": {"name": "Carbios", "thresholds": {"high": 15.0, "low": 3.0, "change_percent": 15.0}},
        "ARVEN.PA": {"name": "Arverne Group", "thresholds": {"high": 10.0, "low": 3.0, "change_percent": 15.0}},
        "ALWTR.PA": {"name": "Osmosun SA", "thresholds": {"high": 5.0, "low": 1.0, "change_percent": 20.0}},
        
        # Healthcare & Biotech
        "ALCAR.PA": {"name": "Carmat", "thresholds": {"high": 15.0, "low": 3.0, "change_percent": 15.0}},
        "ALNFL.PA": {"name": "NFL Biosciences SA", "thresholds": {"high": 5.0, "low": 1.0, "change_percent": 20.0}},
        "VALN.PA": {"name": "Valneva SE", "thresholds": {"high": 10.0, "low": 2.0, "change_percent": 15.0}},
        
        # Large Caps & Industrial
        "OVH.PA": {"name": "OVH Groupe SAS", "thresholds": {"high": 20.0, "low": 10.0, "change_percent": 5.0}},
        "ATO.PA": {"name": "Atos", "thresholds": {"high": 5.0, "low": 0.5, "change_percent": 15.0}},
        "MT.PA": {"name": "ArcelorMittal", "thresholds": {"high": 30.0, "low": 15.0, "change_percent": 8.0}},
        "ENGI.PA": {"name": "Engie", "thresholds": {"high": 18.0, "low": 10.0, "change_percent": 6.0}},
        "STLAP.PA": {"name": "Stellantis", "thresholds": {"high": 20.0, "low": 8.0, "change_percent": 10.0}},
        "EN.PA": {"name": "Bouygues", "thresholds": {"high": 40.0, "low": 25.0, "change_percent": 6.0}},
        "CA.PA": {"name": "Carrefour", "thresholds": {"high": 18.0, "low": 12.0, "change_percent": 6.0}},
        "FRVIA.PA": {"name": "Forvia", "thresholds": {"high": 20.0, "low": 10.0, "change_percent": 10.0}},
        
        # Services & Consumer
        "KOF.PA": {"name": "Kaufman & Broad", "thresholds": {"high": 40.0, "low": 20.0, "change_percent": 10.0}},
        "ETL.PA": {"name": "Eutelsat Communications", "thresholds": {"high": 10.0, "low": 3.0, "change_percent": 12.0}},
        "ELIOR.PA": {"name": "Elior Group", "thresholds": {"high": 10.0, "low": 3.0, "change_percent": 12.0}},
        "SBT.PA": {"name": "Œneo", "thresholds": {"high": 15.0, "low": 8.0, "change_percent": 10.0}},
        "PLX.PA": {"name": "Pluxee NV", "thresholds": {"high": 30.0, "low": 20.0, "change_percent": 8.0}},
        "CRI.PA": {"name": "Chargeurs", "thresholds": {"high": 20.0, "low": 10.0, "change_percent": 10.0}},
        "ALVIN.PA": {"name": "Vinpai SA", "thresholds": {"high": 10.0, "low": 3.0, "change_percent": 15.0}},
        "FDJ.PA": {"name": "FDJ (La Française des Jeux)", "thresholds": {"high": 40.0, "low": 30.0, "change_percent": 8.0}},
        "ALLPL.PA": {"name": "Lepermislibre", "thresholds": {"high": 5.0, "low": 1.0, "change_percent": 20.0}}
    }
    
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
        'stocks': default_stocks,
        'crypto': {
            'SOL': {
                'name': 'Solana',
                'thresholds': {
                    'high': float(os.getenv('SOL_HIGH', '180.0')),
                    'low': float(os.getenv('SOL_LOW', '90.0')),
                    'change_percent': float(os.getenv('SOL_CHANGE', '10.0'))
                }
            }
        }
    }
    
    monitor = FinanceMonitor(config)
    
    # Check if we're running as a one-time task or continuous service
    run_mode = os.getenv('RUN_MODE', 'continuous')
    
    if run_mode == 'continuous':
        # Schedule monitoring every 20 minutes
        schedule.every(20).minutes.do(monitor.monitor_assets)
        
        logger.info("🚀 Financial Monitor Bot started in CONTINUOUS mode (Google Finance Edition)")
        logger.info(f"📊 Monitoring {len(config['stocks'])} French stocks via Google Finance + {len(config['crypto'])} cryptocurrencies")
        logger.info("📱 Slack alerts for urgent notifications")
        logger.info("📧 Daily email reports around 10:00 and 18:00 Paris time (sent during regular monitoring)")
        logger.info(f"🏢 Portfolio: {len(default_stocks)} French stocks including CAC40 components")
        
        # Test email configuration on first startup
        logger.info("🧪 Testing email configuration...")
        if monitor.test_email_configuration():
            logger.info("✅ Email test successful - you should receive a test email shortly")
        else:
            logger.warning("❌ Email test failed - check your Gmail App Password configuration")
        
        # Run once immediately
        monitor.monitor_assets()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    else:
        # Single execution mode (for limited platforms like PythonAnywhere)
        paris_now = datetime.now(pytz.timezone('Europe/Paris'))
        
        logger.info(f"🤖 Daily Financial Monitor Execution (Single Run Mode - Google Finance)")
        logger.info(f"⏰ Running at {paris_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Always run monitoring (which will check if daily reports are needed)
        monitor.monitor_assets()
        
        logger.info("✅ Single execution completed")

if __name__ == "__main__":
    main()
