"""Dashboard Streamlit : suivi des avis clients classés par IA (alimenté par le workflow n8n)."""
import os
import random
from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Avis clients IA", page_icon="🍣", layout="wide")
st.title("Analyse des avis clients par IA")


def demo_data(n: int = 120) -> pd.DataFrame:
    """Données FICTIVES pour tester le dashboard sans clé API."""
    random.seed(0)
    restos = ["Restaurant Démo 1", "Restaurant Démo 2", "Restaurant Démo 3"]
    themes = ["service", "attente", "qualite", "prix", "livraison", "proprete", "ambiance"]
    rows = []
    for i in range(n):
        note = random.choices([1, 2, 3, 4, 5], weights=[1, 1, 2, 4, 5])[0]
        sentiment = "negatif" if note <= 2 else "neutre" if note == 3 else "positif"
        rows.append({
            "review_id": f"demo-{i}",
            "date": (date.today() - timedelta(days=random.randint(0, 90))).isoformat(),
            "restaurant": random.choice(restos),
            "note": note,
            "sentiment": sentiment,
            "score": {1: -2, 2: -1, 3: 0, 4: 1, 5: 2}[note],
            "themes": ", ".join(random.sample(themes, k=random.randint(1, 2))),
            "urgence": "haute" if note == 1 and random.random() < 0.5 else "basse",
            "resume": "Avis fictif de démonstration",
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=600)
def load(url: str) -> pd.DataFrame:
    return pd.read_csv(url)


# --- Source des données ---------------------------------------------------
try:
    sheet_id = st.secrets.get("SHEET_ID", os.getenv("SHEET_ID", ""))
except Exception:  # pas de fichier secrets.toml
    sheet_id = os.getenv("SHEET_ID", "")
source = st.sidebar.radio("Source", ["Google Sheet", "Fichier CSV", "Démo (données fictives)"],
                          index=0 if sheet_id else 2)

if source == "Google Sheet":
    sheet_id = st.sidebar.text_input("ID du Google Sheet", sheet_id)
    if not sheet_id:
        st.info("Renseigne l'ID du Google Sheet (partagé en lecture via le lien).")
        st.stop()
    df = load(f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Avis")
elif source == "Fichier CSV":
    f = st.sidebar.file_uploader("Export CSV de l'onglet Avis", type="csv")
    if not f:
        st.stop()
    df = pd.read_csv(f)
else:
    st.warning("Mode démo : données fictives générées pour illustrer le dashboard.")
    df = demo_data()

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

st.subheader("Évolution de la note moyenne par semaine")
hebdo = (df.dropna(subset=["date"]).set_index("date").groupby("restaurant")["note"]
         .resample("W").mean().reset_index())
st.altair_chart(
    alt.Chart(hebdo).mark_line(point=True).encode(
        x=alt.X("date:T", title=None), y=alt.Y("note:Q", scale=alt.Scale(domain=[1, 5])), color="restaurant:N"),
    width="stretch",
)

st.subheader("Avis urgents à traiter")
st.dataframe(
    df[df["urgence"] == "haute"].sort_values("date", ascending=False)
    [["date", "restaurant", "note", "themes", "resume"]],
    width="stretch", hide_index=True,
)
