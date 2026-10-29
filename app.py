# -*- coding: utf-8 -*-
"""Tableau de bord exploratoire de suivi des prix et indices quotidiens IHPC."""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

DOSSIER = Path(__file__).resolve().parent
DOSSIER_DATA = DOSSIER / "data"
FICHIER_PRIX = "prix_nettoyes_rapproches.csv"
FICHIER_INDICES = "indices_quotidiens.csv"

st.set_page_config(page_title="IHPC | Suivi des prix", page_icon="📊", layout="wide")
st.title("Suivi quotidien des prix — IHPC")
st.caption("Prototype descriptif pour les relevés IvoirShop et Adjovan. Les indices sont exploratoires.")


@st.cache_data(show_spinner=False)
def lire_csv(chemin: str, signature: int) -> pd.DataFrame:
    """Lecture mise en cache; la signature change dès que le fichier est actualisé."""
    del signature
    return pd.read_csv(chemin, encoding="utf-8-sig", low_memory=False)


def charger_csv(nom: str) -> pd.DataFrame:
    """Charge un CSV du répertoire data, ou renvoie un tableau vide s'il manque."""
    chemin = DOSSIER_DATA / nom
    if not chemin.exists():
        return pd.DataFrame()
    return lire_csv(str(chemin), chemin.stat().st_mtime_ns)


def colonne_ou(df: pd.DataFrame, nom: str, valeur_par_defaut=np.nan) -> pd.Series:
    """Retourne une colonne ou une série par défaut de même index."""
    if nom in df.columns:
        return df[nom]
    return pd.Series(valeur_par_defaut, index=df.index)


def calculer_indices(prix: pd.DataFrame) -> pd.DataFrame:
    """Calcule Jevons à base fixe (premier jour=100), puis Young pondéré.

    Les relatifs Jevons d'une variété utilisent les mêmes produits appariés au jour
    de base et au jour courant. Les poids sont normalisés sur les variétés présentes.
    Le global et les niveaux COICOP de 2/4 chiffres sont calculés par site et tous sites.
    """
    colonnes = ["date", "site", "niveau", "code_niveau", "code_variete", "indice",
                "variation_jour_pct", "nb_produits", "nb_varietes", "methode"]
    d = prix.copy()
    d["apparie"] = colonne_ou(d, "apparie", False).astype(str).str.lower().isin(["true", "1", "oui"])
    d["code_variete"] = colonne_ou(d, "code_variete").astype("string").str.replace(r"\.0$", "", regex=True).str.zfill(12)
    d["cle_produit"] = colonne_ou(d, "cle_produit", "").fillna("").astype(str)
    d["prix"] = pd.to_numeric(colonne_ou(d, "prix"), errors="coerce")
    d["date"] = pd.to_datetime(colonne_ou(d, "date"), errors="coerce").dt.strftime("%Y-%m-%d")
    d["site"] = colonne_ou(d, "site", "Inconnu").fillna("Inconnu").astype(str)
    d = d[d["apparie"] & d["code_variete"].str.fullmatch(r"\d{12}", na=False)
          & d["prix"].gt(0) & d["date"].notna()].copy()
    if d.empty:
        return pd.DataFrame(columns=colonnes)

    # Consolide les doublons puis ajoute une série moyenne « Tous sites ».
    d = d.groupby(["date", "site", "code_variete", "cle_produit"], as_index=False)["prix"].mean()
    tous = d.groupby(["date", "code_variete", "cle_produit"], as_index=False)["prix"].mean()
    tous["site"] = "Tous sites"
    d = pd.concat([d, tous], ignore_index=True)
    poid = pd.to_numeric(colonne_ou(prix, "poids"), errors="coerce")
    poids_ref = prix.assign(_poids=poid).groupby("code_variete", dropna=True)["_poids"].first().to_dict()

    var_lignes = []
    for site, serie in d.groupby("site", sort=True):
        for code, v in serie.groupby("code_variete", sort=True):
            # Chaque variété commence à 100 lors de sa première observation disponible.
            jour_base = v["date"].min()
            p0 = v[v["date"].eq(jour_base)].set_index("cle_produit")["prix"]
            var_lignes.append({"date": jour_base, "site": site, "niveau": "variete",
                               "code_niveau": code, "code_variete": code, "indice": 100.0,
                               "nb_produits": len(p0), "methode": "base"})
            for jour in sorted(v.loc[v["date"].ne(jour_base), "date"].unique()):
                pt = v[v["date"].eq(jour)].set_index("cle_produit")["prix"]
                commun = p0.index.intersection(pt.index)
                if len(commun) == 0:
                    continue
                relatifs = pt.loc[commun].to_numpy(float) / p0.loc[commun].to_numpy(float)
                var_lignes.append({"date": jour, "site": site, "niveau": "variete",
                                   "code_niveau": code, "code_variete": code,
                                   "indice": float(np.exp(np.log(relatifs).mean()) * 100),
                                   "nb_produits": len(commun), "methode": "jevons_base_fixe"})
    var = pd.DataFrame(var_lignes)
    if var.empty:
        return pd.DataFrame(columns=colonnes)
    var["_poids"] = var["code_variete"].map(poids_ref).fillna(1.0)
    agg = []
    for (site, jour), groupe in var.groupby(["site", "date"], sort=True):
        for digits in (2, 4):
            temp = groupe.copy()
            temp["_coicop"] = temp["code_variete"].astype(str).str[:digits]
            for code, sous in temp.groupby("_coicop"):
                poids = sous["_poids"].clip(lower=0)
                if poids.sum() > 0:
                    agg.append({"date": jour, "site": site, "niveau": f"coicop_{digits}",
                                "code_niveau": code, "code_variete": np.nan,
                                "indice": float(np.average(sous["indice"], weights=poids)),
                                "nb_produits": int(sous["nb_produits"].sum()),
                                "nb_varietes": len(sous), "methode": "young_pondere"})
        poids = groupe["_poids"].clip(lower=0)
        if poids.sum() > 0:
            agg.append({"date": jour, "site": site, "niveau": "global", "code_niveau": "TOUS",
                        "code_variete": np.nan,
                        "indice": float(np.average(groupe["indice"], weights=poids)),
                        "nb_produits": int(groupe["nb_produits"].sum()),
                        "nb_varietes": len(groupe), "methode": "young_pondere"})
    resultat = pd.concat([var, pd.DataFrame(agg)], ignore_index=True, sort=False)
    resultat["variation_jour_pct"] = resultat.sort_values("date").groupby(
        ["site", "niveau", "code_niveau"])["indice"].pct_change() * 100
    for col in colonnes:
        if col not in resultat:
            resultat[col] = np.nan
    return resultat[colonnes]


