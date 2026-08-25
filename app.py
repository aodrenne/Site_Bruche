import base64
import math
from pathlib import Path
import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st
import unicodedata
 
st.set_page_config(page_title="Maquette", layout="wide", initial_sidebar_state="expanded")
 
MAP_CENTER = {"lat": 48.450509, "lon": 7.197954}
MAP_ZOOM = 10.3
MAP_ZOOM_Com = 13
Shapefile = Path(__file__).parent / "Shapefile"
 
COULEURS_typo = {
    "Par défaut": [128, 128, 128, 200], 
    "Acceuil": [255, 209, 168, 200], 
    "Cimetiere": [214, 214, 214, 200], 
    "Culture": [179, 146, 214, 200],  
    "Gare": [100, 100, 100, 200],  
    "Habitation": [240, 211, 96, 200],  
    "Industrie": [179, 233, 255, 200],  
    "Public": [182, 204, 188, 200],  
    "Religieux": [214, 125, 114, 200],  
}
 
PALETTE_BASE = ["#F8EACD", "#F0D4A2", "#E0B366", "#C09447", "#967841", "#8A7154", "#665637", "#4F432F"]
 
 
BASEMAPS = {
    "Clair (Positron)": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    "Sombre (Dark Matter)": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    "Couleur (Voyager)": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
    "Satellite (Esri)": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"
}
 


def get_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()
 
 
def _rgba_css(rgb):
    """Convertit une couleur [r, g, b, a(0-255)] en chaîne CSS rgba() pour Plotly."""
    r, g, b, a = rgb
    return f"rgba({r},{g},{b},{a / 255:.2f})"
 
 
VALEURS_INVALIDES = ["nan", "none", "n/a", "na", "-", "", "nan||nan", "none||none"]
 
 
def _colonne_texte(df, col):
    if col in df.columns:
        serie = df[col]
        return serie.astype(str).str.strip().mask(serie.isna(), "")
    return pd.Series("", index=df.index)
 
def _est_valide(serie):
    return ~serie.str.lower().isin(VALEURS_INVALIDES)
 
 
# --------------------- Chargement des données ----------------------------------------------------#
#reprojection 4326#
def _to_wgs84(gdf):
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        return gdf.to_crs(epsg=4326)
    return gdf
 
 
def _est_url(source):
    """Détecte si 'source' est une URL http(s) plutôt qu'un nom de fichier local."""
    return str(source).startswith("http://") or str(source).startswith("https://")
 
 
def _load_shapefile(filename, encoding):
    source = filename if _est_url(filename) else (Shapefile / filename)
    gdf = gpd.read_file(source, encoding=encoding)
    return _to_wgs84(gdf)
 
 
@st.cache_data
def load_communes():
    gdf = _load_shapefile("https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/Shapefile/Commune_VB_3.gpkg", "utf-8")
    df_communes = pd.read_csv("https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/Shapefile/Informations_communes_2.csv", encoding="utf-8", sep=";")
    df_communes["BLASON"] = df_communes["BLASON"].astype(str).str.strip()
    gdf = gdf.merge(df_communes[["NOM", "BLASON"]], on="NOM", how="left")
    return gdf
 
 
@st.cache_data
def load_points():
    gdf = _load_shapefile("https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/Shapefile/Points_avec_info_13.gpkg", "cp1252")
    gdf["lon"] = gdf.geometry.centroid.x
    gdf["lat"] = gdf.geometry.centroid.y
 

    df_textes = pd.read_csv("https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/Shapefile/Informations_pts_14.csv", encoding="cp1252", sep=";")
    df_textes["Photo"] = df_textes["Photo"].astype(str).str.strip()
    candidates = ["Histoire", "Datation", "typo_g2", "Photo", "Siecle_1", "Deno"]
    colonnes_du_csv = [c for c in candidates if c in df_textes.columns and c not in gdf.columns]
    colonnes_a_fusionner = ["REF"] + colonnes_du_csv
    gdf = gdf.merge(df_textes[colonnes_a_fusionner], on="REF", how="left")
 
    if "Photo" in gdf.columns:
        gdf["Photo"] = gdf["Photo"].astype(str).str.strip()
 
    def attribuer_couleur(val):
        return COULEURS_typo.get(str(val).strip(), COULEURS_typo["Par défaut"])
 
    gdf["couleur_rgb"] = gdf.get("groupe_1", pd.Series(["Par défaut"] * len(gdf))).apply(attribuer_couleur)
    return gdf
 
 
@st.cache_data
def load_topo():
    return _load_shapefile("https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/Shapefile/topo.gpkg", "utf-8")
 
 
