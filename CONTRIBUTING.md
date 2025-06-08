
# 🤝 Guide de contribution – Market Watch Bot

Merci de votre intérêt pour ce projet ! Voici quelques règles pour contribuer efficacement :

## ✅ Comment contribuer

1. Fork du projet
2. Créez une branche dédiée :
   ```bash
   git checkout -b feature/nom-fonction
   ```
3. Codez, testez, et ajoutez vos commits
4. Lancez les tests :
   ```bash
   pytest tests/
   ```
5. Créez une Pull Request claire avec le modèle PR fourni

## 📁 Structure des dossiers

- `modules/` : chaque sous-module métier
- `storage/` : accès Supabase, backup B2
- `tests/` : un fichier de test par module
- `scheduler/` : orchestrateur de tâches

## ✅ Bonnes pratiques

- Aucune clé API ne doit figurer en dur
- Toujours utiliser `os.getenv()`
- Test unitaire minimal requis pour chaque PR
- Suivre PEP8 / flake8

Merci 🙏
