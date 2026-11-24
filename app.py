"""Dashboard Streamlit : suivi des avis clients classés par IA (alimenté par le workflow n8n)."""
import os

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Avis clients IA", page_icon="🍣", layout="wide")
st.title("Analyse des avis clients par IA")


@st.cache_data(ttl=600)
def load(url: str) -> pd.DataFrame:
    return pd.read_csv(url)


# --- Source des données ---------------------------------------------------
try:
    sheet_id = st.secrets.get("SHEET_ID", os.getenv("SHEET_ID", ""))
except Exception:  # pas de fichier secrets.toml
    sheet_id = os.getenv("SHEET_ID", "")
source = st.sidebar.radio("Source", ["Google Sheet", "Fichier CSV"])

if source == "Google Sheet":
    sheet_id = st.sidebar.text_input("ID du Google Sheet", sheet_id)
    if not sheet_id:
        st.info("Renseigne l'ID du Google Sheet (partagé en lecture via le lien).")
        st.stop()
    df = load(f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Avis")
else:
    f = st.sidebar.file_uploader("Export CSV de l'onglet Avis", type="csv")
    if not f:
        st.stop()
    df = pd.read_csv(f)

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["note"] = pd.to_numeric(df["note"], errors="coerce")
df["themes"] = df["themes"].fillna("").astype(str)

# --- Filtres -----------------------------------------------------------------
restos = sorted(df["restaurant"].dropna().unique())
choix = st.sidebar.multiselect("Restaurants", restos, default=restos)
df = df[df["restaurant"].isin(choix)]
if df.empty:
    st.info("Aucun avis pour cette sélection.")
    st.stop()

# --- KPIs ---------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Avis analysés", len(df))
k2.metric("Note moyenne", f"{df['note'].mean():.2f} / 5")
k3.metric("Avis négatifs", f"{(df['sentiment'] == 'negatif').mean():.0%}")
k4.metric("Urgents", int((df["urgence"] == "haute").sum()))

# --- Graphiques ---------------------------------------------------------------
c1, c2 = st.columns(2)
with c1:
    st.subheader("Sentiment par restaurant")
    st.altair_chart(
        alt.Chart(df).mark_bar().encode(
            y=alt.Y("restaurant:N", title=None),
            x=alt.X("count():Q", stack="normalize", title="Part des avis", axis=alt.Axis(format="%")),
            color=alt.Color("sentiment:N", scale=alt.Scale(domain=["positif", "neutre", "negatif"],
                                                           range=["#2e7d32", "#9e9e9e", "#c62828"])),
        ),
        width="stretch",
    )
with c2:
    st.subheader("Sujets des avis négatifs")
    neg = df[df["sentiment"] == "negatif"]["themes"].str.split(", ").explode()
    neg = neg[neg != ""].value_counts().rename_axis("theme").reset_index(name="avis")
    st.altair_chart(
        alt.Chart(neg).mark_bar(color="#c62828").encode(
            x=alt.X("avis:Q"), y=alt.Y("theme:N", sort="-x", title=None)),
        width="stretch",
    )

st.subheader("Évolution de la note moyenne par semaine (depuis 2026)")
recents = df[df["date"] >= pd.Timestamp("2026-01-01")].dropna(subset=["date"])
if recents.empty:
    st.info("Aucun avis publié depuis le 1er janvier 2026.")
else:
    choix_resto = st.selectbox(
        "Restaurant à afficher",
        ["Tous les restaurants"] + sorted(recents["restaurant"].unique()),
        key="resto_courbe",
    )
    if choix_resto != "Tous les restaurants":
        recents = recents[recents["restaurant"] == choix_resto]
        c_a, c_b, c_c = st.columns(3)
        c_a.metric("Avis depuis 2026", len(recents))
        c_b.metric("Note moyenne", f"{recents['note'].mean():.2f} / 5")
        c_c.metric("Avis négatifs", f"{(recents['sentiment'] == 'negatif').mean():.0%}")
    hebdo = (recents.set_index("date").groupby("restaurant")["note"]
             .resample("W").mean().dropna().reset_index())
    st.altair_chart(
        alt.Chart(hebdo).mark_line(point=True).encode(
            x=alt.X("date:T", title=None, axis=alt.Axis(format="%d %b")),
            y=alt.Y("note:Q", title="Note moyenne", scale=alt.Scale(domain=[1, 5])),
            color=alt.Color("restaurant:N", title=None),
            tooltip=[alt.Tooltip("restaurant:N"), alt.Tooltip("date:T", format="%d/%m/%Y"),
                     alt.Tooltip("note:Q", format=".1f")],
        ),
        width="stretch",
    )

st.subheader("Avis urgents à traiter")
st.dataframe(
    df[df["urgence"] == "haute"].sort_values("date", ascending=False)
    [["date", "restaurant", "note", "themes", "resume"]],
    width="stretch", hide_index=True,
)
