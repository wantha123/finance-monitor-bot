
# 🤖 Market Watch Bot – Modular Version

Surveillance intelligente des marchés financiers (actions, crypto) avec alertes automatisées, analyse technique, carnet d’ordres, stockage cloud Supabase, sauvegarde Backblaze B2, et déploiement Railway.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Supabase](https://img.shields.io/badge/database-Supabase-brightgreen.svg)
![Backblaze](https://img.shields.io/badge/backup-BackblazeB2-red.svg)
![CI](https://github.com/wantha123/finance-monitor-bot/actions/workflows/test.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 📋 Table des matières

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Installation rapide (Bootstrap)](#-installation-rapide-bootstrap)
- [Configuration](#configuration)
- [Utilisation CLI](#utilisation-cli)
- [Modules](#modules)
- [Déploiement Railway](#déploiement-railway)
- [Sécurité](#sécurité)
- [Roadmap](#roadmap)

## 🚀 Fonctionnalités

- 🔄 Surveillance des actions (Yahoo Finance) et cryptos (CoinGecko)
- ⚙️ Analyse technique multi-modules (RSI, MACD, carnets, volatilité, etc.)
- 📊 Score d’opportunité pondéré via moteur de stratégie
- 📨 Alertes par Email et Slack
- 🧠 Interface CLI pour gestion rapide
- 🌐 Intégration Supabase (DB cloud) + Backblaze B2 (backups JSON)
- 🔁 Scheduler automatique via APScheduler
- ✅ Déploiement complet sur Railway (Docker-ready)

## 🧱 Architecture

```
finance-monitor-bot/
├── main.py                     → Point d'entrée principal
├── config.py                   → Chargement des variables via .env
├── bootstrap.sh                → Script d’installation rapide
├── requirements.txt            → Dépendances précises
├── modules/                    → Modules d’analyse spécialisés
├── storage/                    → Connexion Supabase, Backup B2
├── alerts/                     → Systèmes de notification
├── scheduler/                  → Orchestrateur de tâches
├── deployment/                 → Dockerfile, init_supabase.sql
├── tests/                      → Tests unitaires par module
├── .env.example                → Fichier d’environnement à copier
└── .github/workflows/test.yml → CI GitHub Actions
```

## ⚙️ Installation rapide (Bootstrap)

Pour initialiser automatiquement l'environnement de travail :

### 🐧 Linux / MacOS

```bash
chmod +x bootstrap.sh
./bootstrap.sh
```

### 🪟 Windows (Git Bash ou WSL)

```bash
bash bootstrap.sh
```

Ce script va :
- Créer un environnement virtuel Python
- Installer toutes les dépendances
- Générer un fichier `.env.example`
- Afficher les instructions pour la suite

Une fois installé :
```bash
# Pour tester la configuration
python main.py --test

# Pour démarrer le bot
python main.py
```

## 🧠 Modules d’analyse

| Module                     | Description                                                  |
|----------------------------|--------------------------------------------------------------|
| `price_trend_analyzer`     | Moyennes, MACD, RSI, Bollinger                               |
| `volatility_monitor`       | ATR, détection de pics                                       |
| `orderbook_analyzer`       | Pression acheteurs/vendeurs (Binance, Kraken…)              |
| `google_trends_signal`     | Analyse d’intérêt public via Google Trends                  |
| `strategy_engine`          | Pondération des signaux en score final                       |
| `news_sentiment_analyzer`  | *À faire via Claude Opus* – Analyse NLP des news             |
| `social_hype_tracker`      | *À faire via Claude Opus* – Réseaux sociaux, FOMO            |

## 📈 Google Trends (module ajouté)

- Utilise la librairie `pytrends` pour obtenir l’intérêt public sur des mots-clés.
- Normalise le score autour de 0 (50 = neutre).
- Peut déclencher des alertes si le score dépasse 80.
- Intégré dans le moteur de stratégie avec une pondération par défaut de **10%**.

## ⚙️ Configuration

Copier le fichier `.env.example` généré par le script :

```bash
cp .env.example .env
```

Et renseigner :
- Clé NewsAPI
- Adresse email d’envoi et de réception
- Webhook Slack (facultatif)
- Clés Supabase et Backblaze

## 🖥️ Utilisation CLI

```bash
# Ajouter un actif avec seuils personnalisés
python cli.py add ETH 3000 1800 7.5

# Lister les actifs surveillés
python cli.py list

# Afficher l’état interne
python cli.py state
```

## ☁️ Déploiement Railway

Ajouter les variables `.env` dans le tableau "Variables" de Railway et lancer le service avec :

```bash
python main.py --once   # pour déclenchement périodique par Railway cron
```

Configurer les backups vers Backblaze dans `scheduler/orchestration_engine.py` ou CRON.

## 🔐 Sécurité

- `.env` est ignoré par `.gitignore`
- Clés API séparées dans `.env`
- Accès Supabase restreint par clé privée

## 📌 Roadmap

- [x] Migration SQLite → Supabase
- [x] Intégration Google Trends
- [x] Script bootstrap.sh
- [x] GitHub Actions (tests automatiques)
- [ ] Modules IA (news/sentiment/FOMO)
- [ ] Backtesting intégré
