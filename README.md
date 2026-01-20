# Atlas Interactif des Bassins de Production du Cameroun

Ce projet est une application de web-mapping qui permet de visualiser les données de production économique (agriculture, élevage, pêche) du Cameroun. L'interface cartographique interactive offre des filtres dynamiques par filière, produit et division administrative, ainsi que plusieurs modes de visualisation (symboles proportionnels et carte de chaleur).

## Aperçu de l'application

![Aperçu de l'application](https://i.imgur.com/example.png) 
*(Note: Remplacez l'URL par une vraie capture d'écran de votre application)*

---

## 🚀 Lancer le projet

Suivez ces étapes pour configurer et lancer l'application sur votre machine locale.

### 1. Prérequis

Avant de commencer, assurez-vous d'avoir installé les logiciels suivants :
- **Python 3.8+**
- **PostgreSQL 12+** avec l'extension **PostGIS 3+**
- **Git** (pour cloner le projet)

### 2. Installation

**Étape 1 : Cloner le projet**
```bash
git clone <URL_DU_PROJET>
cd <NOM_DU_DOSSIER_PROJET>
```

**Étape 2 : Créer un environnement virtuel et installer les dépendances Python**
Il est fortement recommandé d'utiliser un environnement virtuel pour isoler les dépendances du projet.

```bash
# Créer un environnement virtuel
python3 -m venv venv

# Activer l'environnement
# Sur Windows:
# venv\Scripts\activate
# Sur macOS/Linux:
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

**Étape 3 : Configurer la base de données PostgreSQL**
L'application nécessite une base de données PostgreSQL avec PostGIS activé.

1.  **Créez un utilisateur et une base de données.**
    *Ouvrez une session `psql` et exécutez les commandes suivantes. Remplacez `donpk` et `18151995` par le nom d'utilisateur et le mot de passe de votre choix.*

    ```sql
    -- Créez un nouvel utilisateur (role)
    CREATE ROLE donpk WITH LOGIN PASSWORD '18151995';

    -- Créez la base de données et donnez les droits à votre nouvel utilisateur
    CREATE DATABASE cameroun_production_db OWNER donpk;
    ```

2.  **Activez l'extension PostGIS.**
    *Connectez-vous à votre nouvelle base de données et activez l'extension.*

    ```bash
    # Quittez la session psql en cours (\q) et reconnectez-vous à la nouvelle base
    \c cameroun_production_db
    ```
    ```sql
    -- Activez l'extension PostGIS
    CREATE EXTENSION postgis;

    -- Vérifiez que l'extension est bien installée
    SELECT PostGIS_Version();
    ```

**Étape 4 : Mettre à jour les informations de connexion dans les fichiers du projet**
Ouvrez les deux fichiers suivants et assurez-vous que la configuration `DB_CONFIG` correspond bien à l'utilisateur et au mot de passe que vous venez de créer à l'étape 3.

- `app.py`
- `load_data.py`

Modifiez ce dictionnaire dans les deux fichiers :
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'cameroun_production_db',
    'user': 'donpk',         # Votre nom d'utilisateur
    'password': '18151995'    # Votre mot de passe
}
```
**Note de sécurité :** Pour un vrai projet en production, il est recommandé de gérer ces informations sensibles via des variables d'environnement plutôt qu'en les écrivant directement dans le code.

### 3. Utilisation

**Étape 1 : Charger les données dans la base de données**
Une fois la configuration terminée, exécutez le script `load_data.py` pour importer les fichiers GeoJSON et CSV dans votre base de données PostGIS.

*Assurez-vous que votre environnement virtuel est toujours activé.*
```bash
python load_data.py
```
Le script affichera la progression du chargement. Si tout se passe bien, vous verrez un message de succès à la fin.

**Étape 2 : Lancer le serveur web**
Maintenant, lancez l'application Flask.

```bash
python app.py
```
Le serveur démarrera, généralement sur le port 5000.

**Étape 3 : Accéder à l'application**
Ouvrez votre navigateur web et rendez-vous à l'adresse suivante :
[**http://127.0.0.1:5000**](http://127.0.0.1:5000)

Vous devriez voir la carte interactive du Cameroun.

---

##  Architecture Technique

L'application utilise une architecture client-serveur :
- **Backend :** Une API RESTful développée avec **Flask (Python)** qui sert les données géospatiales depuis une base de données PostGIS.
- **Frontend :** Une interface utilisateur "single-page" construite avec **HTML, CSS et JavaScript pur**, utilisant **Leaflet.js** pour la cartographie.

![Architecture Diagram](https://i.imgur.com/3s0Y3f5.png)