@st.cache_data
def load_eau():
    return _load_shapefile("https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/Shapefile/cours_eau.gpkg", "cp1252")
 
 
@st.cache_data
def load_voirie():
    return _load_shapefile("https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/Shapefile/voirie.gpkg", "utf-8")
 
 
topo_gdf = load_topo()
communes_gdf = load_communes()
voirie_gdf = load_voirie()
eau_gdf = load_eau()
points_gdf = load_points()
 
if "basemap_select" not in st.session_state:
    st.session_state["basemap_select"] = list(BASEMAPS.keys())[0]

 
# --------- Sidebar gauche -------------------#
with st.sidebar:
 
    st.markdown("### Filtrage des communes")
 
    comptage_full = (
        points_gdf["Informat_4"]
        .dropna()
        .value_counts()
        .reset_index()
        .rename(columns={"Informat_4": "commune", "count": "nb"})
        .sort_values("nb", ascending=False)
        .reset_index(drop=True)
    )
 
    selected_communes = st.multiselect(
        "Sélection de la commune :",
        options=comptage_full["commune"].tolist(),
        default=st.session_state.get("commune_selectionnee", []),
    )
    if selected_communes != st.session_state.get("commune_selectionnee", []):
        st.session_state["commune_selectionnee"] = selected_communes
        st.session_state["sel_source"] = "sidebar"
        st.rerun()

 
    # ----- Partie 1 : Filtrage par typologie -----------------
    st.write("---")
    st.markdown("### Filtrage par typo")
    with st.expander("Sélectionner une typologie...", expanded=False):
 
        df_arbre_typo = pd.DataFrame(index=points_gdf.index)
        for col in ["groupe_1", "groupe_2", "groupe_3"]:
            df_arbre_typo[col] = _colonne_texte(points_gdf, col)
 
        if "selected_g1" not in st.session_state:
            st.session_state["selected_g1"] = set()
        if "selected_g2" not in st.session_state:
            st.session_state["selected_g2"] = set()
        if "selected_g3" not in st.session_state:
            st.session_state["selected_g3"] = set()
 
        tous_g1_valides = set(df_arbre_typo.loc[_est_valide(df_arbre_typo["groupe_1"]), "groupe_1"])
 
        df_g2_valides_all = df_arbre_typo[
            _est_valide(df_arbre_typo["groupe_1"]) & _est_valide(df_arbre_typo["groupe_2"])
        ].drop_duplicates(["groupe_1", "groupe_2"])
        tous_g2_valides = {f"{r['groupe_1']}||{r['groupe_2']}" for _, r in df_g2_valides_all.iterrows()}
 
        df_g3_valides_all = df_arbre_typo[
            _est_valide(df_arbre_typo["groupe_1"])
            & _est_valide(df_arbre_typo["groupe_2"])
            & _est_valide(df_arbre_typo["groupe_3"])
        ].drop_duplicates(["groupe_1", "groupe_2", "groupe_3"])
        tous_g3_valides = {f"{r['groupe_1']}||{r['groupe_2']}||{r['groupe_3']}" for _, r in df_g3_valides_all.iterrows()}
 
        typo_tout_coche = (
            tous_g1_valides.issubset(st.session_state["selected_g1"])
            and tous_g2_valides.issubset(st.session_state["selected_g2"])
            and tous_g3_valides.issubset(st.session_state["selected_g3"])
        )
        label_global_typo = "Tout décocher (Typo)" if typo_tout_coche else "Tout cocher (Typo)"
 
        if st.button(label_global_typo, use_container_width=True, key="btn_typo_global"):
            if typo_tout_coche:
                st.session_state["selected_g1"].clear()
                st.session_state["selected_g2"].clear()
                st.session_state["selected_g3"].clear()
            else:
                st.session_state["selected_g1"] = set(tous_g1_valides)
                st.session_state["selected_g2"] = set(tous_g2_valides)
                st.session_state["selected_g3"] = set(tous_g3_valides)
            st.rerun()
 
        st.write(" ")
 
 
        df_g1_valides = df_arbre_typo[_est_valide(df_arbre_typo["groupe_1"])]
        g1_uniques = sorted(df_g1_valides["groupe_1"].unique().tolist(), key=lambda x: str(x))
 
        for g1 in g1_uniques:
            df_g1 = df_g1_valides[df_g1_valides["groupe_1"] == g1]
            df_g1_g2_valides = df_g1[_est_valide(df_g1["groupe_2"])]
            df_g1_g3_valides = df_g1_g2_valides[_est_valide(df_g1_g2_valides["groupe_3"])]
 
            tous_g2_attendus = {f"{g1}||{x}" for x in df_g1_g2_valides["groupe_2"].unique()}
            tous_g3_attendus = {
                f"{g1}||{row['groupe_2']}||{row['groupe_3']}" for _, row in df_g1_g3_valides.iterrows()
            }
 
            if tous_g2_attendus or tous_g3_attendus:
                if tous_g2_attendus.issubset(st.session_state["selected_g2"]) and tous_g3_attendus.issubset(
                    st.session_state["selected_g3"]
                ):
                    st.session_state["selected_g1"].add(g1)
                else:
                    st.session_state["selected_g1"].discard(g1)
 
            is_g1_selected = g1 in st.session_state["selected_g1"]
            icon_g1 = "☑" if is_g1_selected else "☐"
 
            with st.expander(f"{icon_g1} {g1}", expanded=False):
                label_g1_btn = "Tout désélectionner" if is_g1_selected else "Tout sélectionner"
                if st.button(label_g1_btn, key=f"btn_g1_{g1}", use_container_width=True):
                    if is_g1_selected:
                        st.session_state["selected_g1"].remove(g1)
                        for _, row in df_g1_g2_valides.iterrows():
                            st.session_state["selected_g2"].discard(f"{g1}||{row['groupe_2']}")
                        for _, row in df_g1_g3_valides.iterrows():
                            st.session_state["selected_g3"].discard(f"{g1}||{row['groupe_2']}||{row['groupe_3']}")
                    else:
                        st.session_state["selected_g1"].add(g1)
                        for _, row in df_g1_g2_valides.iterrows():
                            st.session_state["selected_g2"].add(f"{g1}||{row['groupe_2']}")
                        for _, row in df_g1_g3_valides.iterrows():
                            st.session_state["selected_g3"].add(f"{g1}||{row['groupe_2']}||{row['groupe_3']}")
                    st.rerun()
 
 
 
                g2_uniques = sorted(df_g1_g2_valides["groupe_2"].unique().tolist(), key=lambda x: str(x))
                for g2 in g2_uniques:
                    df_g2 = df_g1_g2_valides[df_g1_g2_valides["groupe_2"] == g2]
                    df_g2_g3_valides = df_g2[_est_valide(df_g2["groupe_3"])]
                    g2_id = f"{g1}||{g2}"
                    tous_g3_du_g2 = {f"{g1}||{g2}||{x}" for x in df_g2_g3_valides["groupe_3"].unique()}
 
                    if tous_g3_du_g2:
                        if tous_g3_du_g2.issubset(st.session_state["selected_g3"]):
                            st.session_state["selected_g2"].add(g2_id)
                        else:
                            st.session_state["selected_g2"].discard(g2_id)
 
 
                    is_g2_selected = g2_id in st.session_state["selected_g2"]
                    icon_g2 = "☑" if is_g2_selected else "☐"
 
                    with st.expander(f"&nbsp;&nbsp;&nbsp;&nbsp;{icon_g2} {g2}", expanded=False):
                        label_g2_btn = "Tout déselectionner" if is_g2_selected else "Tout sélectionner"
                        if st.button(label_g2_btn, key=f"btn_g2_{g1}_{g2}", use_container_width=True):
                            if is_g2_selected:
                                st.session_state["selected_g2"].remove(g2_id)
                                for _, row in df_g2_g3_valides.iterrows():
                                    st.session_state["selected_g3"].discard(f"{g1}||{g2}||{row['groupe_3']}")
                            else:
                                st.session_state["selected_g2"].add(g2_id)
                                for _, row in df_g2_g3_valides.iterrows():
                                    st.session_state["selected_g3"].add(f"{g1}||{g2}||{row['groupe_3']}")
                            st.rerun()
 
 
                        g3_uniques = sorted(df_g2_g3_valides["groupe_3"].unique().tolist(), key=lambda x: str(x))
                        for g3 in g3_uniques:
                            g3_id = f"{g1}||{g2}||{g3}"
                            is_g3_selected = g3_id in st.session_state["selected_g3"]
                            icon_g3 = "☑" if is_g3_selected else "☐"
 
                            if st.button(
                                f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{icon_g3} {g3}",
                                key=f"btn_g3_{g1}_{g2}_{g3}",
                                use_container_width=True,
                            ):
                                if is_g3_selected:
                                    st.session_state["selected_g3"].remove(g3_id)
                                else:
                                    st.session_state["selected_g3"].add(g3_id)
                                st.rerun()

 
    # ----- Partie 2 : Datation --------------------------------#
    st.write("---")
    st.markdown("### Filtrage par Datation")
    with st.expander("Sélectionner la période...", expanded=False):
 
        df_arbre_chrono = pd.DataFrame(index=points_gdf.index)
        for col in ["Siecle_1", "Datation"]:
            df_arbre_chrono[col] = _colonne_texte(points_gdf, col)
 
        if "selected_s1" not in st.session_state:
            st.session_state["selected_s1"] = set()
        if "selected_s2" not in st.session_state:
            st.session_state["selected_s2"] = set()
 
 
        tous_s1_valides = set(df_arbre_chrono.loc[_est_valide(df_arbre_chrono["Siecle_1"]), "Siecle_1"])
        df_s2_valides_all = df_arbre_chrono[
            _est_valide(df_arbre_chrono["Siecle_1"]) & _est_valide(df_arbre_chrono["Datation"])
        ].drop_duplicates(["Siecle_1", "Datation"])
        tous_s2_valides = {f"{r['Siecle_1']}||{r['Datation']}" for _, r in df_s2_valides_all.iterrows()}
 
        chrono_tout_coche = tous_s1_valides.issubset(st.session_state["selected_s1"]) and tous_s2_valides.issubset(
            st.session_state["selected_s2"]
        )
        label_global_chrono = "Tout décocher (Chrono)" if chrono_tout_coche else "Tout cocher (Chrono)"
 
        if st.button(label_global_chrono, use_container_width=True, key="btn_chrono_global"):
            if chrono_tout_coche:
                st.session_state["selected_s1"].clear()
                st.session_state["selected_s2"].clear()
            else:
                st.session_state["selected_s1"] = set(tous_s1_valides)
                st.session_state["selected_s2"] = set(tous_s2_valides)
            st.rerun()
 
        st.write(" ")
 
 
        df_s1_valides = df_arbre_chrono[_est_valide(df_arbre_chrono["Siecle_1"])]
        s1_uniques = sorted(df_s1_valides["Siecle_1"].unique().tolist(), key=lambda x: str(x))
 
        for s1 in s1_uniques:
            df_s1 = df_s1_valides[df_s1_valides["Siecle_1"] == s1]
            df_s1_s2_valides = df_s1[_est_valide(df_s1["Datation"])]
            tous_s2_attendus = {f"{s1}||{x}" for x in df_s1_s2_valides["Datation"].unique()}
 
            if tous_s2_attendus:
                if tous_s2_attendus.issubset(st.session_state["selected_s2"]):
                    st.session_state["selected_s1"].add(s1)
                else:
                    st.session_state["selected_s1"].discard(s1)
 
            is_s1_selected = s1 in st.session_state["selected_s1"]
            icon_s1 = "☑" if is_s1_selected else "☐"
 
            with st.expander(f"{icon_s1} {s1}", expanded=False):
                label_s1_btn = "Tout désélectionner" if is_s1_selected else "Tout sélectionner"
                if st.button(label_s1_btn, key=f"btn_s1_{s1}", use_container_width=True):
                    if is_s1_selected:
                        st.session_state["selected_s1"].remove(s1)
                        for _, row in df_s1_s2_valides.iterrows():
                            st.session_state["selected_s2"].discard(f"{s1}||{row['Datation']}")
                    else:
                        st.session_state["selected_s1"].add(s1)
                        for _, row in df_s1_s2_valides.iterrows():
                            st.session_state["selected_s2"].add(f"{s1}||{row['Datation']}")
                    st.rerun()
 
 
                s2_uniques = sorted(df_s1_s2_valides["Datation"].unique().tolist(), key=lambda x: str(x))
                for s2 in s2_uniques:
                    s2_id = f"{s1}||{s2}"
                    is_s2_selected = s2_id in st.session_state["selected_s2"]
                    icon_s2 = "☑" if is_s2_selected else "☐"
 
                    if st.button(
                        f"&nbsp;&nbsp;&nbsp;&nbsp;{icon_s2} {s2}", key=f"btn_s2_{s1}_{s2}", use_container_width=True
                    ):
                        if is_s2_selected:
                            st.session_state["selected_s2"].remove(s2_id)
                        else:
                            st.session_state["selected_s2"].add(s2_id)
                        st.rerun()
 

 
