
# 🚀 Déploiement sur Railway – Guide de Configuration

Ce guide explique comment configurer correctement les variables d’environnement et le démarrage du bot Market Watch sur Railway.

---

## 🔑 Variables d’environnement à définir

Railway **n'utilise pas `.env`**, vous devez définir les variables **manuellement dans l’interface Railway**.

Rendez-vous dans :
```
Project > Variables > Add Variable
```

Copiez-y les clés suivantes depuis votre `.env` local :

| Variable            | Description                             |
|---------------------|-----------------------------------------|
| `SUPABASE_URL`      | URL de votre projet Supabase            |
| `SUPABASE_KEY`      | Clé `service_role` (⚠️ privée)         |
| `EMAIL_USER`        | Adresse Gmail utilisée pour les alertes |
| `EMAIL_PASS`        | Mot de passe d’application Gmail        |
| `EMAIL_TARGET`      | Adresse du destinataire                 |
| `SLACK_WEBHOOK`     | (Optionnel) Webhook Slack               |
| `NEWS_API_KEY`      | Clé gratuite NewsAPI.org                |
| `B2_KEY_ID`         | (Optionnel) Backblaze Key ID            |
| `B2_APPLICATION_KEY`| (Optionnel) Backblaze App Key           |
| `B2_BUCKET_ID`      | (Optionnel) ID du bucket B2             |
| `RUN_MODE`          | `continuous` ou `once`                  |
| `TEST_MODE`         | `false` (ou `true` pour debug)          |

---

## ⚙️ Configuration du service

Dans Railway :

1. Ajoutez votre dépôt GitHub
2. Définissez la **commande de démarrage** :
   ```
   python main.py
   ```

3. (Optionnel) Ajoutez un second service CRON ou Web si besoin
4. Vérifiez les logs et l’environnement

---

## 🛡️ Conseils de sécurité

- Ne jamais mettre de `.env` dans le dépôt
- Ne jamais exposer la `service_role` à un client (web, JS)
- Les clés sont stockées chiffrées sur Railway

---

## ✅ Vérification

Lancez dans la console Railway :
```bash
python main.py --test
```

Cela vous permettra de valider que toutes les variables sont bien chargées.

