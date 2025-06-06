def monitor_assets(self):
        """Main monitoring function for multiple assets with enhanced notifications"""
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
        logger.info(f"Monitoring {len(stock_symbols)} stocks via Yahoo Finance...")
        
        for symbol, stock_config in stock_symbols.items():
            try:
                data = self.get_stock_price(symbol)
                if data:
                    # Store price data
                    self.store_price_data(symbol, data['current_price'], 'stock')
                    
                    # Check alerts with enhanced formatting
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
                    
            except Exception as e:
                logger.error(f"Error monitoring {symbol}: {e}")
                continue
        
        # Monitor all cryptocurrencies (efficient bulk fetch)
        crypto_symbols = self.config.get('crypto', {})
        logger.info(f"Monitoring {len(crypto_symbols)} cryptocurrencies via CoinGecko...")
        
        try:
            all_crypto_data = self.get_all_crypto_prices()
            
            for symbol, crypto_config in crypto_symbols.items():
                if symbol in all_crypto_data:
                    data = all_crypto_data[symbol]
                    
                    # Store EUR price in database
                    if data['current_price_eur']:
                        self.store_price_data(symbol, data['current_price_eur'], 'crypto')
                        
                        thresholds = crypto_config.get('thresholds', {})
                        crypto_alerts = self.check_price_alerts(symbol, data['current_price_eur'], thresholds)
                        alerts.extend(crypto_alerts)
                        
                        # Store for reporting
                        crypto_data[symbol] = data
                        
                        logger.info(f"{crypto_config['name']} ({symbol}): €{data['current_price_eur']:.4f} ({data['change_percent_24h']:+.2f}%)")
                    else:
                        logger.warning(f"No EUR price available for {symbol}")
                else:
                    logger.warning(f"No data returned for {symbol}")
                    
        except Exception as e:
            logger.error(f"Error monitoring cryptocurrencies: {e}")
        
        # Get news - highly optimized for large portfolio
        current_minute = datetime.now().minute
        should_check_news = (
            self.is_euronext_open() and current_minute == 0  # Only once per hour during market hours
        )
        
        news_items = []
        if should_check_news:
            logger.info("Checking news for priority assets (API optimized)...")
            # Only check news for top assets to save API calls
            priority_stocks = ['OVH.PA', 'STMPA.PA', 'STLAP.PA', 'MT.PA', 'ENGI.PA']
            priority_crypto = ['ETH', 'SOL', 'DOGE']
            
            # Stock news
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
            
            # Crypto news
            for symbol in priority_crypto:
                if symbol in crypto_data:
                    crypto_config = crypto_symbols[symbol]
                    try:
                        news_query = f"{crypto_config['name']} cryptocurrency"
                        symbol_news = self.get_news(news_query)
                        if symbol_news:
                            news_items.extend(symbol_news[:1])  # Max 1 news per crypto
                    except Exception as e:
                        logger.warning(f"News fetch failed for {symbol}: {e}")
                        continue
        else:
            logger.info("Skipping news check (preserving API limits for large portfolio)")
        
        # Send enhanced notifications if there are alerts
        if alerts:
            subject = f"🚨 Portfolio Alert - {len(alerts)} notifications from enhanced portfolio"
            
            # Create enhanced alert message
            message = self.create_enhanced_alert_message(alerts, market_status, stock_data, crypto_data, news_items)
            
            self.send_notification(subject, message, notification_type="alert")
        
        # Summary logging with visual enhancements
        total_monitored = len([d for d in stock_data.values() if d]) + len([d for d in crypto_data.values() if d])
        total_possible = len(stock_symbols) + len(crypto_symbols)
        total_errors = total_possible - total_monitored
        
        logger.info("=" * 60)
        logger.info("📊 ENHANCED MONITORING CYCLE COMPLETED")
        logger.info("=" * 60)
        logger.info(f"✅ Successfully monitored: {total_monitored}/{total_possible} assets")
        logger.info(f"🏢 Stocks active: {len(stock_data)}")
        logger.info(f"🪙 Cryptocurrencies active: {len(crypto_data)}")
        logger.info(f"⚠️  Assets failed/skipped: {total_errors}") 
        logger.info(f"🚨 Alerts generated: {len(alerts)}")
        logger.info(f"📰 News items collected: {len(news_items)}")
        logger.info("=" * 60)
    
    def create_enhanced_alert_message(self, alerts: List[str], market_status: List[str], 
                                    stock_data: Dict, crypto_data: Dict, news_items: List) -> str:
        """Create visually enhanced alert message for notifications"""
        
        # Header with clear visual hierarchy
        message = "🚨 ENHANCED PORTFOLIO MONITORING ALERT\n"
        message += "=" * 50 + "\n\n"
        
        # Market status with color indicators
        message += "📊 MARKET STATUS:\n"
        for status in market_status:
            if "OPEN" in status:
                message += f"  ✅ {status}\n"
            else:
                message += f"  ❌ {status}\n"
        message += "\n"
        
        # Enhanced price alerts with clear formatting
        message += f"🚨 PRICE ALERTS ({len(alerts)}):\n"
        message += "─" * 50 + "\n\n"
        
        for i, alert in enumerate(alerts, 1):
            message += f"ALERT #{i}:\n{alert}\n"
            if i < len(alerts):
                message += "─" * 30 + "\n\n"
        
        message += "\n"
        
        # Portfolio performance summary
        if stock_data or crypto_data:
            message += "📈 CURRENT PORTFOLIO SNAPSHOT:\n"
            
            # Combine and sort by absolute change
            all_assets = []
            for symbol, data in stock_data.items():
                all_assets.append((symbol, data, self.config['stocks'][symbol]['name'], 'stock'))
            for symbol, data in crypto_data.items():
                all_assets.append((symbol, data, self.config['crypto'][symbol]['name'], 'crypto'))
            
            # Sort by absolute change percentage
            all_assets.sort(key=lambda x: abs(x[1].get('change_percent', x[1].get('change_percent_24h', 0))), reverse=True)
            
            # Show top movers
            message += "\n🔥 BIGGEST MOVERS:\n"
            for symbol, data, name, asset_type in all_assets[:5]:
                change = data.get('change_percent', data.get('change_percent_24h', 0))
                if asset_type == 'crypto':
                    price = data['current_price_eur']
                    type_emoji = "🪙"
                    price_str = f"€{price:.4f}"
                else:
                    price = data['current_price']
                    type_emoji = "🏢"
                    price_str = f"€{price:.2f}"
                
                direction = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                message += f"  {direction} {type_emoji} {name}: {price_str} ({change:+.2f}%)\n"
            message += "\n"
        
        # News section (if any)
        if news_items:
            message += "📰 LATEST NEWS:\n"
            for news in news_items[:3]:  # Limit to 3 news items
                message += f"  • {news.title}\n"
                message += f"    Source: {news.source} | {news.url}\n\n"
        
        # Enhanced footer with key metrics
        message += "=" * 50 + "\n"
        message += f"📊 Portfolio: {len(stock_data)} stocks + {len(crypto_data)} crypto active\n"
        message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CET\n"
        message += f"🤖 Enhanced Financial Monitor v2.0"
        
        return message


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
    
    # ALL CRYPTOCURRENCIES from your list with reasonable default thresholds
    default_crypto = {
        'ETH': {'name': 'Ethereum', 'thresholds': {'high': 4000.0, 'low': 2000.0, 'change_percent': 8.0}},
        'SOL': {'name': 'Solana', 'thresholds': {'high': 180.0, 'low': 90.0, 'change_percent': 10.0}},
        'DOGE': {'name': 'Dogecoin', 'thresholds': {'high': 0.5, 'low': 0.1, 'change_percent': 15.0}},
        'ADA': {'name': 'Cardano', 'thresholds': {'high': 1.0, 'low': 0.3, 'change_percent': 12.0}},
        'LINK': {'name': 'Chainlink', 'thresholds': {'high': 30.0, 'low': 10.0, 'change_percent': 12.0}},
        'ZEC': {'name': 'Zcash', 'thresholds': {'high': 100.0, 'low': 30.0, 'change_percent': 15.0}},
        'PEPE': {'name': 'Pepe', 'thresholds': {'high': 0.00003, 'low': 0.000005, 'change_percent': 20.0}},
        'UNI': {'name': 'Uniswap', 'thresholds': {'high': 15.0, 'low': 5.0, 'change_percent': 15.0}},
        'CRO': {'name': 'Cronos', 'thresholds': {'high': 0.2, 'low': 0.05, 'change_percent': 15.0}},
        'MNT': {'name': 'Mantle', 'thresholds': {'high': 1.5, 'low': 0.5, 'change_percent': 15.0}},
        'RENDER': {'name': 'Render', 'thresholds': {'high': 10.0, 'low': 3.0, 'change_percent': 15.0}},
        'FET': {'name': 'Artificial Superintelligence Alliance', 'thresholds': {'high': 2.0, 'low': 0.5, 'change_percent': 15.0}},
        'ARB': {'name': 'Arbitrum', 'thresholds': {'high': 2.0, 'low': 0.5, 'change_percent': 15.0}},
        'FIL': {'name': 'Filecoin', 'thresholds': {'high': 10.0, 'low': 3.0, 'change_percent': 15.0}},
        'ALGO': {'name': 'Algorand', 'thresholds': {'high': 0.5, 'low': 0.1, 'change_percent': 15.0}},
        'MKR': {'name': 'Sky', 'thresholds': {'high': 2000.0, 'low': 800.0, 'change_percent': 12.0}},
        'GRT': {'name': 'The Graph', 'thresholds': {'high': 0.5, 'low': 0.1, 'change_percent': 15.0}},
        'ENS': {'name': 'Ethereum Name Service', 'thresholds': {'high': 50.0, 'low': 15.0, 'change_percent': 15.0}},
        'GALA': {'name': 'Gala', 'thresholds': {'high': 0.1, 'low': 0.02, 'change_percent': 20.0}},
        'FLOW': {'name': 'Flow', 'thresholds': {'high': 2.0, 'low': 0.5, 'change_percent': 15.0}},
        'MANA': {'name': 'Decentraland', 'thresholds': {'high': 1.0, 'low': 0.3, 'change_percent': 15.0}},
        'STRK': {'name': 'Starknet', 'thresholds': {'high': 3.0, 'low': 1.0, 'change_percent': 15.0}},
        'EIGEN': {'name': 'EigenLayer', 'thresholds': {'high': 10.0, 'low': 2.0, 'change_percent': 15.0}},
        'EGLD': {'name': 'MultiversX', 'thresholds': {'high': 50.0, 'low': 20.0, 'change_percent': 12.0}},
        'MOVE': {'name': 'Movement', 'thresholds': {'high': 2.0, 'low': 0.5, 'change_percent': 20.0}},
        'LPT': {'name': 'Livepeer', 'thresholds': {'high': 30.0, 'low': 10.0, 'change_percent': 15.0}},
        'MOG': {'name': 'Mog Coin', 'thresholds': {'high': 0.000005, 'low': 0.000001, 'change_percent': 25.0}},
        'MASK': {'name': 'Mask Network', 'thresholds': {'high': 5.0, 'low': 2.0, 'change_percent': 15.0}},
        'MINA': {'name': 'Mina', 'thresholds': {'high': 2.0, 'low': 0.5, 'change_percent': 15.0}},
        'BAT': {'name': 'Basic Attention Token', 'thresholds': {'high': 0.5, 'low': 0.15, 'change_percent': 15.0}},
        'ENJ': {'name': 'Enjin Coin', 'thresholds': {'high': 0.5, 'low': 0.15, 'change_percent': 15.0}},
        'COTI': {'name': 'COTI', 'thresholds': {'high': 0.3, 'low': 0.05, 'change_percent': 20.0}},
        'BAND': {'name': 'Band Protocol', 'thresholds': {'high': 5.0, 'low': 1.0, 'change_percent': 15.0}},
        'UMA': {'name': 'UMA', 'thresholds': {'high': 5.0, 'low': 1.5, 'change_percent': 15.0}},
        'BICO': {'name': 'Biconomy', 'thresholds': {'high': 1.0, 'low': 0.3, 'change_percent': 20.0}},
        'KEEP': {'name': 'Keep Network', 'thresholds': {'high': 0.5, 'low': 0.1, 'change_percent': 20.0}},
        'POWR': {'name': 'Powerledger', 'thresholds': {'high': 0.5, 'low': 0.1, 'change_percent': 20.0}},
        'AUDIO': {'name': 'Audius', 'thresholds': {'high': 0.5, 'low': 0.1, 'change_percent': 20.0}},
        'RLC': {'name': 'iExec RLC', 'thresholds': {'high': 5.0, 'low': 1.0, 'change_percent': 15.0}},
        'SAGA': {'name': 'Saga', 'thresholds': {'high': 5.0, 'low': 1.0, 'change_percent': 20.0}},
        'CTSI': {'name': 'Cartesi', 'thresholds': {'high': 0.5, 'low': 0.1, 'change_percent': 20.0}},
        'SCRT': {'name': 'Secret', 'thresholds': {'high': 1.0, 'low': 0.3, 'change_percent': 15.0}},
        'TNSR': {'name': 'Tensor', 'thresholds': {'high': 2.0, 'low': 0.5, 'change_percent': 20.0}},
        'C98': {'name': 'Coin98', 'thresholds': {'high': 0.5, 'low': 0.1, 'change_percent': 20.0}},
        'OGN': {'name': 'Origin Protocol', 'thresholds': {'high': 0.3, 'low': 0.05, 'change_percent': 20.0}},
        'RAD': {'name': 'Radworks', 'thresholds': {'high': 5.0, 'low': 1.0, 'change_percent': 20.0}},
        'NYM': {'name': 'NYM', 'thresholds': {'high': 0.5, 'low': 0.1, 'change_percent': 20.0}},
        'ARPA': {'name': 'ARPA', 'thresholds': {'high': 0.2, 'low': 0.03, 'change_percent': 20.0}},
        'ALCX': {'name': 'Alchemix', 'thresholds': {'high': 50.0, 'low': 15.0, 'change_percent': 15.0}},
        'ATLAS': {'name': 'Star Atlas', 'thresholds': {'high': 0.01, 'low': 0.003, 'change_percent': 25.0}},
        'POLIS': {'name': 'Star Atlas DAO', 'thresholds': {'high': 1.0, 'low': 0.2, 'change_percent': 20.0}},
        'PERP': {'name': 'Perpetual Protocol', 'thresholds': {'high': 2.0, 'low': 0.5, 'change_percent': 15.0}},
        'STEP': {'name': 'Step Finance', 'thresholds': {'high': 0.1, 'low': 0.02, 'change_percent': 25.0}},
        'RBN': {'name': 'Robonomics.network', 'thresholds': {'high': 5.0, 'low': 1.0, 'change_percent': 20.0}},
        'KP3R': {'name': 'Keep3rV1', 'thresholds': {'high': 100.0, 'low': 30.0, 'change_percent': 15.0}},
        'KEY': {'name': 'SelfKey', 'thresholds': {'high': 0.02, 'low': 0.005, 'change_percent': 25.0}},
        'KILT': {'name': 'KILT Protocol', 'thresholds': {'high': 2.0, 'low': 0.5, 'change_percent': 20.0}},
        'TEER': {'name': 'Integritee Network', 'thresholds': {'high': 0.5, 'low': 0.1, 'change_percent': 25.0}},
        'CRU': {'name': 'Crust Shadow', 'thresholds': {'high': 2.0, 'low': 0.5, 'change_percent': 20.0}},
        'ZEUS': {'name': 'Zeus Network', 'thresholds': {'high': 1.0, 'low': 0.3, 'change_percent': 25.0}},
        'MC': {'name': 'Merit Circle', 'thresholds': {'high': 1.0, 'low': 0.2, 'change_percent': 20.0}}
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
        'crypto': default_crypto
    }
    
    monitor = FinanceMonitor(config)
    
    # Check if we're running as a one-time task or continuous service
    run_mode = os.getenv('RUN_MODE', 'continuous')
    
    if run_mode == 'continuous':
        # Intelligent scheduling based on market hours
        def smart_schedule():
            paris_now = datetime.now(pytz.timezone('Europe/Paris'))
            is_market_open = monitor.is_euronext_open()
            
            if is_market_open:
                # During market hours: monitor every 20 minutes (stocks + crypto)
                schedule.every(20).minutes.do(monitor.monitor_assets)
                logger.info("📊 Market hours: Monitoring every 20 minutes (stocks + crypto)")
            else:
                # After hours: monitor every 60 minutes (crypto only, save resources)
                schedule.every(60).minutes.do(monitor.monitor_assets)
                logger.info("🌙 After hours: Monitoring every 60 minutes (crypto focus)")
        
        # Initial smart scheduling
        smart_schedule()
        
        # Re-evaluate schedule every 4 hours to adapt to market open/close
        schedule.every(4).hours.do(smart_schedule)
        
        logger.info("🚀 Enhanced Financial Monitor Bot started in CONTINUOUS mode with SMART SCHEDULING")
        logger.info(f"📊 Monitoring {len(config['stocks'])} French stocks via Yahoo Finance + {len(config['crypto'])} cryptocurrencies via CoinGecko")
        logger.info("💱 All prices converted to EUR for consistency")
        logger.info("📱 Slack alerts for urgent notifications")
        logger.info("📧 Daily email reports around 10:00 and 18:00 Paris time")
        logger.info(f"🏢 Stocks: {len(default_stocks)} French companies")
        logger.info(f"🪙 Crypto: {len(default_crypto)} cryptocurrencies")
        logger.info("⚡ CoinGecko API optimized with bulk fetching and caching")
        logger.info("🧠 Smart scheduling: 20min (market hours) / 60min (after hours)")
        logger.info("🎨 Enhanced UI/UX: Color-coded alerts, HTML emails, professional design")
        
        # Test email configuration on first startup
        logger.info("🧪 Testing email configuration...")
        if monitor.test_email_configuration():
            logger.info("✅ Email test successful - you should receive a test email shortly")
        else:
            logger.warning("❌ Email test failed - check your Gmail App Password configuration")
        
        # Display current year's holidays for transparency
        current_year = datetime.now().year
        holidays = monitor.get_euronext_holidays(current_year)
        logger.info(f"📅 {current_year} Euronext Paris Market Holidays:")
        for holiday in holidays:
            holiday_names = {
                (1, 1): "New Year's Day",
                (5, 1): "Labour Day", 
                (5, 8): "Victory in Europe Day",
                (7, 14): "Bastille Day",
                (8, 15): "Assumption of Mary",
                (11, 1): "All Saints' Day",
                (11, 11): "Armistice Day",
                (12, 25): "Christmas Day",
                (12, 26): "Boxing Day"
            }
            
            # Check if it's an Easter-related holiday
            easter = monitor.calculate_easter_date(current_year)
            if holiday == easter - timedelta(days=2):
                name = "Good Friday"
            elif holiday == easter + timedelta(days=1):
                name = "Easter Monday"
            elif holiday == easter + timedelta(days=39):
                name = "Ascension Day"
            elif holiday == easter + timedelta(days=50):
                name = "Whit Monday"
            else:
                name = holiday_names.get((holiday.month, holiday.day), "Unknown Holiday")
            
            logger.info(f"   🗓️ {holiday.strftime('%B %d, %Y')} - {name}")
        
        # Run once immediately
        monitor.monitor_assets()
        
        # Keep running with smart scheduling
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    else:
        # Single execution mode (for limited platforms like PythonAnywhere)
        paris_now = datetime.now(pytz.timezone('Europe/Paris'))
        
        logger.info(f"🤖 Enhanced Daily Financial Monitor Execution (Single Run Mode)")
        logger.info(f"⏰ Running at {paris_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"📊 Portfolio: {len(config['stocks'])} stocks + {len(config['crypto'])} cryptocurrencies")
        logger.info(f"🎨 Enhanced with visual improvements and HTML email formatting")
        
        # Always run monitoring (which will check if daily reports are needed)
        monitor.monitor_assets()
        
        logger.info("✅ Single execution completed")

if __name__ == "__main__":
    main()#!/usr/bin/env python3
"""
Financial & Crypto Monitoring Bot
Monitors 37 French stocks and 60+ cryptocurrencies with news alerts
Uses Yahoo Finance with automatic EUR conversion
Enhanced with professional UI/UX design and visual clarity
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
        
        # CoinGecko API cache to avoid rate limits
        self.coingecko_cache = {}
        self.last_coingecko_update = None
        
        # Dynamic holiday calculation (updates automatically each year)
        self.market_holidays_cache = {}
        self.last_holiday_update_year = None
        
        # CoinGecko ID mapping for cryptocurrencies
        self.crypto_id_mapping = {
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
            'FET': 'fetch-ai',  # Artificial Superintelligence Alliance
            'ARB': 'arbitrum',
            'FIL': 'filecoin',
            'ALGO': 'algorand',
            'MKR': 'maker',  # Sky (formerly MakerDAO)
            'GRT': 'the-graph',
            'ENS': 'ethereum-name-service',
            'GALA': 'gala',
            'FLOW': 'flow',
            'MANA': 'decentraland',
            'STRK': 'starknet',
            'EIGEN': 'eigenlayer',
            'EGLD': 'elrond-erd-2',  # MultiversX
            'MOVE': 'move-protocol',
            'LPT': 'livepeer',
            'MOG': 'mog-coin',
            'MASK': 'mask-network',
            'MINA': 'mina-protocol',
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
            'ATLAS': 'star-atlas',
            'POLIS': 'star-atlas-dao',
            'PERP': 'perpetual-protocol',
            'STEP': 'step-finance',
            'RBN': 'robonomics-network',
            'KP3R': 'keep3rv1',
            'KEY': 'selfkey',
            'KILT': 'kilt-protocol',
            'TEER': 'integritee',
            'CRU': 'crust-network',
            'ZEUS': 'zeus-network',
            'MC': 'merit-circle'
        }
    
    def calculate_easter_date(self, year: int) -> datetime:
        """Calculate Easter Sunday date for a given year using the algorithm"""
        # Using the anonymous Gregorian algorithm
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        
        return datetime(year, month, day)
    
    def get_euronext_holidays(self, year: int) -> List[datetime]:
        """Calculate Euronext Paris holidays for a given year"""
        # Check cache first
        if (self.last_holiday_update_year == year and 
            year in self.market_holidays_cache):
            return self.market_holidays_cache[year]
        
        holidays = []
        
        # Fixed holidays that are the same every year
        fixed_holidays = [
            (1, 1),   # New Year's Day
            (5, 1),   # Labour Day
            (5, 8),   # Victory in Europe Day (WWII)
            (7, 14),  # Bastille Day (French National Day)
            (8, 15),  # Assumption of Mary
            (11, 1),  # All Saints' Day
            (11, 11), # Armistice Day (WWI)
            (12, 25), # Christmas Day
            (12, 26), # Boxing Day
        ]
        
        # Add fixed holidays
        for month, day in fixed_holidays:
            holidays.append(datetime(year, month, day))
        
        # Calculate Easter-dependent holidays
        easter_sunday = self.calculate_easter_date(year)
        
        # Good Friday (2 days before Easter)
        good_friday = easter_sunday - timedelta(days=2)
        holidays.append(good_friday)
        
        # Easter Monday (1 day after Easter)
        easter_monday = easter_sunday + timedelta(days=1)
        holidays.append(easter_monday)
        
        # Ascension Day (39 days after Easter)
        ascension_day = easter_sunday + timedelta(days=39)
        holidays.append(ascension_day)
        
        # Whit Monday (50 days after Easter)
        whit_monday = easter_sunday + timedelta(days=50)
        holidays.append(whit_monday)
        
        # Sort holidays chronologically
        holidays.sort()
        
        # Cache the results
        self.market_holidays_cache[year] = holidays
        self.last_holiday_update_year = year
        
        logger.info(f"📅 Calculated {len(holidays)} Euronext Paris holidays for {year}")
        
        return holidays
    
    def is_euronext_holiday(self, date: datetime) -> bool:
        """Check if a specific date is a Euronext Paris holiday"""
        year = date.year
        holidays = self.get_euronext_holidays(year)
        
        # Check if the date (ignoring time) matches any holiday
        date_only = date.date()
        for holiday in holidays:
            if holiday.date() == date_only:
                return True
        return False
    
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
        
        # Check if it's a holiday using dynamic calculation
        if self.is_euronext_holiday(now_paris):
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
        max_days_to_check = 14  # Prevent infinite loop
        days_checked = 0
        
        while days_checked < max_days_to_check:
            # Skip weekends
            if next_day.weekday() >= 5:
                next_day += timedelta(days=1)
                days_checked += 1
                continue
            
            # Skip holidays using dynamic calculation
            if self.is_euronext_holiday(next_day):
                next_day += timedelta(days=1)
                days_checked += 1
                continue
            
            return next_day
        
        # Fallback if something goes wrong
        logger.warning("Could not find next market open date within 14 days")
        return next_day
    
    def get_stock_price(self, symbol: str) -> Optional[Dict]:
        """Get stock price from Yahoo Finance with EUR conversion"""
        # Check if market is open for European stocks
        if symbol.endswith('.PA') and not self.is_euronext_open():
            next_open = self.get_next_market_open()
            logger.info(f"Euronext Paris is closed. Next market open: {next_open.strftime('%Y-%m-%d %H:%M %Z')}")
            return None
            
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current data
            info = ticker.info
            hist = ticker.history(period="1d", interval="1m")
            
            if hist.empty:
                logger.warning(f"No data found for {symbol}")
                return None
            
            # Get prices
            current_price = float(hist['Close'].iloc[-1])
            prev_close = float(info.get('previousClose', current_price))
            
            # Get currency
            currency = info.get('currency', 'EUR')
            
            # Convert to EUR if needed
            if currency != 'EUR':
                if currency == 'USD':
                    rate = self.get_usd_to_eur_rate()
                    current_price = current_price * rate
                    prev_close = prev_close * rate
                else:
                    logger.warning(f"Unknown currency {currency} for {symbol}, using raw values")
            
            # Calculate change
            change_percent = ((current_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0
            
            # Get volume
            volume = int(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'previous_close': prev_close,
                'change_percent': change_percent,
                'volume': volume,
                'currency': 'EUR',  # Always EUR after conversion
                'timestamp': datetime.now().isoformat(),
                'market_open': True
            }
            
        except Exception as e:
            logger.error(f"Error recording report: {e}")
    
    def test_email_configuration(self):
        """Test email configuration by sending a test message"""
        try:
            subject = "🧪 Enhanced Financial Monitor - Email Test"
            message = """This is a test email from your Enhanced Financial Monitor Bot.

If you receive this message, your email configuration is working correctly!

✅ SMTP Server: Connected
✅ Authentication: Successful  
✅ Email Delivery: Working

Your monitoring covers:
📊 37 French stocks via Yahoo Finance
🪙 60+ cryptocurrencies via CoinGecko

Your morning reports will be sent around 10:00 AM Paris time.
Your evening reports will be sent around 6:00 PM Paris time.

---
Enhanced Financial Monitor Bot v2.0
"""
            
            self.send_email_notification(subject, message)
            logger.info("📧 Test email sent successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Email test failed: {e}")
            return False
    
    def create_html_email(self, subject: str, content: str, report_type: str = None) -> str:
        """Create professional HTML email with enhanced formatting"""
        paris_time = datetime.now(self.paris_tz)
        
        # Parse content to create structured HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin: 25px 0;
            padding: 20px;
            border-left: 4px solid #667eea;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        .section h2 {{
            margin-top: 0;
            color: #333;
            font-size: 20px;
        }}
        .asset-grid {{
            display: grid;
            gap: 10px;
            margin: 15px 0;
        }}
        .asset-row {{
            padding: 12px;
            background: white;
            border-radius: 5px;
            border-left: 3px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s ease;
        }}
        .asset-row:hover {{
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .asset-row.gain {{
            border-left-color: #28a745;
            background: #f0fff4;
        }}
        .asset-row.loss {{
            border-left-color: #dc3545;
            background: #fff5f5;
        }}
        .asset-info {{
            flex: 1;
        }}
        .asset-name {{
            font-weight: 600;
            color: #333;
        }}
        .asset-symbol {{
            color: #6c757d;
            font-size: 14px;
        }}
        .asset-price {{
            text-align: right;
        }}
        .price-value {{
            font-family: 'Courier New', monospace;
            font-size: 18px;
            font-weight: 600;
            color: #333;
        }}
        .price-change {{
            font-size: 14px;
            font-weight: 600;
            margin-top: 4px;
        }}
        .gain .price-change {{
            color: #28a745;
        }}
        .loss .price-change {{
            color: #dc3545;
        }}
        .neutral .price-change {{
            color: #6c757d;
        }}
        .stats-box {{
            background: #e7f3ff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 15px;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: 600;
            color: #667eea;
        }}
        .stat-label {{
            font-size: 14px;
            color: #6c757d;
            margin-top: 5px;
        }}
        .alert-box {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }}
        .alert-box.high {{
            background: #f8d7da;
            border-left-color: #dc3545;
        }}
        .alert-box.low {{
            background: #d1ecf1;
            border-left-color: #17a2b8;
        }}
        .news-item {{
            padding: 15px;
            border-bottom: 1px solid #dee2e6;
        }}
        .news-item:last-child {{
            border-bottom: none;
        }}
        .news-title {{
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }}
        .news-meta {{
            font-size: 14px;
            color: #6c757d;
        }}
        .footer {{
            background: #343a40;
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .footer p {{
            margin: 5px 0;
            opacity: 0.9;
        }}
        .emoji {{
            font-size: 1.2em;
            margin-right: 5px;
        }}
        @media (max-width: 600px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            .asset-row {{
                flex-direction: column;
                text-align: center;
            }}
            .asset-price {{
                margin-top: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{subject}</h1>
            <p>📅 {paris_time.strftime('%A, %B %d, %Y')} | 🕐 {paris_time.strftime('%H:%M %Z')}</p>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            <p><strong>🤖 Enhanced Financial Monitor v2.0</strong></p>
            <p>📊 Monitoring {len(self.config.get('stocks', {}))} French Stocks + {len(self.config.get('crypto', {}))} Cryptocurrencies</p>
            <p>💱 All prices in EUR | 📈 Real-time data from Yahoo Finance & CoinGecko</p>
        </div>
    </div>
</body>
</html>
"""
        return html_content
    
    def send_email_notification(self, subject: str, message: str, use_html: bool = True):
        """Send enhanced email notification with HTML formatting"""
        try:
            email_config = self.config.get('email', {})
            if not email_config.get('enabled', False):
                logger.info(f"Email disabled. Would send: {subject}")
                return
            
            msg = MIMEMultipart('alternative')
            msg['From'] = email_config['from_email']
            msg['To'] = email_config['to_email']
            msg['Subject'] = subject
            
            # Always attach plain text version
            text_part = MIMEText(message, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Add HTML version if enabled
            if use_html:
                html_content = self.create_html_email(subject, message)
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['from_email'], email_config['password'])
            text = msg.as_string()
            server.sendmail(email_config['from_email'], email_config['to_email'], text)
            server.quit()
            
            logger.info(f"Enhanced email sent: {subject}")
        except Exception as e:
            logger.error(f"Error sending email: {e}")
    
    def send_slack_notification(self, message: str):
        """Send notification to Slack with enhanced formatting"""
        try:
            slack_config = self.config.get('slack', {})
            if not slack_config.get('enabled', False):
                logger.info(f"Slack disabled. Would send: {message[:100]}...")
                return
            
            webhook_url = slack_config.get('webhook_url')
            if not webhook_url:
                logger.error("Slack webhook URL not configured")
                return
            
            # Parse message to extract alerts
            alerts_count = message.count("THRESHOLD REACHED") + message.count("SIGNIFICANT MOVEMENT")
            
            # Create enhanced Slack payload
            payload = {
                "text": f"🚨 Portfolio Alert - {alerts_count} notifications",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🚨 Enhanced Portfolio Alert"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CET | 📊 {len(self.config.get('stocks', {}))} Stocks + {len(self.config.get('crypto', {}))} Crypto"
                            }
                        ]
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```{message}```"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "🤖 Enhanced Financial Monitor | 🔄 Next check in 20min | 📧 Reports at 10:00 & 18:00 CET"
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("Enhanced Slack notification sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
    
    def send_notification(self, subject: str, message: str, notification_type: str = "alert"):
        """Send notification via configured method"""
        if notification_type == "daily_report":
            # Daily reports go to email with HTML formatting
            self.send_email_notification(subject, message, use_html=True)
        else:
            # Alerts go to Slack
            self.send_slack_notification(message)
    
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
            data = self.get_stock_price(symbol)
            if data:
                summary['stock_data'][symbol] = data
        
        # Get current prices for all crypto (in one efficient API call)
        all_crypto_data = self.get_all_crypto_prices()
        summary['crypto_data'] = all_crypto_data
        
        # Get daily changes from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get prices from 24 hours ago
        yesterday = datetime.now() - timedelta(days=1)
        
        # Check all tracked symbols
        all_symbols = list(stock_symbols.keys()) + list(all_crypto_data.keys())
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
                    asset_name = stock_symbols.get(symbol, {}).get('name', 
                                  self.config.get('crypto', {}).get(symbol, {}).get('name', symbol))
                    summary['daily_changes'][symbol] = {
                        'name': asset_name,
                        'old_price': old_price,
                        'current_price': current_price,
                        'change_percent': change
                    }
        
        conn.close()
        return summary
    
    def create_enhanced_daily_report(self, summary: Dict, report_type: str = "morning") -> tuple:
        """Create enhanced daily report with professional formatting"""
        paris_time = datetime.now(self.paris_tz)
        
        # Header
        if report_type == "morning":
            header_emoji = "🌅"
            greeting = "Good morning! Here's your enhanced financial market update:"
        else:
            header_emoji = "🌆"
            greeting = "Good evening! Here's your enhanced end-of-day financial summary:"
        
        # Start building HTML content
        html_sections = []
        
        # Market Status Section
        market_status_html = '<div class="section"><h2>📊 Market Status</h2>'
        for status in summary['market_status']:
            if "OPEN" in status:
                market_status_html += f'<p style="color: #28a745; font-weight: bold;">✅ {status}</p>'
            else:
                market_status_html += f'<p style="color: #dc3545; font-weight: bold;">❌ {status}</p>'
        market_status_html += '</div>'
        html_sections.append(market_status_html)
        
        # Portfolio Performance Section
        all_assets = []
        
        # Add stocks
        for symbol, data in summary['stock_data'].items():
            stock_config = self.config['stocks'][symbol]
            all_assets.append({
                'name': stock_config['name'],
                'symbol': symbol,
                'price': data['current_price'],
                'change': data['change_percent'],
                'type': '🏢',
                'category': 'stock'
            })
        
        # Add crypto
        for symbol, data in summary['crypto_data'].items():
            crypto_config = self.config['crypto'][symbol]
            all_assets.append({
                'name': crypto_config['name'],
                'symbol': symbol,
                'price': data['current_price_eur'],
                'change': data['change_percent_24h'] or 0,
                'type': '🪙',
                'category': 'crypto'
            })
        
        # Sort by change percentage
        all_assets.sort(key=lambda x: x['change'], reverse=True)
        
        # Top Performers Section
        top_performers_html = '<div class="section"><h2>📈 Top Performers</h2><div class="asset-grid">'
        for asset in all_assets[:5]:
            change_class = "gain" if asset['change'] > 0 else "loss" if asset['change'] < 0 else "neutral"
            top_performers_html += f'''
                <div class="asset-row {change_class}">
                    <div class="asset-info">
                        <div class="asset-name">{asset['type']} {asset['name']}</div>
                        <div class="asset-symbol">{asset['symbol']}</div>
                    </div>
                    <div class="asset-price">
                        <div class="price-value">€{asset['price']:.4f}</div>
                        <div class="price-change">{asset['change']:+.2f}%</div>
                    </div>
                </div>
            '''
        top_performers_html += '</div></div>'
        html_sections.append(top_performers_html)
        
        # Worst Performers Section
        worst_performers_html = '<div class="section"><h2>📉 Worst Performers</h2><div class="asset-grid">'
        for asset in all_assets[-5:]:
            change_class = "gain" if asset['change'] > 0 else "loss" if asset['change'] < 0 else "neutral"
            worst_performers_html += f'''
                <div class="asset-row {change_class}">
                    <div class="asset-info">
                        <div class="asset-name">{asset['type']} {asset['name']}</div>
                        <div class="asset-symbol">{asset['symbol']}</div>
                    </div>
                    <div class="asset-price">
                        <div class="price-value">€{asset['price']:.4f}</div>
                        <div class="price-change">{asset['change']:+.2f}%</div>
                    </div>
                </div>
            '''
        worst_performers_html += '</div></div>'
        html_sections.append(worst_performers_html)
        
        # Portfolio Statistics
        if all_assets:
            total_assets = len(all_assets)
            gainers = len([a for a in all_assets if a['change'] > 0])
            losers = len([a for a in all_assets if a['change'] < 0])
            unchanged = total_assets - gainers - losers
            
            stats_html = f'''
                <div class="stats-box">
                    <h2>📊 Portfolio Statistics</h2>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-value">{gainers}</div>
                            <div class="stat-label">📈 Gainers ({gainers/total_assets*100:.1f}%)</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{losers}</div>
                            <div class="stat-label">📉 Losers ({losers/total_assets*100:.1f}%)</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{unchanged}</div>
                            <div class="stat-label">➡️ Unchanged ({unchanged/total_assets*100:.1f}%)</div>
                        </div>
                    </div>
                </div>
            '''
            html_sections.append(stats_html)
        
        # Combine all sections
        content_html = '\n'.join(html_sections)
        
        # Also create plain text version
        plain_text = f"{greeting}\n\n"
        plain_text += "=" * 60 + "\n"
        plain_text += f"📅 ENHANCED DAILY FINANCIAL REPORT - {paris_time.strftime('%A, %B %d, %Y')}\n"
        plain_text += f"🕐 Generated at: {paris_time.strftime('%H:%M %Z')}\n"
        plain_text += f"📊 Coverage: {len(self.config.get('stocks', {}))} stocks + {len(self.config.get('crypto', {}))} cryptocurrencies\n"
        plain_text += "=" * 60 + "\n\n"
        
        # Add market status
        plain_text += "📊 MARKET STATUS:\n"
        for status in summary['market_status']:
            plain_text += f"  {status}\n"
        plain_text += "\n"
        
        # Add top performers
        plain_text += "📈 TOP PERFORMERS:\n"
        for asset in all_assets[:5]:
            plain_text += f"  {asset['type']} {asset['name']}: €{asset['price']:.4f} ({asset['change']:+.2f}%)\n"
        plain_text += "\n"
        
        # Add worst performers
        plain_text += "📉 WORST PERFORMERS:\n"
        for asset in all_assets[-5:]:
            plain_text += f"  {asset['type']} {asset['name']}: €{asset['price']:.4f} ({asset['change']:+.2f}%)\n"
        plain_text += "\n"
        
        # Add statistics
        if all_assets:
            plain_text += "📊 PORTFOLIO STATISTICS:\n"
            plain_text += f"  📈 Gainers: {gainers} ({gainers/total_assets*100:.1f}%)\n"
            plain_text += f"  📉 Losers: {losers} ({losers/total_assets*100:.1f}%)\n"
            plain_text += f"  ➡️ Unchanged: {unchanged} ({unchanged/total_assets*100:.1f}%)\n"
            plain_text += f"  📊 Total Assets: {total_assets}\n\n"
        
        # Footer
        plain_text += "=" * 60 + "\n"
        plain_text += "🤖 Enhanced Financial Monitor v2.0\n"
        plain_text += "=" * 60
        
        return content_html, plain_text
    
    def send_daily_report(self, report_type: str = "morning"):
        """Send enhanced daily email report"""
        logger.info(f"Generating enhanced {report_type} daily report...")
        
        summary = self.get_daily_summary()
        paris_time = datetime.now(self.paris_tz)
        
        if report_type == "morning":
            subject = f"🌅 Morning Financial Report - {paris_time.strftime('%Y-%m-%d')}"
        else:  # evening
            subject = f"🌆 Evening Financial Report - {paris_time.strftime('%Y-%m-%d')}"
        
        # Create enhanced report
        html_content, plain_text = self.create_enhanced_daily_report(summary, report_type)
        
        # For HTML emails, we pass the HTML content which will be properly formatted
        # The create_html_email method will wrap it in the full HTML template
        self.send_notification(subject, html_content, notification_type="daily_report")
        
        # Record that we sent this report
        self.record_report_sent(report_type)
        
        logger.info(f"Enhanced {report_type} daily report sent")
    
    def should_send_daily_report(self) -> Optional[str]:
        """Check if it's time to send a daily report"""
        paris_now = datetime.now(self.paris_tz)
        current_hour = paris_now.hour
        current_minute = paris_now.minute
        today = paris_now.date()
        
        # Morning report window: 9:30 AM - 10:30 AM
        if 9 <= current_hour <= 10:
            if (current_hour == 9 and current_minute >= 30) or (current_hour == 10 and current_minute <= 30):
                if not self.has_sent_report_today('morning', today):
                    return 'morning'
        
        # Evening report window: 5:30 PM - 6:30 PM
        if 17 <= current_hour <= 18:
            if (current_hour == 17 and current_minute >= 30) or (current_hour == 18 and current_minute <= 30):
                if not self.has_sent_report_today('evening', today):
                    return 'evening'
        
        return None"Error fetching {symbol} price: {e}")
            return None

    def get_all_crypto_prices(self) -> Dict[str, Dict]:
        """Get all cryptocurrency prices from CoinGecko API in one call (free tier optimized)"""
        now = datetime.now()
        
        # Cache for 5 minutes to avoid rate limits (CoinGecko free tier: 10-50 calls/minute)
        if (self.last_coingecko_update and 
            (now - self.last_coingecko_update).total_seconds() < 300):
            logger.info("Using cached crypto prices (avoiding rate limits)")
            return self.coingecko_cache
        
        max_retries = 3
        retry_delay = 10  # seconds
        
        # Get all CoinGecko IDs for our cryptocurrencies
        crypto_symbols = self.config.get('crypto', {})
        coingecko_ids = []
        symbol_to_id = {}
        
        for symbol in crypto_symbols.keys():
            if symbol in self.crypto_id_mapping:
                coingecko_id = self.crypto_id_mapping[symbol]
                coingecko_ids.append(coingecko_id)
                symbol_to_id[coingecko_id] = symbol
            else:
                logger.warning(f"No CoinGecko ID mapping found for {symbol}")
        
        logger.info(f"Fetching prices for {len(coingecko_ids)} cryptocurrencies from CoinGecko...")
        
        for attempt in range(max_retries):
            try:
                # CoinGecko simple/price endpoint - can get up to 250 coins per call
                url = "https://api.coingecko.com/api/v3/simple/price"
                
                # Split into chunks of 100 to be safe with free tier
                chunk_size = 100
                all_data = {}
                
                for i in range(0, len(coingecko_ids), chunk_size):
                    chunk_ids = coingecko_ids[i:i + chunk_size]
                    
                    params = {
                        'ids': ','.join(chunk_ids),
                        'vs_currencies': 'usd,eur',
                        'include_24hr_change': 'true',
                        'include_24hr_vol': 'true',
                        'include_market_cap': 'true'
                    }
                    
                    logger.info(f"Fetching chunk {i//chunk_size + 1}/{(len(coingecko_ids)-1)//chunk_size + 1} ({len(chunk_ids)} coins)")
                    
                    response = requests.get(url, params=params, timeout=15)
                    
                    if response.status_code == 429:  # Rate limited
                        wait_time = retry_delay * (attempt + 1)
                        logger.warning(f"Rate limited by CoinGecko, waiting {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            time.sleep(wait_time)
                            break  # Break inner loop, continue outer retry loop
                        else:
                            logger.error("Max retries reached for CoinGecko API")
                            return self.coingecko_cache if self.coingecko_cache else {}
                    
                    response.raise_for_status()
                    chunk_data = response.json()
                    all_data.update(chunk_data)
                    
                    # Small delay between chunks to be respectful to free tier
                    if i + chunk_size < len(coingecko_ids):
                        time.sleep(2)
                
                # Convert to our format
                crypto_data = {}
                for coingecko_id, data in all_data.items():
                    if coingecko_id in symbol_to_id:
                        symbol = symbol_to_id[coingecko_id]
                        
                        # Get EUR price directly or convert from USD
                        price_eur = data.get('eur')
                        if price_eur is None and data.get('usd'):
                            price_eur = self.usd_to_eur(data.get('usd'))
                        
                        # Convert volume to EUR if needed
                        volume_usd = data.get('usd_24h_vol')
                        volume_eur = self.usd_to_eur(volume_usd) if volume_usd else None
                        
                        # Convert market cap to EUR
                        market_cap_usd = data.get('usd_market_cap')
                        market_cap_eur = self.usd_to_eur(market_cap_usd) if market_cap_usd else None
                        
                        crypto_data[symbol] = {
                            'symbol': symbol,
                            'coingecko_id': coingecko_id,
                            'current_price_eur': price_eur,
                            'current_price_usd': data.get('usd'),
                            'change_percent_24h': data.get('usd_24h_change'),
                            'volume_24h_eur': volume_eur,
                            'volume_24h_usd': volume_usd,
                            'market_cap_eur': market_cap_eur,
                            'market_cap_usd': market_cap_usd,
                            'timestamp': datetime.now().isoformat(),
                            'market_open': True,  # Crypto markets are always open
                            'exchange_rate_used': self.get_usd_to_eur_rate()
                        }
                
                # Update cache
                self.coingecko_cache = crypto_data
                self.last_coingecko_update = now
                
                logger.info(f"Successfully fetched {len(crypto_data)} cryptocurrency prices")
                return crypto_data
                
            except Exception as e:
                logger.error(f"Error fetching crypto prices (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    # Return cached data if available
                    if self.coingecko_cache:
                        logger.warning("Using cached crypto data due to API failure")
                        return self.coingecko_cache
                    return {}
        
        return {}
    
    def format_price_change_display(self, asset_name: str, symbol: str, current_price: float, 
                                   previous_price: float, change_percent: float, asset_type: str = "stock") -> str:
        """Format price change with clear before/after display and visual indicators"""
        
        # Determine direction and color indicators
        if change_percent > 0:
            direction_emoji = "📈"
            change_indicator = "GAIN"
            trend_symbol = "▲"
        elif change_percent < 0:
            direction_emoji = "📉"
            change_indicator = "LOSS" 
            trend_symbol = "▼"
        else:
            direction_emoji = "➡️"
            change_indicator = "FLAT"
            trend_symbol = "━"
        
        # Asset type emoji
        type_emoji = "🏢" if asset_type == "stock" else "🪙"
        
        # Price formatting based on value
        if current_price >= 1:
            price_format = ".2f"
        elif current_price >= 0.01:
            price_format = ".4f"
        else:
            price_format = ".6f"
        
        # Create clear before/after display
        formatted_display = (
            f"{direction_emoji} {type_emoji} {asset_name} ({symbol})\n"
            f"   💰 BEFORE: €{previous_price:{price_format}} → AFTER: €{current_price:{price_format}}\n"
            f"   {trend_symbol} {change_indicator}: {change_percent:+.2f}%"
        )
        
        return formatted_display
    
    def check_price_alerts(self, symbol: str, current_price: float, thresholds: Dict) -> List[str]:
        """Check if price alerts should be triggered with enhanced formatting"""
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
        
        # Get asset info for better display
        asset_name = symbol
        asset_type = "crypto"
        if symbol in self.config.get('stocks', {}):
            asset_name = self.config['stocks'][symbol]['name']
            asset_type = "stock"
        elif symbol in self.config.get('crypto', {}):
            asset_name = self.config['crypto'][symbol]['name']
            asset_type = "crypto"
        
        # Check thresholds with enhanced formatting
        if current_price >= thresholds.get('high', float('inf')):
            alert = self.format_price_change_display(
                asset_name, symbol, current_price, prev_price, change_percent, asset_type
            )
            alerts.append(f"🔴 HIGH THRESHOLD REACHED\n{alert}")
        
        if current_price <= thresholds.get('low', 0):
            alert = self.format_price_change_display(
                asset_name, symbol, current_price, prev_price, change_percent, asset_type
            )
            alerts.append(f"🔵 LOW THRESHOLD REACHED\n{alert}")
        
        if abs(change_percent) >= thresholds.get('change_percent', 10):
            alert = self.format_price_change_display(
                asset_name, symbol, current_price, prev_price, change_percent, asset_type
            )
            alerts.append(f"⚡ SIGNIFICANT MOVEMENT\n{alert}")
        
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
            logger.error(f
