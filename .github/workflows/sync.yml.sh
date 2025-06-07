name: Sync branches from finance_monitor

on:
  workflow_dispatch:  # Cela permet de lancer le script manuellement

jobs:
  sync-branches:
    runs-on: ubuntu-latest

    steps:
    - name: 🔁 Cloner le repo
      uses: actions/checkout@v3
      with:
        fetch-depth: 0  # Important pour accéder à toutes les branches

    - name: ⚙️ Configurer Git
      run: |
        git config user.name "GitHub Actions"
        git config user.email "actions@github.com"

    - name: ✅ Rendre le script exécutable et l'exécuter
      run: |
        chmod +x sync_from_finance_monitor.sh
        ./sync_from_finance_monitor.sh