def commentaire_regle(serie: pd.Series, etiquette: str) -> str:
    """Produit un constat déterministe et descriptif, sans extrapolation."""
    valeurs = pd.to_numeric(serie, errors="coerce").dropna()
    if valeurs.empty:
        return f"Aucune valeur exploitable pour {etiquette} avec ces filtres."
    if len(valeurs) < 2 or valeurs.nunique() < 2:
        return f"{etiquette} est stable ou ne comporte qu'une observation sur la période."
    depart, fin = float(valeurs.iloc[0]), float(valeurs.iloc[-1])
    if depart == 0:
        return f"{etiquette} varie; la variation relative n'est pas calculable depuis une valeur initiale nulle."
    variation = (fin / depart - 1) * 100
    sens = "augmente" if variation > 0 else "diminue" if variation < 0 else "reste stable"
    return f"Selon les observations affichées, {etiquette} {sens} de {abs(variation):.1f} % entre les bornes. Constat descriptif, pas une prévision."


prix = charger_csv(FICHIER_PRIX)
if prix.empty:
    st.error("CSV de prix absent ou vide. Placez prix_nettoyes_rapproches.csv dans dashboard/data/.")
    st.stop()

# Harmonise les colonnes attendues sans écarter les colonnes personnalisées.
prix["date"] = pd.to_datetime(colonne_ou(prix, "date"), errors="coerce")
prix["prix"] = pd.to_numeric(colonne_ou(prix, "prix"), errors="coerce")
prix["site"] = colonne_ou(prix, "site", "Inconnu").fillna("Inconnu").astype(str)
prix["categorie"] = colonne_ou(prix, "categorie", "Non renseignée").fillna("Non renseignée").astype(str)
prix["libelle_produit"] = colonne_ou(prix, "libelle_produit", "Produit non renseigné").fillna("Produit non renseigné").astype(str)
prix["code_variete"] = colonne_ou(prix, "code_variete").astype("string")
prix = prix.dropna(subset=["date", "prix"])
if prix.empty:
    st.error("Aucune observation avec une date et un prix valides.")
    st.stop()

indices = charger_csv(FICHIER_INDICES)
if not indices.empty and {"date", "indice", "niveau", "site"}.issubset(indices.columns):
    indices["date"] = pd.to_datetime(indices["date"], errors="coerce")
    indices["indice"] = pd.to_numeric(indices["indice"], errors="coerce")
    if "variation_jour_pct" in indices:
        indices["variation_jour_pct"] = pd.to_numeric(indices["variation_jour_pct"], errors="coerce")
