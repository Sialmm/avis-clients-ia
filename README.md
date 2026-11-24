# Analyse automatisée d'avis clients par IA

Pipeline qui récupère chaque semaine les avis Google de plusieurs restaurants, les classe avec un LLM (sentiment, thème, urgence) et envoie aux managers un rapport avec les actions prioritaires. Un dashboard Streamlit permet de suivre l'évolution dans le temps.

**Stack :** n8n · API Google Places · Google Gemini (LLM) · Google Sheets · Gmail · Streamlit · Python

## Fonctionnement

```
Chaque lundi 8h (n8n)
  → API Google Places : récupère les restaurants et leurs avis
  → Code : un item par avis, puis regroupement en une seule liste
  → LLM (Gemini, 1 seule requête) : sentiment, thèmes, urgence, résumé de chaque avis (JSON structuré)
  ├→ Google Sheets : historique des avis (sans doublon, clé = review_id)
  └→ Stats des 7 derniers jours → LLM : 3 actions prioritaires → mail HTML aux managers

Dashboard Streamlit ← lit le Google Sheet
```

## Installation

### 1. Google Sheet
Crée un Google Sheet avec un onglet nommé **`Avis`** et cette ligne d'en-tête :

```
review_id | date | restaurant | adresse | note | auteur | avis | sentiment | score | themes | urgence | resume | traite_le
```

### 2. Workflow n8n
1. Dans n8n : **Workflows → Import from file** → `workflow_avis_ia.json`.
2. Crée les identifiants (credentials) :
   - **Google Places** : type *Header Auth*, nom `X-Goog-Api-Key`, valeur = ta clé API Google Cloud (activer *Places API (New)*).
   - **Google Gemini** : clé gratuite sur [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
   - **Google Sheets** et **Gmail** : connexion OAuth Google.
3. Associe chaque credential à son nœud.
4. Dans le nœud **Config**, renseigne la recherche (`searchQuery`), le filtre de nom et l'email du destinataire ; sélectionne ton Sheet dans le nœud **Google Sheets - historique**.
5. Clique sur **Lancer à la main** pour tester, puis active le workflow.

### 3. Dashboard
```bash
pip install -r requirements.txt
streamlit run app.py
```
Partage le Sheet en lecture (« toute personne disposant du lien ») et colle son ID dans la barre latérale, ou définis `SHEET_ID` dans `.streamlit/secrets.toml`. Un **mode démo** avec des données fictives permet de tester sans clé API.

## Limites
- Tous les avis sont classés en **une seule requête** au LLM, pour rester dans le quota gratuit de Gemini (environ 20 requêtes par jour).
- L'API Google Places renvoie au maximum **5 avis par établissement** par appel ; l'historique se construit donc semaine après semaine dans le Sheet.
- Les avis sont reformulés et classés par un LLM : à relire avant toute décision importante.
- Ne jamais publier ses clés API sur GitHub (elles restent dans les credentials n8n).
