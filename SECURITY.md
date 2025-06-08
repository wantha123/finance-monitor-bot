
# 🔐 Guide de Sécurité – Market Watch Bot

Ce fichier décrit les bonnes pratiques mises en œuvre pour sécuriser ce projet.

## ✅ Éléments de sécurité actifs

### 🔒 .env et secrets
- Toutes les **clés sensibles** (API, email, Supabase, B2) sont stockées dans `.env`
- Le fichier `.env` est **exclu du dépôt** via `.gitignore`
- Un fichier `.env.example` est fourni sans données sensibles

### ☁️ Variables d’environnement sur Railway
- Toutes les clés sont redéfinies dans l’interface Railway
- Aucune valeur secrète n’est stockée dans le code

### 🛡 Supabase
- Utilisation de la clé `service_role` uniquement côté serveur
- Les accès publics doivent utiliser la `anon` key avec **RLS activé**
- Aucun token Supabase n’est committé

### 🔑 SMTP, Slack, Backblaze
- Email via mot de passe d'application uniquement
- Webhook Slack utilisé au lieu d’un token utilisateur
- Clé Backblaze restreinte à un bucket dédié

---

## 🚫 Ce qu’il ne faut jamais faire

- **Ne jamais commit** un fichier `.env` ou `.json` contenant des secrets
- Ne jamais écrire de clés dans `config.py` (toujours via `os.getenv`)
- Ne jamais exposer la `service_role` dans un frontend ou API publique
- Ne jamais laisser un token apparaître dans une URL ou un log

---

## 🔍 Recommandations supplémentaires

- Activer **2FA** sur tous les comptes associés (GitHub, Supabase, Google)
- Changer régulièrement les mots de passe d'application
- Si vous avez accidentellement commit un secret :
  - Révoquez la clé immédiatement
  - Utilisez `git filter-repo` pour le purger de l'historique

---

## 📅 Vérifications recommandées

| Fréquence | Vérification                                   |
|-----------|------------------------------------------------|
| À chaque commit | Aucune fuite de `.env` dans le diff     |
| 1x / mois  | Rotation des clés Backblaze / SMTP            |
| 1x / sprint| Audit Supabase : clés, accès, règles RLS      |