#-------Selections --------------------#
commune_sel = st.session_state.get("commune_selectionnee", [])
sel_source = st.session_state.get("sel_source", "sidebar")
 
sel_g1 = st.session_state.get("selected_g1", set())
sel_g2 = st.session_state.get("selected_g2", set())
sel_g3 = st.session_state.get("selected_g3", set())
sel_s1 = st.session_state.get("selected_s1", set())
sel_s2 = st.session_state.get("selected_s2", set())
 
 
points_filtres = points_gdf.copy()
 
# 1. Filtre Typologie
col_g1 = _colonne_texte(points_filtres, "groupe_1")
col_g2 = _colonne_texte(points_filtres, "groupe_2")
col_g3 = _colonne_texte(points_filtres, "groupe_3")
 
if sel_g1 or sel_g2 or sel_g3:
    masque_typo = pd.Series(False, index=points_filtres.index)
    if sel_g1:
        masque_typo = masque_typo | col_g1.isin(sel_g1)
    if sel_g2:
        g2_ids = col_g1 + "||" + col_g2
        masque_typo = masque_typo | g2_ids.isin(sel_g2)
    if sel_g3:
        g3_ids = col_g1 + "||" + col_g2 + "||" + col_g3
        masque_typo = masque_typo | g3_ids.isin(sel_g3)
    points_filtres = points_filtres[masque_typo]
 
 
