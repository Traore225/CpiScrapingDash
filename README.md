# Tableau de bord IHPC — Streamlit

Prototype descriptif pour les relevés de prix IvoirShop et Adjovan. Les indices affichés sont exploratoires et ne remplacent pas une production statistique officielle.

## Démarrage local

```bash
pip install -r requirements.txt
mkdir -p data
cp prix_nettoyes_rapproches.csv data/
streamlit run app.py
```

Le fichier `data/indices_quotidiens.csv` est facultatif : en son absence, l’application recalcule un indice quotidien à base fixe (premier jour = 100), avec Jevons au niveau variété et Young pondéré par `Depense_pe` pour les agrégats. Le CSV de prix contient notamment `date`, `site`, `libelle_produit`, `cle_produit`, `code_variete`, `prix`, `apparie`, `poids`, `categorie`, `prix_promo` et `remise_pct`.

## Onglets

- **Synthèse** : observations, prix moyens/médians et commentaire descriptif automatique.
- **Indices** : séries globales et COICOP, variations entre dates.
- **Comparaison des sites** : distribution et médianes pour un produit.
- **Hausses/Baisses et contributions** : variétés en extrêmes; la contribution présentée est explicitement une approximation, pas une contribution budgétaire officielle.
- **Promotions** : fréquence et remises observées.
- **Volatilité & distributions** : distribution des variations successives, médiane et dispersion interquartile; les intervalles de dates ne sont pas annualisés.
- **Qualité des données** : rapprochement et disponibilité des produits.
- **Données** : consultation et téléchargement du tableau filtré.

Les filtres site, période et catégorie s’appliquent aux observations. Les données manquantes et les prix extrêmes ne sont pas imputés/supprimés par le dashboard.

## Déploiement Streamlit Community Cloud

Publiez le dépôt contenant `app.py`, `requirements.txt` et `data/prix_nettoyes_rapproches.csv`, puis sélectionnez `app.py` comme fichier principal. N’incluez aucun jeton secret dans le dépôt.

## Charte graphique ANSTAT

Le tableau de bord adopte la palette ANSTAT : orange principal `#F39323`, vert `#49655A`, complétés par les verts `#0A966F`, `#0C6B23`, `#8CC048` et les orangés `#EF7911`, `#F6A000`, `#FCBF00`, ainsi que des neutres `#1D1D1B`, `#555454`, `#9F9F9F`, `#CCCCCC`. Les titres, onglets, métriques, tableaux et graphiques sont harmonisés; IvoirShop est représenté en orange et Adjovan en vert.

Pour ajouter le logo institutionnel, placez le fichier PNG sous `assets/logo_anstat.png` (à côté de `app.py`). Un recadrage du logo fourni dans l’image de charte est livré sous `assets/logo_anstat.png`; remplacez-le par un original haute définition si vous en disposez. En son absence, l’en-tête affiche automatiquement une marque textuelle stylisée « Anstat ». `assets/logo_placeholder.svg` reste une maquette; elle n’est pas utilisée comme logo institutionnel. Le CSS de l’application reste actif même sans `.streamlit/config.toml`; le thème Streamlit recommandé est livré dans ce dossier.
