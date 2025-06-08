
# 📦 Image officielle Python
FROM python:3.10-slim

# 🧱 Création du dossier de travail
WORKDIR /app

# 📄 Copie des fichiers
COPY . .

# 🧪 Installation des dépendances
RUN pip install --no-cache-dir -r requirements.txt

# 🔁 Commande par défaut
CMD ["python", "main.py"]
