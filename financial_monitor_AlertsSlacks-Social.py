# alerts/slack.py
"""
Module d'envoi de notifications Slack avec support Block Kit.
Utilise les webhooks pour des notifications enrichies et interactives.
"""

import requests
import logging
from config import CONFIG
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

def send_slack(message: str):
    """
    Envoie un message simple à Slack via webhook.
    
    Args:
        message: Message texte à envoyer
    """
    cfg = CONFIG.get("slack", {})
    if not cfg.get("enabled"):
        logger.info("Slack désactivé dans la configuration. Envoi annulé.")
        return

    webhook_url = cfg.get("webhook_url")
    if not webhook_url:
        logger.error("URL webhook Slack non configurée.")
        return

    payload = {"text": message}
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("✅ Message Slack envoyé avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi du message Slack: {e}")

def send_slack_blocks(blocks: List[Dict], text_fallback: str = None):
    """
    Envoie un message Slack enrichi avec Block Kit.
    
    Args:
        blocks: Liste des blocs Block Kit
        text_fallback: Texte de fallback pour les clients non compatibles
    """
    cfg = CONFIG.get("slack", {})
    if not cfg.get("enabled"):
        logger.info("Slack désactivé dans la configuration. Envoi annulé.")
        return

    webhook_url = cfg.get("webhook_url")
    if not webhook_url:
        logger.error("URL webhook Slack non configurée.")
        return

    payload = {
        "blocks": blocks
    }
    
    if text_fallback:
        payload["text"] = text_fallback
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("✅ Message Slack enrichi envoyé avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi du message Slack enrichi: {e}")

def create_alert_blocks(alerts: List[str], market_status: List[str] = None) -> List[Dict]:
    """
    Crée les blocs Block Kit pour les alertes de prix.
    
    Args:
        alerts: Liste des alertes
        market_status: Statut des marchés
        
    Returns:
        Liste des blocs Block Kit
    """
    blocks = []
    
    # En-tête
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": f"🚨 Alerte Portfolio ({len(alerts)} notifications)",
            "emoji": True
        }
    })
    
    # Contexte avec timestamp
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"*Heure:* {datetime.now().strftime('%H:%M:%S')} CET"
            }
        ]
    })
    
    blocks.append({"type": "divider"})
    
    # Statut des marchés si fourni
    if market_status:
        market_text = ""
        for status in market_status:
            if "OUVERT" in status:
                market_text += f"✅ {status}\n"
            else:
                market_text += f"❌ {status}\n"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📊 Statut des Marchés:*\n{market_text}"
            }
        })
        
        blocks.append({"type": "divider"})
    
    # Alertes groupées par type
    threshold_alerts = [a for a in alerts if "THRESHOLD" in a]
    movement_alerts = [a for a in alerts if "MOVEMENT" in a]
    
    if threshold_alerts:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🎯 Seuils Atteints ({len(threshold_alerts)}):*"
            }
        })
        
        for alert in threshold_alerts[:3]:  # Limiter à 3 pour la lisibilité
            # Extraire les informations clés de l'alerte
            alert_type = "🔴" if "HIGH" in alert else "🔵"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{alert_type} {alert[:100]}..."  # Tronquer pour Slack
                }
            })
    
    if movement_alerts:
        if threshold_alerts:
            blocks.append({"type": "divider"})
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*⚡ Mouvements Significatifs ({len(movement_alerts)}):*"
            }
        })
        
        for alert in movement_alerts[:3]:  # Limiter à 3 pour la lisibilité
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⚡ {alert[:100]}..."  # Tronquer pour Slack
                }
            })
    
    # Pied de page
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "🤖 Finance Monitor Bot | 📧 Détails complets envoyés par email"
            }
        ]
    })
    
    return blocks

