# HydroTrack - plateforme web complete

Base de demarrage du projet HydroTrack a partir de la specification fonctionnelle.

## Ce qui est inclus

- API FastAPI pour ingestion de donnees compteurs et capteurs
- Persistance SQLite locale (`backend/data/hydrotrack.db`)
- Moteur IA hybride (IsolationForest si dispo, fallback statistique sinon)
- Endpoints conformes a la specification:
  - `POST /api/meters/data`
  - `POST /api/sensors/pressure`
  - `GET /api/anomalies`
  - `GET /api/alerts`
  - `GET /api/network/state`
- WebSocket temps reel: `ws://localhost:8000/ws/events`
- Frontend React professionnel (dashboard + cartographie)
- Script d'ingestion CSV: `scripts/ingest_csv.py`

## Lancer le backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Si le port 8000 est deja pris, verifier d'abord si un backend HydroTrack tourne deja.

Swagger:

- [http://localhost:8000/docs](http://localhost:8000/docs)

## Lancer le frontend React

Dans un autre terminal:

```bash
cd frontend
npm install
npm run dev
```

Puis ouvrir:

- [http://localhost:5173](http://localhost:5173)

Le frontend inclut:

- Pages dashboard (theme clair bleu):
  - `/dashboard` synthese globale
  - `/dashboard/compteurs` debit, volumes, top compteurs, series debit
  - `/dashboard/capteurs` intensite / frequence, alertes pression
  - `/dashboard/alertes` statistiques gravite / categories, journal
  - `/dashboard/detection` vue ML / probabilites de fuite
- Page Cartographie dediee:
  - Carte capteurs & zones + carte compteurs (deux cartes cote a cote)
  - Points d'alertes geolocalises

## Exemple d'appel API

```bash
curl -X POST "http://localhost:8000/api/meters/data" \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp":"2026-04-17T12:00:00Z",
    "meter_id":"AMPERE_1",
    "volume":120.2,
    "flow_rate":23.7
  }'
```

## Ingestion CSV de test

Avec le backend lance:

```bash
python3 scripts/ingest_csv.py --csv CALCUL_JPD_2025.csv --max-rows 300
```

## Prochaines etapes recommandees

- Ajouter authentification API (token/JWT)
- Connecter PostgreSQL/TimescaleDB en remplacement de SQLite
- Ajouter vraie analyse capteurs de pression (filtrage signal, triangulation)
- Ajouter module admin (gestion dynamique compteurs/capteurs/zones)
