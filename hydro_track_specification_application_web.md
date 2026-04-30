# HydroTrack

## 1. Présentation générale

**HydroTrack** est une application web de monitoring en temps réel dédiée à la détection, à l’analyse et à la visualisation des fuites d’eau sur le réseau d’eau d’EDF.

L’application combine :
- L’analyse de données issues de compteurs d’eau
- L’exploitation de capteurs d’ondes de pression
- Des modèles de machine learning pour la détection d’anomalies
- Une cartographie temps réel du réseau

L’objectif principal est d’identifier rapidement :
- Les anomalies de consommation
- Les fuites potentielles
- Leur localisation précise
- L’état global du réseau en temps réel

---

## 2. Objectifs fonctionnels

- Suivi en temps réel de 12 compteurs d’eau
- Détection automatique d’anomalies via un modèle de machine learning
- Analyse des signaux de pression pour confirmer et localiser les fuites
- Visualisation claire via dashboards et cartes interactives
- Système d’alertes en temps réel
- Évaluation continue de l’efficacité du système

---

## 3. Architecture globale

### 3.1 Vue d’ensemble

```
Capteurs & Compteurs
        ↓ (API temps réel)
Backend (API + ML + Traitement)
        ↓
Base de données temps réel
        ↓
Frontend Web (Dashboards + Carte)
```

---

## 4. Sources de données

### 4.1 Compteurs d’eau

- Nombre initial : 23 compteurs (extensible)
- Liste des compteurs réseau EP DATANUMIA – CNPE Nogent / Seine :
  - AMPERE (x2)
  - BCA1
  - BCA2
  - BECQUEREL
  - CCAS
  - CHARPAK
  - EINSTEIN
  - SIMULATEUR
  - FARADAY
  - FRANKLIN
  - JOLIOT CURIE (x2)
  - NEWTON
  - PAP
  - VOLTA
  - AVOGADRO
  - EDISON
  - COULOMB1
  - COULOMB2
  - TREMPLIN
  - SALLE MUSCULATION

- **Extensibilité** :
  - Possibilité d’ajouter, supprimer ou modifier des compteurs dynamiquement
  - Les compteurs sont gérés via une configuration centralisée (base de données / interface admin)

- Données reçues :
  - Horodatage
  - Volume consommé
  - Débit
  - Identifiant compteur

- Insertion des données :
  - Via API temps réel
  - Chaque réception de données déclenche automatiquement :
    - L’analyse par le modèle de machine learning
    - La mise à jour des dashboards
    - La génération d’alertes si nécessaire

### 4.2 Capteurs d’ondes de pression

- Données reçues en temps réel via API :
  - Signal de pression
  - Fréquence
  - Intensité
  - Horodatage
  - Identifiant capteur
  - Zone géographique

- **Zones d’implantation des capteurs** :
  - Zone 1 : CRT
  - Zone 2 : Entreprise
  - Zone 3 : AIE
  - Zone 4 : Aire TFA / Vigilia
  - Zone 5 : IPE
  - Zone 6 : TR 3 / TR 4
  - Zone 7 : TR 2
  - Zone 8 : TR 1
  - Zone 9 : Réfrigérants
  - Zone 10 : BTE
  - Zone 11 : SUT / PAP
  - Zone 12 : MIF / Restaurant
  - Zone 13 : Accueil / Parking / Simulateur / CIP

- Accessibilité :
  - **INTERNERDU : D454309372485**

- Fonctionnement :
  - Chaque nouvelle donnée reçue déclenche :
    - L’analyse des signaux de pression
    - La corrélation entre capteurs
    - La mise à jour en temps réel des alertes et de la carte

---

## 5. Machine Learning

### 5.1 Détection d’anomalies (compteurs)

- Modèle fourni par l’utilisateur
- Rôle du modèle :
  - Identifier les comportements anormaux
  - Estimer la probabilité de fuite

### 5.2 Analyse des ondes de pression

- Traitement du signal (filtrage, extraction de caractéristiques)
- Corrélation entre capteurs
- Détermination du point de fuite par triangulation / analyse spatiale

---

## 6. Backend

### 6.1 API

- Réception des données temps réel
- Endpoints principaux (exemples) :

```http
POST /api/meters/data
POST /api/sensors/pressure
GET  /api/anomalies
GET  /api/alerts
GET  /api/network/state
```

### 6.2 Traitements

- Ingestion temps réel
- Stockage des données
- Appel du modèle ML
- Génération d’alertes

---

## 7. Frontend

### 7.1 Dashboards

- État global du réseau
- Consommation par compteur
- Historique des anomalies
- Alertes actives
- Indicateurs de performance

### 7.2 Visualisations

- Graphiques temps réel
- Séries temporelles
- Heatmaps de pression

---

## 8. Cartographie du réseau

### 8.1 Carte interactive

- Affichage du réseau d’eau complet
- Position réelle des :
  - Compteurs
  - Capteurs
- Mise à jour en temps réel

### 8.2 Alertes géolocalisées

- Points de fuite affichés sur la carte
- Codes couleur selon la gravité
- Informations contextuelles au clic

---

## 9. Système d’alertes

- Alertes temps réel :
  - Fuite suspectée
  - Fuite confirmée
  - Anomalie critique
- Canaux possibles :
  - Interface web
  - Notifications

---

## 10. Sécurité & fiabilité

- Authentification API
- Validation des données entrantes
- Journalisation des événements
- Tolérance aux pannes

---

## 11. Technologies (à définir)

- **Frontend** : React / Vue / autre
- **Backend** : Node.js / Python (FastAPI)
- **Base de données** : Time-series / SQL / NoSQL
- **ML** : Python (scikit-learn, PyTorch, etc.)
- **Cartographie** : Mapbox / Leaflet
- **Temps réel** : WebSockets / MQTT

---

## 12. Évolutions futures

- Ajout de nouveaux capteurs
- Prédiction de fuites à moyen terme
- Optimisation de la maintenance
- Rapports automatiques

---

## 13. Résumé

HydroTrack vise à fournir une vision complète, fiable et en temps réel de l’état du réseau d’eau, permettant une détection rapide des fuites, une meilleure prise de décision et une amélioration significative de la performance opérationnelle.