col_s1 = _colonne_texte(points_filtres, "Siecle_1")
col_s2 = _colonne_texte(points_filtres, "Datation")
 
if sel_s1 or sel_s2:
    masque_chrono = pd.Series(False, index=points_filtres.index)
    if sel_s1:
        masque_chrono = masque_chrono | col_s1.isin(sel_s1)
    if sel_s2:
        s2_ids = col_s1 + "||" + col_s2
        masque_chrono = masque_chrono | s2_ids.isin(sel_s2)
    points_filtres = points_filtres[masque_chrono]
 
 
if commune_sel:
    points_filtres = points_filtres[points_filtres["Informat_4"].isin(commune_sel)]
 
 
comptage = (
    points_filtres["Informat_4"]
    .dropna()
    .value_counts()
    .reset_index()
    .rename(columns={"Informat_4": "commune", "count": "nb"})
    .sort_values("nb", ascending=False)
    .reset_index(drop=True)
)


 
#--------Comptage donut-------------------#
 
col_g1_disp = _colonne_texte(points_filtres, "groupe_1").rename("typo")
comptage_typo = (
    col_g1_disp[_est_valide(col_g1_disp)]
    .value_counts()
    .reset_index()
    .rename(columns={"count": "nb"})
    .sort_values("nb", ascending=False)
    .reset_index(drop=True)
)
total_typo = int(comptage_typo["nb"].sum())
 
