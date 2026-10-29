# Tableau de bord IHPC — Streamlit

Application exploratoire des relevés de prix IvoirShop et Adjovan.

## Lancer en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Déposez `prix_nettoyes_rapproches.csv` dans `data/`. Le fichier optionnel `indices_quotidiens.csv` sera utilisé s’il existe; sinon les indices quotidiens sont recalculés à base fixe (premier jour = 100), Jevons par variété et agrégation Young pondérée. Les indices restent exploratoires.

## Streamlit Community Cloud

1. Publiez ce dépôt GitHub (la cellule GitHub du notebook automatise la création et le push).
2. Connectez-vous à [Streamlit Community Cloud](https://share.streamlit.io/) et choisissez **New app**.
3. Sélectionnez le dépôt, la branche `main` et le fichier principal `app.py`, puis cliquez **Deploy**.
4. Le dépôt doit contenir `data/prix_nettoyes_rapproches.csv`; les nouvelles données sont publiées avec la cellule **Actualiser** du notebook.
5. Les redéploiements suivent les pushes GitHub. Ne mettez aucun jeton dans le dépôt; le jeton GitHub est demandé en mémoire dans Colab.
