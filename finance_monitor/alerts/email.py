# alerts/email.py
"""
Module d'envoi d'emails avec support HTML et texte brut.
Configuration via variables d'environnement pour la sécurité.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import CONFIG
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def send_email(subject: str, plain_text: str, html_content: str = None):
    """
    Envoie un email de notification en utilisant SMTP.
    
    Args:
        subject: Sujet de l'email
        plain_text: Contenu texte brut
        html_content: Contenu HTML optionnel
    """
    cfg = CONFIG.get("email", {})
    if not cfg.get("enabled"):
        logger.info("Email désactivé dans la configuration. Envoi annulé.")
        return

    try:
        # Création du message
        msg = MIMEMultipart("alternative")
        msg["From"] = cfg["from_email"]
        msg["To"] = cfg["to_email"]
        msg["Subject"] = subject
        msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

        # Toujours attacher le texte brut
        part1 = MIMEText(plain_text, "plain", "utf-8")
        msg.attach(part1)

        # Optionnellement attacher le HTML
        if html_content:
            part2 = MIMEText(html_content, "html", "utf-8")
            msg.attach(part2)

        # Connexion SMTP et envoi
        server = smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"])
        server.starttls()  # Activer TLS
        server.login(cfg["from_email"], cfg["password"])
        
        text = msg.as_string()
        server.sendmail(cfg["from_email"], cfg["to_email"], text)
        server.quit()

        logger.info(f"✅ Email envoyé avec succès: {subject}")

    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi de l'email: {e}")
        raise

def create_html_email_template(title: str, content: str) -> str:
    """
    Crée un template HTML professionnel pour les emails.
    
    Args:
        title: Titre de l'email
        content: Contenu HTML à insérer
        
    Returns:
        HTML complet formaté
    """
    html_template = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
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
        .price-change {{
            font-family: 'Courier New', monospace;
            font-weight: bold;
            font-size: 16px;
        }}
        .gain {{
            color: #28a745;
        }}
        .loss {{
            color: #dc3545;
        }}
        .neutral {{
            color: #6c757d;
        }}
        .footer {{
            background: #343a40;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 14px;
        }}
        .footer p {{
            margin: 5px 0;
            opacity: 0.9;
        }}
        @media (max-width: 600px) {{
            .container {{
                margin: 10px;
                border-radius: 5px;
            }}
            .header, .content, .footer {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>📅 {datetime.now().strftime('%d/%m/%Y %H:%M')} (Paris)</p>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            <p><strong>🤖 Finance Monitor Bot</strong></p>
            <p>Monitoring automatique des actifs financiers</p>
        </div>
    </div>
</body>
</html>
"""
    return html_template

def send_alert_email(alerts: list, market_status: list = None, additional_info: str = None):
    """
    Envoie un email d'alerte formaté avec les alertes de prix.
    
    Args:
        alerts: Liste des alertes générées
        market_status: Statut des marchés
        additional_info: Informations additionnelles
    """
    if not alerts:
        logger.info("Aucune alerte à envoyer")
        return

    subject = f"🚨 Alerte Portfolio - {len(alerts)} notification(s)"
    
    # Contenu texte brut
    plain_content = []
    plain_content.append("🚨 ALERTE MONITORING FINANCIER")
    plain_content.append("=" * 50)
    plain_content.append("")
    
    if market_status:
        plain_content.append("📊 STATUT DES MARCHÉS:")
        for status in market_status:
            plain_content.append(f"  {status}")
        plain_content.append("")
    
    plain_content.append(f"🚨 ALERTES DE PRIX ({len(alerts)}):")
    plain_content.append("-" * 30)
    
    for i, alert in enumerate(alerts, 1):
        plain_content.append(f"\nALERTE #{i}:")
        plain_content.append(alert)
    
    if additional_info:
        plain_content.append("\n" + additional_info)
    
    plain_content.append("\n" + "=" * 50)
    plain_content.append("🤖 Finance Monitor Bot")
    
    plain_text = "\n".join(plain_content)
    
    # Contenu HTML
    html_alerts = []
    for i, alert in enumerate(alerts, 1):
        alert_class = "high" if "HIGH THRESHOLD" in alert else "low" if "LOW THRESHOLD" else ""
        html_alerts.append(f"""
        <div class="alert-box {alert_class}">
            <h3>Alerte #{i}</h3>
            <pre>{alert}</pre>
        </div>
        """)
    
    html_content_body = ""
    
    if market_status:
        html_content_body += "<h2>📊 Statut des Marchés</h2>"
        for status in market_status:
            html_content_body += f"<p>{status}</p>"
    
    html_content_body += f"<h2>🚨 Alertes de Prix ({len(alerts)})</h2>"
    html_content_body += "".join(html_alerts)
    
    if additional_info:
        html_content_body += f"<div style='margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 5px;'>{additional_info}</div>"
    
    html_content = create_html_email_template("Alerte Portfolio", html_content_body)
    
    # Envoyer l'email
    send_email(subject, plain_text, html_content)

