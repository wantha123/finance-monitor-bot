#!/usr/bin/env python3
"""
Point d'entrée principal du bot de monitoring financier.
Gère l'initialisation, la planification et l'exécution.
"""

import os
import sys
import logging
import schedule
import time
from datetime import datetime
import argparse

# Configuration du logging
def setup_logging(log_level: str = "INFO"):
    """Configure le système de logging."""
    # Créer le dossier logs si nécessaire
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Nom du fichier log avec date
    log_file = os.path.join(log_dir, f"finance_monitor_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Configuration
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Logger principal
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("🚀 DÉMARRAGE DU FINANCE MONITOR BOT")
    logger.info("=" * 60)
    
    return logger


def check_environment():
    """Vérifie que l'environnement est correctement configuré."""
    logger = logging.getLogger(__name__)
    
    required_vars = [
        'NEWS_API_KEY',
        'EMAIL_USER',
        'EMAIL_PASS',
        'EMAIL_TARGET'
    ]
    
    optional_vars = [
        'SLACK_WEBHOOK',
        'RUN_MODE',
        'LOG_LEVEL'
    ]
    
    missing = []
    
    # Vérifier les variables requises
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        logger.error(f"❌ Variables d'environnement manquantes: {', '.join(missing)}")
        logger.error("Veuillez configurer ces variables avant de lancer le bot.")
        return False
    
    # Afficher les variables optionnelles
    logger.info("📋 Configuration de l'environnement:")
    for var in required_vars + optional_vars:
        value = os.environ.get(var)
        if value:
            # Masquer les valeurs sensibles
            if 'PASS' in var or 'KEY' in var or 'WEBHOOK' in var:
                display_value = value[:4] + "****" + value[-4:] if len(value) > 8 else "****"
            else:
                display_value = value
            logger.info(f"  • {var}: {display_value}")
        else:
            logger.info(f"  • {var}: Non défini")
    
    return True


def initialize_database():
    """Initialise la base de données."""
    logger = logging.getLogger(__name__)
    
    try:
        from data.database import init_database
        init_database()
        logger.info("✅ Base de données initialisée")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur initialisation base de données: {e}")
        return False


def load_configuration():
    """Charge et valide la configuration."""
    logger = logging.getLogger(__name__)
    
    try:
        from config import CONFIG
        
        # Compter les actifs
        stocks_count = len(CONFIG.get('stocks', {}))
        crypto_count = len(CONFIG.get('crypto', {}))
        
        logger.info(f"📊 Configuration chargée:")
        logger.info(f"  • {stocks_count} actions")
        logger.info(f"  • {crypto_count} cryptomonnaies")
        logger.info(f"  • Email: {'Activé' if CONFIG.get('email', {}).get('enabled') else 'Désactivé'}")
        logger.info(f"  • Slack: {'Activé' if CONFIG.get('slack', {}).get('enabled') else 'Désactivé'}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erreur chargement configuration: {e}")
        return False


def test_connections():
    """Teste les connexions aux services externes."""
    logger = logging.getLogger(__name__)
    logger.info("🔌 Test des connexions...")
    
    # Test email
    try:
        from alerts.email import send_email
        send_email(
            "🧪 Test Finance Monitor",
            "Ceci est un email de test.\nSi vous recevez ce message, la configuration email fonctionne !",
            None
        )
        logger.info("✅ Email de test envoyé")
    except Exception as e:
        logger.warning(f"⚠️  Test email échoué: {e}")
    
    # Test API News
    try:
        from data.fetchers import NewsFetcher
        from config import CONFIG
        
        fetcher = NewsFetcher(CONFIG.get('news_api_key'))
        news = fetcher.get_news("bitcoin", language="fr")
        
        if news:
            logger.info(f"✅ API News fonctionnelle ({len(news)} articles trouvés)")
        else:
            logger.warning("⚠️  API News: Aucun article trouvé")
    except Exception as e:
        logger.warning(f"⚠️  Test API News échoué: {e}")
    
    # Test Yahoo Finance
    try:
        from data.fetchers import StockFetcher
        
        fetcher = StockFetcher()
        data = fetcher.get_stock_price("AAPL")
        
        if data:
            logger.info(f"✅ Yahoo Finance fonctionnel (AAPL: ${data['current_price']:.2f})")
        else:
            logger.warning("⚠️  Yahoo Finance: Pas de données")
    except Exception as e:
        logger.warning(f"⚠️  Test Yahoo Finance échoué: {e}")
    
    # Test CoinGecko
    try:
        from data.fetchers import CryptoFetcher
        
        fetcher = CryptoFetcher()
        data = fetcher.get_all_crypto_prices(['BTC'])
        
        if data and 'BTC' in data:
            price = data['BTC'].get('current_price_eur', 0)
            logger.info(f"✅ CoinGecko fonctionnel (BTC: €{price:,.2f})")
        else:
            logger.warning("⚠️  CoinGecko: Pas de données")
    except Exception as e:
        logger.warning(f"⚠️  Test CoinGecko échoué: {e}")


def schedule_tasks():
    """Configure la planification des tâches."""
    logger = logging.getLogger(__name__)
    
    from core.monitor import run_monitoring_cycle
    from core.utils import is_euronext_open
    
    # Mode d'exécution
    run_mode = os.environ.get('RUN_MODE', 'continuous').lower()
    
    if run_mode == 'once':
        # Exécution unique
        logger.info("🔄 Mode: Exécution unique")
        run_monitoring_cycle()
        return False
    
    else:
        # Mode continu avec planification intelligente
        logger.info("🔄 Mode: Exécution continue")
        
        # Planification adaptative
        def smart_schedule():
            """Adapte la fréquence selon les heures de marché."""
            # Nettoyer les jobs existants
            schedule.clear()
            
            if is_euronext_open():
                # Marché ouvert: monitoring fréquent
                schedule.every(20).minutes.do(run_monitoring_cycle)
                logger.info("📊 Marché ouvert: Monitoring toutes les 20 minutes")
            else:
                # Marché fermé: monitoring réduit
                schedule.every(60).minutes.do(run_monitoring_cycle)
                logger.info("🌙 Marché fermé: Monitoring toutes les 60 minutes")
            
            # Toujours replanifier l'adaptation
            schedule.every(4).hours.do(smart_schedule)
        
        # Planification initiale
        smart_schedule()
        
        # Exécution immédiate au démarrage
        run_monitoring_cycle()
        
        return True


def run_analysis_mode():
    """Mode analyse technique des actifs."""
    logger = logging.getLogger(__name__)
    logger.info("📈 Mode: Analyse technique")
    
    from config import CONFIG
    from analysis.strategy import TradingStrategy
    
    strategy = TradingStrategy()
    analyses = []
    
    # Analyser tous les actifs
    all_symbols = []
    
    # Stocks
    for symbol in CONFIG.get('stocks', {}):
        all_symbols.append((symbol, 'stock'))
    
    # Cryptos
    for symbol in CONFIG.get('crypto', {}):
        all_symbols.append((symbol, 'crypto'))
    
    logger.info(f"Analyse de {len(all_symbols)} actifs...")
    
    for symbol, asset_type in all_symbols:
        try:
            analysis = strategy.analyze_asset(symbol, asset_type)
            analyses.append(analysis)
            
            # Log résumé
            overall = analysis.get('overall_score', {})
            if overall:
                logger.info(f"  • {symbol}: Score {overall['score']:.1f} - {overall.get('signal', 'N/A')}")
        
        except Exception as e:
            logger.error(f"  ❌ Erreur analyse {symbol}: {e}")
    
    # Générer le rapport
    if analyses:
        report = strategy.generate_strategy_report(analyses)
        
        # Sauvegarder le rapport
        report_file = f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📄 Rapport d'analyse sauvegardé: {report_file}")
        
        # Optionnel: envoyer par email
        try:
            from alerts.email import send_email
            send_email(
                f"📊 Analyse Technique - {datetime.now().strftime('%d/%m/%Y')}",
                report,
                None
            )
            logger.info("📧 Rapport envoyé par email")
        except Exception as e:
            logger.warning(f"Impossible d'envoyer le rapport: {e}")


def main():
    """Fonction principale."""
    # Parser les arguments
    parser = argparse.ArgumentParser(description='Bot de monitoring financier')
    parser.add_argument('--mode', choices=['monitor', 'analyze', 'test'], 
                       default='monitor', help='Mode d\'exécution')
    parser.add_argument('--once', action='store_true', 
                       help='Exécuter une seule fois puis quitter')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default=os.environ.get('LOG_LEVEL', 'INFO'),
                       help='Niveau de logging')
    
    args = parser.parse_args()
    
    # Configuration du logging
    logger = setup_logging(args.log_level)
    
    # Vérification de l'environnement
    if not check_environment():
        sys.exit(1)
    
    # Initialisation de la base de données
    if not initialize_database():
        sys.exit(1)
    
    # Chargement de la configuration
    if not load_configuration():
        sys.exit(1)
    
    # Mode test
    if args.mode == 'test':
        logger.info("🧪 Mode test des connexions")
        test_connections()
        sys.exit(0)
    
    # Mode analyse
    if args.mode == 'analyze':
        run_analysis_mode()
        sys.exit(0)
    
    # Mode monitoring (par défaut)
    logger.info("💼 Démarrage du monitoring financier")
    
    # Override du mode d'exécution si --once est spécifié
    if args.once:
        os.environ['RUN_MODE'] = 'once'
    
    # Test des connexions au premier lancement
    test_connections()
    
    # Planification des tâches
    should_continue = schedule_tasks()
    
    if should_continue:
        # Boucle principale
        logger.info("⏰ Planification active. Appuyez sur Ctrl+C pour arrêter.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Vérifier chaque minute
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Arrêt demandé par l'utilisateur")
        except Exception as e:
            logger.error(f"❌ Erreur critique: {e}", exc_info=True)
        finally:
            logger.info("👋 Finance Monitor Bot terminé")
    else:
        logger.info("✅ Exécution unique terminée")


if __name__ == "__main__":
    main()
