Démo : 
https://avis-clients-ia-fvjuaoqwdlwc3p6stomgev.streamlit.app/

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
  └→ Stats des 7 derniers jours → sujets récurrents + LLM : pistes d'amélioration → mail HTML aux managers

Dashboard Streamlit ← lit le Google Sheet
```