else:
    indices = calculer_indices(prix)
    st.sidebar.info("Indice quotidien recalculé à base fixe : CSV d'indices absent ou incomplet.")

# Filtres partagés par les sections du tableau de bord.
dates = sorted(prix["date"].dt.date.dropna().unique())
with st.sidebar:
    st.header("Filtres")
    sites = sorted(prix["site"].unique())
    sites_selectionnes = st.multiselect("Sites", sites, default=sites)
    if len(dates) > 1:
        periode = st.date_input("Période", value=(dates[0], dates[-1]), min_value=dates[0], max_value=dates[-1])
        if isinstance(periode, (tuple, list)) and len(periode) == 2:
            debut, fin = periode
        else:
            debut = fin = periode
    else:
        debut = fin = dates[0]
        st.info(f"Une seule date disponible ({debut}) : filtre de période désactivé.")
    categories = sorted(prix["categorie"].unique())
    categories_selectionnees = st.multiselect("Catégories", categories, default=categories)
    produits = sorted(prix["libelle_produit"].unique())
    produit_compare = st.selectbox("Produit à comparer", produits) if produits else None

filtre = prix[prix["site"].isin(sites_selectionnes) & prix["categorie"].isin(categories_selectionnees)].copy()
filtre = filtre[filtre["date"].dt.date.between(debut, fin)]
indices_filtres = indices.copy()
if not indices_filtres.empty:
    indices_filtres = indices_filtres[indices_filtres["date"].dt.date.between(debut, fin)]
    indices_filtres = indices_filtres[indices_filtres["site"].isin(sites_selectionnes + ["Tous sites"])]

onglets = st.tabs(["Synthèse", "Indices", "Comparaison des sites", "Hausses/Baisses et contributions",
                   "Promotions", "Qualité des données", "Données"])

with onglets[0]:
    st.subheader("Synthèse de la période")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Observations", f"{len(filtre):,}")
    k2.metric("Prix moyen", f"{filtre['prix'].mean():,.0f}" if not filtre.empty else "—")
    k3.metric("Prix médian", f"{filtre['prix'].median():,.0f}" if not filtre.empty else "—")
    k4.metric("Produits distincts", f"{filtre['cle_produit'].nunique():,}" if "cle_produit" in filtre and not filtre.empty else f"{filtre['libelle_produit'].nunique():,}")
    st.info(commentaire_regle(filtre.sort_values("date").groupby("date")["prix"].mean(), "Le prix moyen"))
    if filtre.empty:
        st.warning("Aucune observation ne correspond à la sélection courante.")

with onglets[1]:
    st.subheader("Indice global et COICOP — variation jour/jour")
    if indices_filtres.empty:
        st.info("Aucun indice disponible pour la période sélectionnée.")
    else:
        global_ix = indices_filtres[indices_filtres["niveau"].astype(str).eq("global")]
        if not global_ix.empty:
            st.plotly_chart(px.line(global_ix.sort_values("date"), x="date", y="indice", color="site", markers=True,
                                    title="Indice global (base 100)"), use_container_width=True)
            variation = global_ix.sort_values("date").groupby("site").tail(1)
            if "variation_jour_pct" in variation:
                st.dataframe(variation[["date", "site", "indice", "variation_jour_pct"]], hide_index=True, use_container_width=True)
        coicop = indices_filtres[indices_filtres["niveau"].astype(str).str.startswith("coicop_")]
        if not coicop.empty:
            coicop["serie"] = coicop["niveau"].astype(str) + " — " + colonne_ou(coicop, "code_niveau", "").astype(str)
            st.plotly_chart(px.line(coicop.sort_values("date"), x="date", y="indice", color="serie", line_dash="site", markers=True,
                                    title="Indices COICOP"), use_container_width=True)
            if "variation_jour_pct" in coicop:
                st.dataframe(coicop.sort_values("date").groupby(["site", "niveau", "code_niveau"], dropna=False).tail(1)
                             [["date", "site", "niveau", "code_niveau", "indice", "variation_jour_pct"]],
                             hide_index=True, use_container_width=True)
        if len(dates) == 1:
            st.caption("Une seule date est présente : les variations jour/jour ne sont pas calculables.")

