#!/bin/bash
# bootstrap.sh - Initialisation rapide du Finance Monitor Bot (version modulaire)

echo "🚀 Finance Monitor Bot (Modulaire) - Installation"
echo "==============================================="

# Vérification Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non détecté. Installez-le d'abord."
    exit 1
fi

echo "✅ Python 3 détecté: $(python3 --version)"

# Création environnement virtuel
echo "📦 Création de l'environnement virtuel..."
python3 -m venv venv

# Activation environnement
echo "🔧 Activation de l'environnement..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Installation des dépendances
echo "📚 Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt

# Création du .env.example
echo "📝 Génération de .env.example..."
cat > .env.example << EOL
# API Keys
NEWS_API_KEY=your_newsapi_key_here

# Email Configuration
EMAIL_USER=your.email@gmail.com
EMAIL_PASS=your_gmail_app_password
EMAIL_TARGET=recipient@email.com

# Slack Configuration (optional)
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_key

# Backblaze B2
B2_KEY_ID=your_b2_key_id
B2_APPLICATION_KEY=your_b2_app_key
B2_BUCKET_ID=your_b2_bucket_id

# Mode
TEST_MODE=false
RUN_MODE=continuous
EOL

# Instructions post-install
echo ""
echo "✨ Installation terminée !"
echo ""
echo "📋 Étapes suivantes :"
echo "1. Copier .env.example vers .env et le configurer :"
echo "   cp .env.example .env"
echo ""
echo "2. Lancer un test de configuration :"
echo "   python main.py --test"
echo ""
echo "3. Lancer le bot :"
echo "   python main.py"
echo ""
echo "📚 Pour en savoir plus, lire le fichier README.md"