col_s1_disp = _colonne_texte(points_filtres, "Siecle_1").rename("periode")
comptage_chrono = (
    col_s1_disp[_est_valide(col_s1_disp)]
    .value_counts()
    .reset_index()
    .rename(columns={"count": "nb"})
    .sort_values("nb", ascending=False)
    .reset_index(drop=True)
)
total_chrono = int(comptage_chrono["nb"].sum())
 

 
# --------------- Graph en barre ---------------------#
fig_bar = go.Figure(
    go.Bar(
        x=comptage["commune"],
        y=comptage["nb"],
        marker_color="#FFE4B0",
        hovertemplate="<b>%{x}</b><br>%{y} bâtiments<extra></extra>",
    )
)
 
fig_bar.update_layout(
    xaxis=dict(categoryorder="array", categoryarray=comptage["commune"].tolist()),
    margin=dict(t=10, b=10, l=10, r=10),
    height=300,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    clickmode="event+select",
)


 
# ---------------- Donuts ----------------------------#
 
# Donut 1 
couleurs_typo = [
    _rgba_css(COULEURS_typo.get(str(t).strip(), COULEURS_typo["Par défaut"]))
    for t in comptage_typo["typo"]
]
 
fig_donut_typo = go.Figure(
    go.Pie(
        labels=comptage_typo["typo"],
        values=comptage_typo["nb"],
        hole=0.55,
        marker=dict(colors=couleurs_typo, line=dict(color="#fff", width=2)),
        textinfo="percent",
        textfont=dict(size=11, family="Georgia, serif"),
        hovertemplate="<b>%{label}</b><br>%{value} bâtiments (%{percent})<extra></extra>",
    )
)
fig_donut_typo.update_layout(
    margin=dict(t=10, b=10, l=10, r=10),
    height=360,
    showlegend=True,
    legend=dict(orientation="h", yanchor="top", y=-0.15, font=dict(size=14)),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    annotations=[
        dict(
            text=f"<b>{total_typo}</b><br>bâtiments",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=13, color="#4D4630", family="Georgia, serif"),
            align="center",
        )
    ],
)
 
 
 
# Donut 2 
palette_chrono = [PALETTE_BASE[i % len(PALETTE_BASE)] for i in range(len(comptage_chrono))]
 
