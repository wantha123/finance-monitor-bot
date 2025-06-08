# 🤖 Finance Monitor Bot

Bot de surveillance automatisé des marchés financiers et cryptomonnaies avec alertes intelligentes, analyse technique et intégration du carnet d'ordres.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [Modules](#-modules)
- [Stratégies d'analyse](#-stratégies-danalyse)
- [Déploiement](#-déploiement)
- [Contribution](#-contribution)

## 🚀 Fonctionnalités

### Surveillance en temps réel
- **37 actions françaises** (Euronext Paris) via Yahoo Finance
- **60+ cryptomonnaies** via CoinGecko API
- Conversion automatique USD → EUR
- Adaptation intelligente aux heures de marché

### Alertes multi-canaux
- 📧 **Email** : Rapports HTML enrichis avec graphiques
- 💬 **Slack** : Notifications instantanées via webhook
- 📊 **Rapports quotidiens** : 10h et 18h (heure de Paris)

### Analyse technique avancée
- **Indicateurs** : RSI, MACD, Bollinger, SMA/EMA, Stochastique
- **Stratégies** : Court/moyen/long terme avec scoring
- **Carnet d'ordres** : Analyse de liquidité (crypto uniquement)
- **News** : Intégration NewsAPI pour contexte marché

### Intelligence artificielle
- Détection automatique des seuils critiques
- Analyse du sentiment (prévu)
- Optimisation de portfolio (prévu)

## 🏗️ Architecture

```
finance_monitor/
├── main.py                 # Point d'entrée principal
├── config.py              # Configuration centralisée
├── requirements.txt       # Dépendances Python
├── README.md             # Documentation
│
├── core/                 # Logique métier
│   ├── monitor.py       # Orchestrateur principal
│   ├── alerting.py      # Gestion des alertes
│   ├── summary.py       # Génération rapports
│   └── utils.py         # Utilitaires
│
├── data/                # Couche données
│   ├── database.py      # SQLite (historique)
│   └── fetchers.py      # APIs (Yahoo, CoinGecko, News)
│
├── alerts/              # Notifications
│   ├── email.py         # SMTP Gmail
│   └── slack.py         # Webhook Slack
│
├── analysis/            # Analyse technique
│   ├── indicators.py    # Calcul indicateurs
│   ├── strategy.py      # Stratégies trading
│   └── orderbook.py     # Analyse carnet d'ordres
│
└── social/              # Future: sentiment
    └── sentiment.py     # Twitter/Reddit (TODO)
```

## 📦 Installation

### Prérequis
- Python 3.8+
- Compte Gmail avec mot de passe d'application
- Clé API NewsAPI (gratuite)
- (Optionnel) Webhook Slack

### Installation locale

```bash
# Cloner le repository
git clone https://github.com/votre-username/finance-monitor.git
cd finance-monitor

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer dépendances
pip install -r requirements.txt
```

## ⚙️ Configuration

### Variables d'environnement

```bash
# Obligatoires
export NEWS_API_KEY="votre_cle_newsapi"
export EMAIL_USER="votre.email@gmail.com"
export EMAIL_PASS="votre_mot_de_passe_application"
export EMAIL_TARGET="destinataire@email.com"

# Optionnelles
export SLACK_WEBHOOK="https://hooks.slack.com/services/..."
export RUN_MODE="continuous"  # ou "once"
export LOG_LEVEL="INFO"       # DEBUG, WARNING, ERROR
```

### Fichier config.py

Le fichier `config.py` contient :
- Liste des actions surveillées (37 entreprises françaises)
- Liste des cryptomonnaies (60+ actifs)
- Seuils d'alerte personnalisés par actif
- Paramètres SMTP et Slack

#### Exemple de configuration d'actif :

```python
"STMPA.PA": {
    "name": "STMicroelectronics",
    "thresholds": {
        "high": 35.0,      # Alerte si prix > 35€
        "low": 15.0,       # Alerte si prix < 15€
        "change_percent": 8.0  # Alerte si variation > 8%
    }
}
```

## 🎮 Utilisation

### Mode monitoring continu

```bash
# Lancement standard (surveillance continue)
python main.py

# Avec niveau de log personnalisé
python main.py --log-level DEBUG
```

### Mode analyse unique

```bash
# Analyse technique de tous les actifs
python main.py --mode analyze

# Test des connexions
python main.py --mode test

# Exécution unique (pour cron/Railway)
python main.py --once
```

### Planification intelligente

Le bot adapte automatiquement sa fréquence :
- **Marché ouvert** : Toutes les 20 minutes
- **Marché fermé** : Toutes les 60 minutes
- **Rapports quotidiens** : 10h et 18h automatiquement

## 📊 Modules

### 1. Monitor (core/monitor.py)
Orchestrateur principal qui :
- Coordonne la récupération des données
- Vérifie les seuils d'alerte
- Envoie les notifications
- Gère les rapports quotidiens

### 2. Indicateurs techniques (analysis/indicators.py)
Calcule en temps réel :
- **RSI** : Surachat/survente (14 périodes)
- **MACD** : Convergence/divergence des moyennes
- **Bollinger** : Volatilité et niveaux extrêmes
- **SMA/EMA** : Tendances court/moyen/long terme
- **ATR** : Volatilité moyenne
- **OBV** : Volume cumulé

### 3. Stratégies (analysis/strategy.py)
Analyse multi-horizons :
- **Intraday** : Scalping basé sur RSI/Stochastique
- **Court terme** : 1-5 jours, MACD + momentum
- **Moyen terme** : 1-4 semaines, tendances + support/résistance
- **Long terme** : 1+ mois, analyse de fond

### 4. Carnet d'ordres (analysis/orderbook.py)
Pour les cryptomonnaies uniquement :
- **Order Book Imbalance** : Déséquilibre acheteurs/vendeurs
- **Détection de murs** : Gros ordres bloquants
- **Score de liquidité** : Profondeur du marché
- **Pondération** : Maximum 20% du signal final

### 5. Alertes (alerts/)
- **Email** : HTML riche avec tableaux et graphiques
- **Slack** : Messages concis avec emojis
- **Personnalisation** : Seuils par actif

## 📈 Stratégies d'analyse

### Signaux d'achat
Le bot génère un signal d'achat quand :
1. RSI < 30 (survente)
2. MACD croise à la hausse
3. Prix proche bande Bollinger inférieure
4. Carnet d'ordres confirme (OBI > 0.3)

### Signaux de vente
Signal de vente généré si :
1. RSI > 70 (surachat)
2. MACD croise à la baisse
3. Prix proche bande Bollinger supérieure
4. Mur de vente détecté < 2% du prix

### Gestion du risque
- Volatilité mesurée par ATR
- Spread bid/ask surveillé
- Liquidité vérifiée avant alerte
- Confirmation multi-indicateurs requise

## 🚢 Déploiement

### Railway (recommandé)

```bash
# Variables d'environnement dans Railway
NEWS_API_KEY=xxx
EMAIL_USER=xxx
EMAIL_PASS=xxx
EMAIL_TARGET=xxx
RUN_MODE=continuous

# Le bot démarre automatiquement
```

### PythonAnywhere

```bash
# Tâche planifiée (cron)
0 */1 * * * cd /home/username/finance_monitor && python main.py --once
```

### Docker

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

## 📊 Actifs surveillés

### Actions françaises (37)
- **Tech** : STMicroelectronics, Ubisoft, Atos, OVH, Dassault Systèmes
- **Énergie** : Engie, TotalEnergies, Engie, Lhyfe (hydrogène)
- **Auto** : Stellantis, Renault, Valeo, Forvia
- **Industrie** : ArcelorMittal, Bouygues, Saint-Gobain
- **Santé** : Sanofi, Carmat, Valneva
- **Distribution** : Carrefour, Casino
- **Et plus...**

### Cryptomonnaies (60+)
- **Majors** : ETH, SOL, ADA, LINK
- **DeFi** : UNI, MKR, AAVE
- **Layer 2** : ARB, MATIC, OP
- **Gaming** : MANA, GALA, ENJ
- **AI/Computing** : FET, RNDR
- **Et plus...**

## 🛠️ Maintenance

### Base de données
```sql
-- Tables SQLite
- price_history    : Historique des prix
- alerts_sent      : Alertes envoyées
- news_tracked     : Articles traités
```

### Logs
```bash
# Consulter les logs
tail -f logs/finance_monitor_20240101.log

# Nettoyer anciens logs
find logs/ -name "*.log" -mtime +30 -delete
```

### Sauvegarde
```bash
# Sauvegarder la base de données
cp finance_monitor.db backups/finance_monitor_$(date +%Y%m%d).db

# Script de sauvegarde automatique (cron)
0 2 * * * /path/to/backup_script.sh
```

## 🔧 Dépannage

### Problèmes fréquents

#### 1. Erreur d'authentification Gmail
```
SMTPAuthenticationError: 535, b'5.7.8 Username and Password not accepted'
```
**Solution** : 
- Activer la validation en 2 étapes sur Gmail
- Générer un mot de passe d'application spécifique
- Utiliser ce mot de passe au lieu du mot de passe habituel

#### 2. Rate limit CoinGecko
```
Error: 429 Too Many Requests
```
**Solution** :
- Le bot gère automatiquement avec un cache de 5 minutes
- Si persiste : réduire le nombre de cryptos surveillées
- Envisager CoinGecko Pro API (payant)

#### 3. Données Yahoo Finance manquantes
```
No data found for symbol XXX.PA
```
**Solution** :
- Vérifier que le symbole est correct (suffixe .PA pour Paris)
- Le marché est peut-être fermé
- Certaines petites actions peuvent avoir peu de données

#### 4. Webhook Slack ne fonctionne pas
```
Error sending Slack notification
```
**Solution** :
- Vérifier l'URL du webhook
- Tester avec : `curl -X POST -H 'Content-type: application/json' --data '{"text":"Test"}' YOUR_WEBHOOK_URL`

### Commandes utiles de débogage

```bash
# Tester uniquement les connexions
python main.py --mode test

# Lancer avec logs détaillés
python main.py --log-level DEBUG

# Vérifier la base de données
sqlite3 finance_monitor.db "SELECT COUNT(*) FROM price_history;"

# Analyser un seul actif (dans Python)
from analysis.orderbook import OrderBookIntegration
oi = OrderBookIntegration()
analysis = oi.analyze_crypto("ETH", 3500.0)
print(analysis.interpretation)
```

## 📊 Exemples de personnalisation

### Ajouter un nouvel actif

```python
# Dans config.py, ajouter à 'stocks' ou 'crypto'
"NOUVEAU.PA": {
    "name": "Nouvelle Entreprise",
    "thresholds": {
        "high": 100.0,
        "low": 50.0,
        "change_percent": 10.0
    }
}
```

### Modifier les horaires de rapport

```python
# Dans core/monitor.py, méthode _check_daily_reports()
# Changer les heures (format 24h)
if 8 <= current_hour <= 9:  # Rapport à 8h30 au lieu de 9h30
    if (current_hour == 8 and current_minute >= 30) or (current_hour == 9 and current_minute <= 30):
```

### Ajouter un indicateur technique

```python
# Dans analysis/indicators.py
def calculate_williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
    """Williams %R oscillator"""
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    wr = -100 * ((highest_high - close) / (highest_high - lowest_low))
    return wr
```

### Personnaliser les templates d'email

```python
# Dans core/monitor.py, méthode _create_html_email()
# Modifier les styles CSS ou la structure HTML
```

## 📈 Performances et optimisations

### Consommation des ressources
- **RAM** : ~100-200 MB en fonctionnement normal
- **CPU** : Pics lors des analyses (< 5% en moyenne)
- **Disque** : ~50 MB + logs (rotation recommandée)
- **Réseau** : ~10-50 MB/jour selon configuration

### Optimisations possibles
1. **Réduire les appels API** :
   - Augmenter le cache à 10 minutes
   - Grouper les requêtes
   - Utiliser des APIs premium

2. **Base de données** :
   - Indexer les colonnes fréquemment requêtées
   - Purger l'historique ancien (> 6 mois)
   - Passer à PostgreSQL pour gros volumes

3. **Performances** :
   - Utiliser asyncio pour les requêtes parallèles
   - Implémenter un pool de connexions
   - Cache Redis pour multi-instances

## 🔒 Sécurité

### Bonnes pratiques
1. **Ne jamais commiter** :
   - Fichiers .env
   - Clés API en dur
   - Mots de passe

2. **Utiliser des secrets** :
   - Variables d'environnement
   - Gestionnaire de secrets (Vault, AWS Secrets)
   - Chiffrement des données sensibles

3. **Limiter les accès** :
   - Webhook Slack en HTTPS uniquement
   - Rotation régulière des clés API
   - Logs sans données sensibles

### Checklist de sécurité
- [ ] .env dans .gitignore
- [ ] Mots de passe forts
- [ ] 2FA sur tous les comptes
- [ ] Logs anonymisés
- [ ] Backups chiffrés
- [ ] Accès serveur sécurisé (SSH keys)

## 📊 Métriques et monitoring

### KPIs du bot
- Nombre d'alertes envoyées / jour
- Taux de faux positifs
- Temps de réponse moyen
- Uptime du service

### Intégration monitoring
```python
# Exemple avec Prometheus
from prometheus_client import Counter, Histogram, start_http_server

alerts_sent = Counter('finance_bot_alerts_sent', 'Total alerts sent')
api_response_time = Histogram('finance_bot_api_response_seconds', 'API response time')

# Dans le code
alerts_sent.inc()
with api_response_time.time():
    # appel API
```

## 🌍 Internationalisation

Le bot supporte actuellement :
- Interface : Français / Anglais (commentaires)
- Devises : EUR (conversion automatique depuis USD)
- Fuseaux : Europe/Paris (configurable)

Pour ajouter une langue :
1. Créer un fichier `locales/es.json` (exemple espagnol)
2. Traduire les messages
3. Charger selon la config utilisateur

## 🚀 Roadmap

### Version 2.0 (Q2 2025)
- [ ] Interface web React
- [ ] WebSocket pour temps réel
- [ ] Multi-utilisateurs
- [ ] Backtesting intégré

### Version 3.0 (Q4 2025)
- [ ] Machine Learning predictions
- [ ] Auto-trading (paper trading)
- [ ] Mobile app
- [ ] Cloud-native architecture

## 💡 FAQ

**Q: Puis-je utiliser ce bot pour du trading automatique ?**
R: Le bot est conçu pour la surveillance et l'alerte uniquement. L'ajout de trading automatique nécessiterait des modifications importantes et une gestion des risques appropriée.

**Q: Combien d'actifs puis-je surveiller ?**
R: Techniquement illimité, mais les APIs gratuites ont des limites (CoinGecko: ~50 requêtes/minute). Recommandé : 50-100 actifs maximum.

**Q: Le bot fonctionne-t-il 24/7 ?**
R: Oui, il s'adapte aux heures de marché. Surveillance continue pour les cryptos, horaires de bourse pour les actions.

**Q: Puis-je l'héberger gratuitement ?**
R: Oui ! Railway offre 500h gratuites/mois, PythonAnywhere a un tier gratuit, et vous pouvez utiliser un Raspberry Pi.

**Q: Comment ajouter mes propres stratégies ?**
R: Créez une nouvelle méthode dans `analysis/strategy.py` et intégrez-la dans `analyze_asset()`. Voir la documentation des modules.

## 🤝 Contribution

Les contributions sont bienvenues ! Pour contribuer :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

### Guidelines de contribution
- Code en anglais, commentaires en français OK
- Tests unitaires pour nouvelles features
- Documentation à jour
- Respect du style PEP 8
- Revue de code obligatoire

### Idées d'amélioration
- [ ] Interface web de monitoring
- [ ] Backtesting des stratégies
- [ ] Machine Learning pour prédictions
- [ ] Intégration Telegram
- [ ] Support d'autres exchanges (Kraken, Bitfinex)
- [ ] Portfolio optimization (Markowitz)
- [ ] Sentiment analysis Twitter/Reddit
- [ ] Trading paper (simulation)
- [ ] Export Excel des rapports
- [ ] Graphiques TradingView intégrés

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## ⚠️ Avertissement

Ce bot est un outil d'aide à la décision. Il ne constitue pas un conseil en investissement. Faites toujours vos propres recherches avant d'investir.

## 📞 Support

- **Issues** : [GitHub Issues](https://github.com/votre-username/finance-monitor/issues)
- **Email** : votre.email@gmail.com
- **Documentation** : Ce README + commentaires dans le code

---

**Développé avec ❤️ par [Votre Nom]**

*Dernière mise à jour : Janvier 2025*
