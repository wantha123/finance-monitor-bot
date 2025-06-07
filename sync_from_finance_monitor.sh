#!/bin/bash

# Branch source
SOURCE_BRANCH="finance_monitor"

# Branches cibles
TARGET_BRANCHES=("alerts" "analysis" "data" "social")

# Dossiers/fichiers à copier
ITEMS_TO_COPY=("core/" "alerts/" "data/")

# Assure-toi que tu es à la racine du projet
cd "$(dirname "$0")"

# Récupère toutes les branches distantes
git fetch origin

# Boucle sur chaque branche cible
for BRANCH in "${TARGET_BRANCHES[@]}"; do
    echo "🔄 Sync vers branche: $BRANCH"

    # Bascule sur la branche cible
    git checkout "$BRANCH"
    git pull origin "$BRANCH"

    # Copie les éléments depuis la branche source
    for ITEM in "${ITEMS_TO_COPY[@]}"; do
        git checkout "$SOURCE_BRANCH" -- "$ITEM"
    done

    # Commit et push
    git add .
    git commit -m "🔁 Sync de ${ITEMS_TO_COPY[*]} depuis $SOURCE_BRANCH"
    git push origin "$BRANCH"
done

echo "✅ Synchronisation terminée."