def send_daily_report_email(title: str, summary_data: dict):
    """
    Envoie le rapport quotidien par email.
    
    Args:
        title: Titre du rapport
        summary_data: Données du résumé quotidien
    """
    subject = f"📊 {title}"
    
    # Construire le contenu texte
    plain_content = []
    plain_content.append(f"📊 {title}")
    plain_content.append("=" * 60)
    plain_content.append(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')} (Paris)")
    plain_content.append("")
    
    if 'market_status' in summary_data:
        plain_content.append("📊 STATUT DES MARCHÉS:")
        for status in summary_data['market_status']:
            plain_content.append(f"  {status}")
        plain_content.append("")
    
    if 'top_performers' in summary_data:
        plain_content.append("📈 MEILLEURES PERFORMANCES:")
        for performer in summary_data['top_performers']:
            plain_content.append(f"  • {performer}")
        plain_content.append("")
    
    if 'worst_performers' in summary_data:
        plain_content.append("📉 PLUS MAUVAISES PERFORMANCES:")
        for performer in summary_data['worst_performers']:
            plain_content.append(f"  • {performer}")
        plain_content.append("")
    
    if 'statistics' in summary_data:
        stats = summary_data['statistics']
        plain_content.append("📊 STATISTIQUES:")
        plain_content.append(f"  • Total actifs: {stats.get('total_assets', 0)}")
        plain_content.append(f"  • En hausse: {stats.get('gainers', 0)} ({stats.get('gainers_pct', 0):.1f}%)")
        plain_content.append(f"  • En baisse: {stats.get('losers', 0)} ({stats.get('losers_pct', 0):.1f}%)")
        plain_content.append(f"  • Inchangés: {stats.get('unchanged', 0)} ({stats.get('unchanged_pct', 0):.1f}%)")
    
    plain_content.append("\n" + "=" * 60)
    plain_content.append("🤖 Finance Monitor Bot - Rapport Quotidien")
    
    plain_text = "\n".join(plain_content)
    
    # Construire le contenu HTML
    html_body = f"<h1>{title}</h1>"
    
    if 'market_status' in summary_data:
        html_body += "<h2>📊 Statut des Marchés</h2>"
        for status in summary_data['market_status']:
            color = "green" if "OUVERT" in status else "red"
            html_body += f"<p style='color: {color}; font-weight: bold;'>{status}</p>"
    
    if 'top_performers' in summary_data:
        html_body += "<h2>📈 Meilleures Performances</h2><ul>"
        for performer in summary_data['top_performers']:
            html_body += f"<li class='gain'>{performer}</li>"
        html_body += "</ul>"
    
    if 'worst_performers' in summary_data:
        html_body += "<h2>📉 Plus Mauvaises Performances</h2><ul>"
        for performer in summary_data['worst_performers']:
            html_body += f"<li class='loss'>{performer}</li>"
        html_body += "</ul>"
    
    if 'statistics' in summary_data:
        stats = summary_data['statistics']
        html_body += f"""
        <h2>📊 Statistiques du Portfolio</h2>
        <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0;'>
            <div style='text-align: center; padding: 15px; background: #e8f5e9; border-radius: 8px;'>
                <div style='font-size: 24px; font-weight: bold; color: #2e7d32;'>{stats.get('gainers', 0)}</div>
                <div>En hausse ({stats.get('gainers_pct', 0):.1f}%)</div>
            </div>
            <div style='text-align: center; padding: 15px; background: #ffebee; border-radius: 8px;'>
                <div style='font-size: 24px; font-weight: bold; color: #c62828;'>{stats.get('losers', 0)}</div>
                <div>En baisse ({stats.get('losers_pct', 0):.1f}%)</div>
            </div>
        </div>
        """
    
    html_content = create_html_email_template(title, html_body)
    
    # Envoyer l'email
    send_email(subject, plain_text, html_content)

def test_email_configuration():
    """
    Teste la configuration email en envoyant un email de test.
    
    Returns:
        bool: True si le test réussit, False sinon
    """
    try:
        subject = "🧪 Test Configuration Finance Monitor"
        message = """Ceci est un email de test du Finance Monitor Bot.

Si vous recevez ce message, votre configuration email fonctionne correctement !

✅ Serveur SMTP: Connecté
✅ Authentification: Réussie  
✅ Livraison email: Fonctionnelle

Votre bot de monitoring est prêt à envoyer des alertes et des rapports quotidiens.

---
🤖 Finance Monitor Bot
"""
        
        send_email(subject, message)
        logger.info("📧 Email de test envoyé avec succès!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Échec du test email: {e}")
        return False