def send_portfolio_alert(alerts: List[str], market_status: List[str] = None, 
                        additional_data: Dict = None):
    """
    Envoie une alerte portfolio formatée à Slack.
    
    Args:
        alerts: Liste des alertes
        market_status: Statut des marchés
        additional_data: Données additionnelles (top movers, etc.)
    """
    if not alerts:
        logger.info("Aucune alerte à envoyer sur Slack")
        return
    
    # Créer les blocs enrichis
    blocks = create_alert_blocks(alerts, market_status)
    
    # Ajouter les données additionnelles si disponibles
    if additional_data and 'top_movers' in additional_data:
        blocks.append({"type": "divider"})
        
        movers_text = "*🔥 Top Mouvements:*\n"
        for mover in additional_data['top_movers'][:3]:
            movers_text += f"• {mover}\n"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": movers_text
            }
        })
    
    # Texte de fallback
    fallback_text = f"🚨 Alerte Portfolio - {len(alerts)} notifications"
    
    # Envoyer les blocs enrichis
    send_slack_blocks(blocks, fallback_text)

def send_daily_summary_slack(title: str, summary_stats: Dict):
    """
    Envoie un résumé quotidien compact à Slack.
    
    Args:
        title: Titre du résumé
        summary_stats: Statistiques résumées
    """
    blocks = []
    
    # En-tête
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": f"📊 {title}",
            "emoji": True
        }
    })
    
    # Statistiques
    if 'total_assets' in summary_stats:
        stats_text = f"*Portfolio:* {summary_stats['total_assets']} actifs\n"
        stats_text += f"📈 *Hausse:* {summary_stats.get('gainers', 0)} ({summary_stats.get('gainers_pct', 0):.1f}%)\n"
        stats_text += f"📉 *Baisse:* {summary_stats.get('losers', 0)} ({summary_stats.get('losers_pct', 0):.1f}%)\n"
        stats_text += f"➡️ *Stable:* {summary_stats.get('unchanged', 0)} ({summary_stats.get('unchanged_pct', 0):.1f}%)"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": stats_text
            }
        })
    
    # Top performers si disponibles
    if 'top_performers' in summary_stats:
        blocks.append({"type": "divider"})
        
        performers_text = "*🏆 Top Performers:*\n"
        for performer in summary_stats['top_performers'][:3]:
            performers_text += f"• {performer}\n"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": performers_text
            }
        })
    
    # Pied de page
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"🕐 {datetime.now().strftime('%H:%M')} CET | 📧 Rapport complet par email"
            }
        ]
    })
    
    # Texte de fallback
    fallback_text = f"{title} - Portfolio de {summary_stats.get('total_assets', 0)} actifs"
    
    # Envoyer
    send_slack_blocks(blocks, fallback_text)

def send_market_status_slack(market_status: List[str]):
    """
    Envoie le statut des marchés à Slack.
    
    Args:
        market_status: Liste des statuts de marchés
    """
    blocks = []
    
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "📊 Statut des Marchés",
            "emoji": True
        }
    })
    
    status_text = ""
    for status in market_status:
        if "OUVERT" in status:
            status_text += f"🟢 {status}\n"
        else:
            status_text += f"🔴 {status}\n"
    
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": status_text
        }
    })
    
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"🕐 Mis à jour: {datetime.now().strftime('%H:%M:%S')} CET"
            }
        ]
    })
    
    fallback_text = "Statut des marchés financiers"
    send_slack_blocks(blocks, fallback_text)

def test_slack_configuration():
    """
    Teste la configuration Slack en envoyant un message de test.
    
    Returns:
        bool: True si le test réussit, False sinon
    """
    try:
        test_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🧪 Test Configuration Slack",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Ceci est un message de test du *Finance Monitor Bot*.\n\nSi vous recevez ce message, votre configuration Slack fonctionne correctement ! ✅"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🕐 Test effectué: {datetime.now().strftime('%H:%M:%S')} CET"
                    }
                ]
            }
        ]
        
        send_slack_blocks(test_blocks, "🧪 Test Configuration Slack - Finance Monitor Bot")
        logger.info("📱 Message de test Slack envoyé avec succès!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Échec du test Slack: {e}")
        return False