fig_donut_chrono = go.Figure(
    go.Pie(
        labels=comptage_chrono["periode"],
        values=comptage_chrono["nb"],
        hole=0.55,
        marker=dict(colors=palette_chrono, line=dict(color="#fff", width=2)),
        textinfo="percent",
        textfont=dict(size=11, family="Georgia, serif"),
        hovertemplate="<b>%{label}</b><br>%{value} bâtiments (%{percent})<extra></extra>",
    )
)
fig_donut_chrono.update_layout(
    margin=dict(t=10, b=10, l=10, r=10),
    height=350,
    showlegend=True,
    legend=dict(orientation="h", yanchor="top", y=-0.15, font=dict(size=14)),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    annotations=[
        dict(
            text=f"<b>{total_chrono}</b><br>bâtiments",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=13, color="#000000", family="Georgia, serif"),
            align="center",
        )
    ],
)
 
if commune_sel and sel_source in ["sidebar", "bar"] and len(commune_sel) == 1:
    gdf_sel = communes_gdf[communes_gdf["NOM"].isin(commune_sel)]
 
    if not gdf_sel.empty:
        # Sécurité : on force le calcul en WGS84 (degrés)
        if gdf_sel.crs is not None and gdf_sel.crs.to_epsg() != 4326:
            gdf_sel = gdf_sel.to_crs(epsg=4326)
 
        bounds = gdf_sel.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
 
        lat_span = bounds[3] - bounds[1]
        lon_span = bounds[2] - bounds[0]
        max_span = max(lat_span, lon_span)
 
        if max_span > 0:
            zoom = 12 - math.log2(max_span / 0.08)
            zoom = round(max(11.0, min(16.0, zoom)), 1)
        else:
            zoom = MAP_ZOOM_Com
 
        print(f"[DEBUG] commune={commune_sel} span={max_span:.5f} zoom={zoom}")
    else:
        center_lat, center_lon, zoom = MAP_CENTER["lat"], MAP_CENTER["lon"], MAP_ZOOM
else:
    center_lat, center_lon, zoom = MAP_CENTER["lat"], MAP_CENTER["lon"], MAP_ZOOM
 
 
# ------------ Couches gpkg---------------#
communes_layer = pdk.Layer(
    "GeoJsonLayer",
    data=communes_gdf.__geo_interface__,
    stroked=True,
    filled=True,
    get_fill_color=[255, 255, 255, 10],
    opacity=0.7,
    get_line_color=[0, 0, 0, 200],
    line_width_min_pixels=1.2,
    pickable=True,
    id="communes",
)
topo_layer = pdk.Layer(
    "GeoJsonLayer",
    data=topo_gdf.__geo_interface__,
    stroked=True,
    filled=False,
    get_line_color=[181, 181, 181, 100],
    line_width_min_pixels=1,
    opacity=0.3,
    id="topo",
)
voirie_layer = pdk.Layer(
    "GeoJsonLayer",
    data=voirie_gdf.__geo_interface__,
    stroked=True,
    filled=False,
    get_line_color=[176, 35, 35, 90],
    line_width_min_pixels=2,
    opacity=0.3,
    id="voirie",
)
eau_layer = pdk.Layer(
    "GeoJsonLayer",
    data=eau_gdf.__geo_interface__,
    stroked=True,
    filled=False,
    get_line_color=[27, 162, 207, 90],
    line_width_min_pixels=3,
    opacity=0.3,
    id="eau",
)
 
 
cols = ["lon", "lat", "groupe_3", "groupe_2", "groupe_1", "Histoire", "Datation", "typo_g2", "Photo", "couleur_rgb", "Deno"]
cols_existantes = [c for c in cols if c in points_filtres.columns]
 
points_layer = pdk.Layer(
    "ScatterplotLayer",
    data=points_filtres[cols_existantes].to_dict(orient="records"),
    get_position=["lon", "lat"],
    get_fill_color="couleur_rgb",
    get_radius=80,
    radius_min_pixels=5,
    radius_max_pixels=14,
    opacity=0.8,
    pickable=True,
    auto_highlight=True,
    id="points",
)
 
layers = [communes_layer, topo_layer, eau_layer, voirie_layer, points_layer]
 
if commune_sel:
    gdf_sel = communes_gdf[communes_gdf["NOM"].isin(commune_sel)]
    if not gdf_sel.empty:
        highlight_layer = pdk.Layer(
            "GeoJsonLayer",
            data=gdf_sel.__geo_interface__,
            stroked=True,
            filled=True,
            get_fill_color=[252, 212, 207, 50],
            get_line_color=[186, 124, 114, 200],
            line_width_min_pixels=4,
            id="highlight",
        )
        layers.insert(1, highlight_layer)
 