with onglets[2]:
    st.subheader("Comparer les prix entre sites")
    if produit_compare is None:
        st.info("Aucun produit disponible avec les filtres courants.")
    else:
        comparaison = filtre[filtre["libelle_produit"].eq(produit_compare)]
        if comparaison.empty:
            st.info("Aucun prix pour le produit sélectionné dans la période et les sites retenus.")
        else:
            stats = comparaison.groupby("site", as_index=False)["prix"].agg(prix_moyen="mean", prix_median="median", observations="count")
            reference = stats["prix_median"].median()
            stats["ecart_pct"] = (stats["prix_median"] / reference - 1) * 100 if reference else np.nan
            st.dataframe(stats, hide_index=True, use_container_width=True)
            st.plotly_chart(px.box(comparaison, x="site", y="prix", points="all", title=f"Distribution : {produit_compare}"), use_container_width=True)
            st.caption("Écart (%) de chaque médiane de site par rapport à la médiane des médianes affichées.")

with onglets[3]:
    st.subheader("Plus fortes hausses et baisses")
    if indices_filtres.empty or "variation_jour_pct" not in indices_filtres:
        st.info("Le fichier d'indices ne contient pas de variations journalières exploitables.")
    else:
        vv = indices_filtres[indices_filtres["niveau"].astype(str).eq("variete")].dropna(subset=["variation_jour_pct"]).copy()
        if vv.empty:
            st.info("Pas de variation calculable (notamment si une seule date est présente).")
        else:
            dernier = vv.sort_values("date").groupby(["site", "code_variete"], dropna=False).tail(1)
            gauche, droite = st.columns(2)
            colonnes = [c for c in ["site", "code_variete", "variation_jour_pct"] if c in dernier]
            gauche.markdown("**Baisses les plus fortes**")
            gauche.dataframe(dernier.nsmallest(10, "variation_jour_pct")[colonnes], hide_index=True, use_container_width=True)
            droite.markdown("**Hausses les plus fortes**")
            droite.dataframe(dernier.nlargest(10, "variation_jour_pct")[colonnes], hide_index=True, use_container_width=True)
            dernier["contribution_approx_pct"] = dernier["variation_jour_pct"]
            st.plotly_chart(px.bar(dernier.sort_values("contribution_approx_pct"), x="code_variete", y="contribution_approx_pct",
                                   color="site", title="Contributions approchées — variation des indices variété"), use_container_width=True)
            st.caption("Contribution approchée, non officielle : variation des indices de variété, sans calcul d'effet budgétaire.")

with onglets[4]:
    st.subheader("Promotions observées")
    promos = filtre.copy()
    promos["prix_promo"] = colonne_ou(promos, "prix_promo", False).astype(str).str.lower().isin(["true", "1", "oui"])
    promos["remise_pct"] = pd.to_numeric(colonne_ou(promos, "remise_pct"), errors="coerce")
    resume = promos.groupby("site", as_index=False).agg(observations=("prix", "size"), promotions=("prix_promo", "sum"), remise_moyenne_pct=("remise_pct", "mean"))
    if not resume.empty:
        resume["part_promo_pct"] = 100 * resume["promotions"] / resume["observations"].replace(0, np.nan)
        st.dataframe(resume, hide_index=True, use_container_width=True)
        st.dataframe(promos[promos["prix_promo"]], hide_index=True, use_container_width=True)
    else:
        st.info("Aucune observation promotionnelle dans la sélection.")

with onglets[5]:
    st.subheader("Qualité du rapprochement")
    apparie = colonne_ou(filtre, "apparie", False).astype(str).str.lower().isin(["true", "1", "oui"])
    qualite = filtre.assign(_apparie=apparie).groupby("site", as_index=False).agg(observations=("prix", "size"), appariees=("_apparie", "sum"))
    if not qualite.empty:
        qualite["score_rapprochement_pct"] = 100 * qualite["appariees"] / qualite["observations"].replace(0, np.nan)
        st.plotly_chart(px.bar(qualite, x="site", y="score_rapprochement_pct", title="Score de rapprochement"), use_container_width=True)
        st.dataframe(qualite, hide_index=True, use_container_width=True)
    st.subheader("Disponibilité des produits")
    dispo = filtre.groupby([filtre["date"].dt.date, "site"], as_index=False).agg(produits_disponibles=("libelle_produit", "nunique"))
    if not dispo.empty:
        st.plotly_chart(px.line(dispo, x="date", y="produits_disponibles", color="site", markers=True), use_container_width=True)
    else:
        st.info("Aucune donnée de disponibilité à afficher.")

with onglets[6]:
    st.subheader("Tableau filtré et téléchargement")
    st.dataframe(filtre, hide_index=True, use_container_width=True)
    st.download_button("Télécharger les données filtrées (CSV)", filtre.to_csv(index=False).encode("utf-8-sig"),
                       file_name="prix_filtres.csv", mime="text/csv")
