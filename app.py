# -*- coding: utf-8 -*-
"""Tableau de bord exploratoire de suivi des prix et indices quotidiens IHPC."""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Palette ANSTAT centralisée pour garder une identité cohérente.
CHARTE = {
    "orange": "#F39323", "vert": "#49655A", "orange_fonce": "#EF7911",
    "orange_ambre": "#F6A000", "jaune": "#FCBF00", "jaune_clair": "#FAEA26",
    "vert_fonce": "#0C6B23", "vert_turquoise": "#0A966F", "vert_vif": "#13A538",
    "vert_clair": "#8CC048", "noir": "#1D1D1B", "gris_fonce": "#555454",
    "gris": "#9F9F9F", "gris_clair": "#CCCCCC", "fond": "#FAFAF7",
}
PALETTE_ANSTAT = [CHARTE[k] for k in ("orange", "vert", "vert_turquoise", "orange_ambre", "vert_clair", "vert_fonce", "orange_fonce", "gris_fonce", "jaune", "gris")]

DOSSIER = Path(__file__).resolve().parent
DOSSIER_DATA = DOSSIER / "data"
FICHIER_PRIX = "prix_nettoyes_rapproches.csv"
FICHIER_INDICES = "indices_quotidiens.csv"

st.set_page_config(page_title="IHPC | Veille des prix", page_icon="📊", layout="wide")