view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=zoom, pitch=0)
 
deck = pdk.Deck(
    layers=layers,
    initial_view_state=view_state,
    map_style=BASEMAPS.get(st.session_state.get("basemap_select"), BASEMAPS[list(BASEMAPS.keys())[0]]),
    tooltip=False,
)
 
 
# -------------------- Popup --------------#
@st.dialog(" ", width="small")
def show_point_popup(obj):
    photo = obj.get("Photo", "")
    if photo and str(photo).lower() != "nan":
        photo_name = str(photo).strip()
        
        # Lien direct vers le fichier dans ton repo Hugging Face
        photo_url = f"https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/{photo_name}"
        
        try:
            st.image(photo_url, use_container_width=True)
        except Exception:
            st.warning(f"Photo introuvable sur Hugging Face : {photo_name}")
    st.markdown(f"<h1 style='color:#751F0F; font-size:30px;'>{obj.get('Deno', '–')}</h1>", unsafe_allow_html=True)
    st.write(f"**Datation :** {obj.get('Datation', '–')}")
    st.write(f"**Historique :** {obj.get('Histoire', '–')}")
 
 
@st.dialog(" ")
def show_commune_popup(props):
    blason = str(props.get("BLASON", "")).strip()
    if blason and blason != "nan":
        # On garde le nom tel quel ou avec son extension selon ton CSV
        blason_name = blason if "." in blason else f"{blason}.png" # Ajuste selon l'extension de tes blasons (png ou jpg)
        
        # Lien direct vers le fichier sur ton repo Hugging Face
        blason_url = f"https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/blason/{blason_name}"
        
        # Streamlit gère directement les URLs dans st.markdown ou st.image !
        st.markdown(
            f"<div style='text-align:center;'><img src='{blason_url}' "
            f"style='width:100px; height:auto;'></div>",
            unsafe_allow_html=True,
        )
    else:
        st.warning(f"Blason introuvable : {blason}")
 
    st.markdown(f"<h1 style='color:#751F0F; font-size:30px;'>{props['NOM']}</h1>", unsafe_allow_html=True)
    st.write(f"**Nombre d'habitants :** {props['POPULATION']}")
    st.write(f"**Code postal :** {props['CODE_POST']}")
    st.write(f"**Nombre de bâtiments recensés :** {props['BATIMENT']}")
 
with st.container(key="basemap_select_container"):
    st.selectbox(
        " ",
        options=list(BASEMAPS.keys()),
        key="basemap_select",
    )
 
# -------------- CSS -------------------#
st.markdown(
    """
    <style>
        html, body { height: 100% !important; overflow: hidden !important; }
 
        header {visibility: hidden;}
        footer {visibility: hidden;}
 
        [data-testid="stAppViewContainer"] {
            padding: 0 !important;
            height: 100vh !important;
            overflow: hidden !important;
        }
        [data-testid="stMain"] {
            padding: 0 !important;
            height: 100% !important;
            overflow: hidden !important;
        }
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
            height: 100% !important;
            overflow: hidden !important;
        }
 
        [data-testid="stHorizontalBlock"] {
            gap: 0 !important;
            align-items: stretch;
            height: 100vh !important;
            overflow: hidden !important;
        }
 
        [data-testid="stSidebar"] { display: block !important; z-index: 999 !important; }
        [data-testid="stSidebarCollapsedControl"] { z-index: 999 !important; }
 
        /* Colonne carte (fixe) */
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
            flex: 0 0 76% !important;
            top: -10px;
            position: relative;
            background: #f0f0f0;
            border-right: 1px solid #ddd;
            padding: 0 !important;
            overflow: hidden !important;
            height: auto;
        }
 
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) {
            flex: 1 !important;
            padding: 0 !important;
            overflow: hidden;
            height: 100vh !important;
        }
 
        /* Colonne droite (seule à scroller) */
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
            flex: 0 0 24% !important;
            background: #FFFAF5;
            padding: 10px 10px !important;
            overflow-y: auto !important;
            height: 100vh !important;
        }
 
        [data-testid="stColumn"] > div { padding: 0 !important; }
        
 
        iframe[title="st.pydeck_chart"] { height: calc(100% - 46px) !important; min-height: calc(100vh - 46px) !important; }
 
        .panel-title { font-family: Georgia, serif; color: #751F0F; font-size: 20px; margin: 0 0 4px 0; border-bottom: 2px solid #751F0F; padding-bottom: 6px; }
        .sous-titre-graph { font-family: Georgia, serif; color: #751F0F; font-size: 14px; margin: 12px 0 2px 0; }
        .commune-selectionnee { font-family: Georgia, serif; font-size: 11px; color: #751F0F; background: #fdf0ed; border: 1px solid #751F0F; border-radius: 4px; padding: 6px 10px; margin-bottom: 10px; }
 
        .st-key-basemap_select_container {
            position: absolute !important;
            height: 30px; width: 200px; top: 15px; right: 450px;
            z-index: 999;
            background: rgba(255,255,255,0);
            padding: 3px 5px;
            border-radius: 4px;
        }
 
        .map-overlay-north {
            position: absolute; bottom: 92px; right: 22px; z-index: 500;
            pointer-events: none; filter: drop-shadow(0 1px 2px rgba(0,0,0,0.35));
        }
 
        [data-testid="stHeader"] {
            height: 20px !important;
            min-height: 20px !important;
            padding: 0 !important;
        }
        [data-testid="stHeader"] > div {
            height: 20px !important;
            min-height: 20px !important;
        }
        [data-testid="stSidebarCollapsedControl"] {
            top: 0 !important;
            height: 20px !important;
            z-index: 999 !important;
        }
 
 
    </style>
    """,
    unsafe_allow_html=True,
)


col_map, col_right = st.columns([0.7, 0.3])

with col_map:
    selection = st.pydeck_chart(
        deck,
        on_select="rerun",
        selection_mode="single-object",
        use_container_width=False,
        height=900,
    )

    # Échelle dynamique + flèche du nord, superposées en bas à droite de la carte
    st.markdown(
        f"""
        <div class="map-overlay-north">
            <svg width="34" height="46" viewBox="0 0 34 46" xmlns="http://www.w3.org/2000/svg">
                <polygon points="17,0 30,40 17,30 4,40" fill="#751F0F" stroke="#fff" stroke-width="1"/>
                <text x="17" y="46" text-anchor="middle" font-family="Georgia, serif" font-size="13" font-weight="bold" fill="#751F0F">N</text>
            </svg>
        </div>
        """,
        unsafe_allow_html=True,
    )


with col_right:

    if commune_sel:
        noms = ", ".join(commune_sel)
        label = "Communes sélectionnées" if len(commune_sel) > 1 else "Commune sélectionnée"
        st.markdown(f"<div class='commune-selectionnee'>{label} : <b>{noms}</b></div>", unsafe_allow_html=True)
        if st.button("Effacer la sélection", key="reset_sel"):
            st.session_state["commune_selectionnee"] = []
            st.session_state["sel_source"] = "sidebar"
            st.rerun()

    # Graphique en barre communes 
    st.markdown("<p class='sous-titre-graph'>Répartition par commune</p>", unsafe_allow_html=True)
    event_bar = st.plotly_chart(fig_bar, use_container_width=True, on_select="rerun", key="bar")

    # Donut 1 : Typologie (groupe_1) — évolue avec les points affichés
    st.markdown("<p class='sous-titre-graph'>Répartition par typologie</p>", unsafe_allow_html=True)
    if not comptage_typo.empty:
        st.plotly_chart(fig_donut_typo, use_container_width=True, key="donut_typo")
    else:
        st.info("Aucune typologie renseignée pour la sélection actuelle.")

    # Donut 2 : Chronologie (Siecle_1) — évolue avec les points affichés
    st.markdown("<p class='sous-titre-graph'>Répartition par période</p>", unsafe_allow_html=True)
    if not comptage_chrono.empty:
        st.plotly_chart(fig_donut_chrono, use_container_width=True, key="donut_chrono")
    else:
        st.info("Aucune période renseignée pour la sélection actuelle.")

    st.markdown("<p class='sous-titre-graph'>Test</p>", unsafe_allow_html=True)




if event_bar and event_bar.selection.get("points"):
    commune_cliquee = event_bar.selection["points"][0].get("x")
    if commune_cliquee:
        new_val = [commune_cliquee]
        if st.session_state.get("commune_selectionnee") != new_val:
            st.session_state["commune_selectionnee"] = new_val
            st.session_state["sel_source"] = "bar"
            st.rerun()

objects = {}
if selection and selection.selection:
    objects = selection.selection.get("objects", {})

point_hits = objects.get("points", [])
commune_hits = objects.get("communes", [])

if point_hits:
    show_point_popup(point_hits[0])
elif commune_hits:
    props = commune_hits[0]["properties"]
    nom_commune = props.get("NOM")
    if nom_commune and st.session_state.get("commune_selectionnee") != [nom_commune]:
        st.session_state["commune_selectionnee"] = [nom_commune]
        st.session_state["sel_source"] = "bar"
        st.rerun()
    show_commune_popup(props)