# CSS autonome : l’application reste habillée même si config.toml n’est pas livré.
# Le chevron filigrane est inline; aucune image externe n’est téléchargée.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700;800&display=swap');
:root { --anstat-orange:#F39323; --anstat-green:#49655A; --anstat-ink:#1D1D1B; }
html, body, [class*="css"] { font-family:'Inter',sans-serif; color:var(--anstat-ink); }
h1,h2,h3,h4 { font-family:'Poppins',sans-serif !important; color:var(--anstat-green) !important; }
[data-testid="stAppViewContainer"] { background-color:#FAFAF7; background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='700' height='700' viewBox='0 0 700 700'%3E%3Cpath d='M110 590 350 110 590 590 500 590 350 290 200 590Z' fill='%23000000' fill-opacity='.035'/%3E%3C/svg%3E"); background-repeat:no-repeat; background-position:right 80px top 180px; background-size:min(54vw,700px); }
[data-testid="stHeader"] { background:rgba(250,250,247,.92); }
[data-testid="stSidebar"] { background:#49655A; }
[data-testid="stSidebar"] * { color:#fff !important; }
[data-testid="stSidebar"] [data-baseweb="tag"] { background:#F39323 !important; }
[data-testid="stSidebar"] input, [data-testid="stSidebar"] [data-baseweb="select"] > div { color:#1D1D1B !important; background:#fff !important; }
[data-testid="stSidebar"] [data-baseweb="select"] span { color:#1D1D1B !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color:#fff; }
div[data-testid="stMetric"] { background:rgba(255,255,255,.96); border:1px solid #e6e9e6; border-left:5px solid #F39323; border-radius:12px; padding:16px 18px; box-shadow:0 4px 16px rgba(29,29,27,.07); }
div[data-testid="stMetricLabel"] { color:#555454; font-weight:600; }
div[data-testid="stMetricValue"] { color:#49655A; font-family:'Poppins',sans-serif; }
.stTabs [data-baseweb="tab-list"] { gap:4px; border-bottom:1px solid #dce2dd; }
.stTabs [data-baseweb="tab"] { color:#49655A; font-weight:600; padding:12px 14px; }
.stTabs [aria-selected="true"] { color:#49655A !important; border-bottom:3px solid #F39323 !important; }
.stButton > button, [data-testid="stDownloadButton"] button { background:#F39323; color:#1D1D1B; border:0; border-radius:8px; font-weight:700; }
.stButton > button:hover, [data-testid="stDownloadButton"] button:hover { background:#EF7911; color:#1D1D1B; }
[data-testid="stDataFrame"] { border:1px solid #dce2dd; border-radius:10px; overflow:hidden; }
.anstat-header { display:flex; align-items:center; gap:22px; padding:18px 24px; margin:4px 0 24px; background:#fff; border:1px solid #e6e9e6; border-radius:16px; box-shadow:0 5px 22px rgba(29,29,27,.06); }
.anstat-brand { min-width:205px; line-height:1.05; }
.anstat-brand .word { font:800 35px 'Poppins',sans-serif; color:#49655A; letter-spacing:-1.8px; }
.anstat-brand .a { color:#F39323; }
.anstat-brand small { display:block; margin-top:5px; color:#555454; font:600 9px 'Inter',sans-serif; letter-spacing:.7px; }
.anstat-title { border-left:1px solid #e5e8e5; padding-left:22px; }
.anstat-title h1 { margin:0 !important; font-size:1.78rem !important; }
.anstat-title h1:after { content:''; display:block; width:72px; height:4px; margin-top:11px; border-radius:5px; background:#F39323; }
.anstat-title p { margin:.55rem 0 0; color:#555454; font-size:.96rem; }
.anstat-version { display:inline-block; margin-top:8px; padding:4px 9px; border-radius:999px; background:#F39323; color:#1D1D1B !important; font-size:.75rem; font-weight:700; letter-spacing:.02em; }
.anstat-footer { margin-top:36px; padding:18px 8px 8px; border-top:2px solid #F39323; color:#555454; font-size:.84rem; }
@media(max-width:700px) { .anstat-header{align-items:flex-start;flex-direction:column;gap:12px}.anstat-title{border-left:0;padding-left:0}.anstat-brand{min-width:0} }
</style>
""", unsafe_allow_html=True)

# Plotly reçoit le même style dans tous les onglets; les règles de calcul restent inchangées.
import plotly.io as pio
pio.templates["anstat"] = pio.templates["plotly_white"]
pio.templates["anstat"].layout.update(
    colorway=PALETTE_ANSTAT, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font={"family":"Inter, sans-serif", "color":CHARTE["noir"]},
    title={"font":{"family":"Poppins, sans-serif", "color":CHARTE["vert"]}},
    xaxis={"gridcolor":CHARTE["gris_clair"], "zerolinecolor":CHARTE["gris_clair"]},
    yaxis={"gridcolor":CHARTE["gris_clair"], "zerolinecolor":CHARTE["gris_clair"]},
)
px.defaults.template = "anstat"
px.defaults.color_discrete_map = {"ivoirshop":CHARTE["orange"], "IvoirShop":CHARTE["orange"], "adjovan":CHARTE["vert"], "Adjovan":CHARTE["vert"], "Tous sites":CHARTE["gris_fonce"]}

# Bandeau de marque : si aucun logo institutionnel n’est présent, texte stylisé sans erreur.
logo = DOSSIER / "assets" / "logo_anstat.png"
if logo.exists():
    import base64
    _logo_data = base64.b64encode(logo.read_bytes()).decode("ascii")
    _marque = f'<img src="data:image/png;base64,{_logo_data}" alt="Anstat — Agence Nationale de la Statistique" style="max-width:190px;max-height:72px;object-fit:contain">'
else:
    _marque = '<div class="anstat-brand"><div class="word"><span class="a">A</span>nstat</div><small>AGENCE NATIONALE DE LA STATISTIQUE</small></div>'

DOSSIER


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

# Date de collecte affichée à partir du champ déjà présent dans le CSV.
_date_derniere_collecte = prix["date"].max()
_date_affichee = _date_derniere_collecte.strftime("%d/%m/%Y") if pd.notna(_date_derniere_collecte) else "non renseignée"
st.markdown(
    f'<section class="anstat-header">{_marque}<div class="anstat-title">'
    f'<h1>Tableau de bord IHPC — Veille des prix en ligne</h1>'
    f'<p>Sources IvoirShop / Adjovan · Dernière collecte : {_date_affichee}</p></div></section>',
    unsafe_allow_html=True,
)

indices = charger_csv(FICHIER_INDICES)
if not indices.empty and {"date", "indice", "niveau", "site"}.issubset(indices.columns):
    indices["date"] = pd.to_datetime(indices["date"], errors="coerce")
    indices["indice"] = pd.to_numeric(indices["indice"], errors="coerce")
    if "variation_jour_pct" in indices:
        indices["variation_jour_pct"] = pd.to_numeric(indices["variation_jour_pct"], errors="coerce")
else:
    indices = calculer_indices(prix)
    st.sidebar.info("Indice quotidien recalculé à base fixe : CSV d'indices absent ou incomplet.")
# Le calcul local renvoie des dates texte ; on les convertit comme celles du CSV d’indices.
if not indices.empty:
    indices["date"] = pd.to_datetime(indices["date"], errors="coerce")
    indices["indice"] = pd.to_numeric(indices["indice"], errors="coerce")
    if "variation_jour_pct" in indices:
        indices["variation_jour_pct"] = pd.to_numeric(indices["variation_jour_pct"], errors="coerce")

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
    st.markdown('<div class="anstat-version">v3 – charte Anstat</div>', unsafe_allow_html=True)

filtre = prix[prix["site"].isin(sites_selectionnes) & prix["categorie"].isin(categories_selectionnees)].copy()
filtre = filtre[filtre["date"].dt.date.between(debut, fin)]
# Les indices par défaut proviennent du CSV exporté. Si une catégorie est écartée,
# on les recalcule sur toutes les dates de la sélection (avant le filtre temporel),
# afin de garder une base fixe et de faire suivre le filtre de catégorie.
if len(categories_selectionnees) < len(categories):
    source_indices = prix[prix["site"].isin(sites_selectionnes)
                          & prix["categorie"].isin(categories_selectionnees)].copy()
    indices = calculer_indices(source_indices)
indices_filtres = indices.copy()
if not indices_filtres.empty:
    indices_filtres = indices_filtres[indices_filtres["date"].dt.date.between(debut, fin)]
    indices_filtres = indices_filtres[indices_filtres["site"].isin(sites_selectionnes + ["Tous sites"])]

onglets = st.tabs(["Synthèse", "Indices", "Comparaison des sites", "Hausses/Baisses et contributions",
                   "Promotions", "Volatilité & distributions", "Qualité des données", "Données"])

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
            st.plotly_chart(px.line(coicop.sort_values("date"), x="date", y="indice", color="site", line_dash="serie", markers=True,
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
                                   color="site", title="Contributions approchées — variation des indices variété", color_discrete_map={"ivoirshop":CHARTE["orange"], "adjovan":CHARTE["vert"]}), use_container_width=True)
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
    st.subheader("Volatilité et distribution des variations")
    # On mesure les changements entre deux relevés successifs du même produit et du même site.
    # Les intervalles peuvent être irréguliers : il ne s’agit donc pas d’une volatilité annualisée.
    historique = filtre.sort_values("date").copy()
    historique["variation_prix_pct"] = historique.groupby(["site", "cle_produit"], dropna=False)["prix"].pct_change() * 100
    variations = historique.dropna(subset=["variation_prix_pct"]).copy()
    if variations.empty:
        st.info("Il faut au moins deux observations datées d'un même produit et site pour mesurer les variations.")
    else:
        # Résume la forme de la distribution sans supprimer les valeurs extrêmes du tableau.
        part_stable = float(variations["variation_prix_pct"].abs().lt(0.1).mean())
        part_baisse = float(variations["variation_prix_pct"].lt(-0.1).mean())
        part_hausse = float(variations["variation_prix_pct"].gt(0.1).mean())
        med_var = float(variations["variation_prix_pct"].median())
        st.info(f"Sur les variations observées : {part_stable:.0%} sont quasi stables (±0,1 %), "
                f"{part_baisse:.0%} sont en baisse et {part_hausse:.0%} en hausse. "
                f"La variation médiane est de {med_var:+.2f} %. Ces constats sont descriptifs, sans extrapolation.")

        # Le graphique limite l’axe aux 1er et 99e percentiles pour rendre le cœur visible.
        # Les observations complètes restent consultables dans le tableau plus bas.
        borne_basse, borne_haute = variations["variation_prix_pct"].quantile([0.01, 0.99])
        centre = variations[variations["variation_prix_pct"].between(borne_basse, borne_haute)].copy()
        if not centre.empty:
            st.plotly_chart(px.histogram(centre, x="variation_prix_pct", color="site", nbins=40,
                                         title="Distribution des variations successives de prix (%)",
                                         labels={"variation_prix_pct": "Variation entre relevés (%)"}),
                            use_container_width=True)
            st.caption("L’histogramme masque uniquement les 1 % les plus bas et les 1 % les plus hauts pour la lisibilité; les données brutes restent conservées.")

        resume_vol = variations.groupby(["site", "categorie"], dropna=False).agg(
            observations=("variation_prix_pct", "size"),
            variation_mediane_pct=("variation_prix_pct", "median"),
            dispersion_iqr_pct=("variation_prix_pct", lambda x: x.quantile(0.75) - x.quantile(0.25)),
            variation_absolue_mediane_pct=("variation_prix_pct", lambda x: x.abs().median())
        ).reset_index()
        # L’IQR décrit l’écart des 50 % centraux et résiste mieux aux extrêmes que l’écart-type.
        st.markdown("**Dispersion robuste par site et catégorie**")
        st.dataframe(resume_vol.sort_values("dispersion_iqr_pct", ascending=False), hide_index=True, use_container_width=True)
        st.markdown("**Variations observées les plus fortes**")
        st.dataframe(variations.reindex(variations["variation_prix_pct"].abs().sort_values(ascending=False).index)
                     [["date", "site", "categorie", "libelle_produit", "variation_prix_pct"]].head(20),
                     hide_index=True, use_container_width=True)

with onglets[6]:
    st.subheader("Qualité du rapprochement")
    apparie = colonne_ou(filtre, "apparie", False).astype(str).str.lower().isin(["true", "1", "oui"])
    qualite = filtre.assign(_apparie=apparie).groupby("site", as_index=False).agg(observations=("prix", "size"), appariees=("_apparie", "sum"))
    if not qualite.empty:
        qualite["score_rapprochement_pct"] = 100 * qualite["appariees"] / qualite["observations"].replace(0, np.nan)
        st.plotly_chart(px.bar(qualite, x="site", y="score_rapprochement_pct", color="site", title="Score de rapprochement"), use_container_width=True)
        st.dataframe(qualite, hide_index=True, use_container_width=True)
    st.subheader("Disponibilité des produits")
    disponibilite = filtre.assign(jour=filtre["date"].dt.date)
    dispo = disponibilite.groupby(["jour", "site"], as_index=False).agg(produits_disponibles=("libelle_produit", "nunique"))
    if not dispo.empty:
        st.plotly_chart(px.line(dispo, x="jour", y="produits_disponibles", color="site", markers=True), use_container_width=True)
    else:
        st.info("Aucune donnée de disponibilité à afficher.")

with onglets[7]:
    st.subheader("Tableau filtré et téléchargement")
    st.dataframe(filtre, hide_index=True, use_container_width=True)
    st.download_button("Télécharger les données filtrées (CSV)", filtre.to_csv(index=False).encode("utf-8-sig"),
                       file_name="prix_filtres.csv", mime="text/csv")


# Pied de page institutionnel et rappel exploratoire, sans modifier les indicateurs.
st.markdown("""
<div class="anstat-footer"><span class="anstat-version">v3 – charte Anstat</span><br><strong>ANSTAT — Agence Nationale de la Statistique</strong> · Prototype exploratoire<br>
Les indices et constats présentés sont descriptifs et exploratoires; ils ne constituent pas une publication officielle. Les variations dépendent des produits appariés, de la période et des filtres sélectionnés. Les prix extrêmes et observations manquantes ne sont pas imputés/supprimés par le dashboard.</div>
""", unsafe_allow_html=True)
