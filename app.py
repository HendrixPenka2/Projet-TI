from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, text
import json

print("--- Démarrage du script app.py ---")

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'cameroun_production_db',
    'user': 'donpk',
    'password': '18151995' 
}

def get_engine():
    connection_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    return create_engine(connection_string, pool_pre_ping=True)

print("--- Création du moteur de base de données... ---")
engine = get_engine()
print("--- Moteur de base de données créé avec succès. ---")

def execute_geojson_query(query, params=None):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            rows = result.fetchall()
            features = []
            for row in rows:
                geojson_geom = json.loads(row[0]) if row[0] else None
                properties = {}
                keys = list(result.keys())
                for i, col in enumerate(keys[1:], start=1):
                    properties[col] = row[i]
                if geojson_geom:
                    features.append({"type": "Feature", "geometry": geojson_geom, "properties": properties})
            return {"type": "FeatureCollection", "features": features}
    except Exception as e:
        print(f"Erreur SQL: {e}")
        return {"type": "FeatureCollection", "features": []}

def execute_query(query, params=None):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            return [dict(zip(result.keys(), row)) for row in result.fetchall()]
    except Exception as e:
        print(f"Erreur: {e}")
        return []

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/regions')
def get_regions():
    filiere = request.args.get('filiere')
    bassin = request.args.get('bassin')

    base_query = """
    WITH productions_filtered AS (
        SELECT region_pcode, produit, quantite, filiere
        FROM (
            SELECT 
                region_pcode, 
                produit, 
                production_tonnes_estimee as quantite, 
                filiere,
                CASE WHEN :filiere = 'Tous' THEN 1 ELSE (CASE WHEN filiere = :filiere THEN 1 ELSE 0 END) END as filiere_match,
                CASE WHEN :bassin = 'Tous' THEN 1 ELSE (CASE WHEN produit = :bassin THEN 1 ELSE 0 END) END as bassin_match
            FROM productions
        ) p
        WHERE filiere_match = 1 AND bassin_match = 1
    ),
    productions_agg AS (
        SELECT 
            p.region_pcode,
            json_agg(json_build_object('produit', p.produit, 'quantite', p.quantite, 'filiere', p.filiere)) as productions,
            SUM(p.quantite) as total_production
        FROM productions_filtered p
        GROUP BY p.region_pcode
    )
    SELECT 
        ST_AsGeoJSON(r.geom) as geojson, 
        r.adm1_pcode, 
        r.adm1_name1,
        pa.productions,
        COALESCE(pa.total_production, 0) as total_production
    FROM regions r
    LEFT JOIN productions_agg pa ON r.adm1_pcode = pa.region_pcode
    """
    
    params = {
        'filiere': filiere if filiere else 'Tous',
        'bassin': bassin if bassin else 'Tous'
    }
    
    return jsonify(execute_geojson_query(base_query, params))

@app.route('/api/departments')
def get_departments():
    region_pcode = request.args.get('region_pcode')
    filiere = request.args.get('filiere')
    bassin = request.args.get('bassin')

    base_query = """
    WITH productions_filtered AS (
        SELECT region_pcode, produit, quantite, filiere
        FROM (
            SELECT 
                region_pcode, 
                produit, 
                production_tonnes_estimee as quantite, 
                filiere,
                CASE WHEN :filiere = 'Tous' THEN 1 ELSE (CASE WHEN filiere = :filiere THEN 1 ELSE 0 END) END as filiere_match,
                CASE WHEN :bassin = 'Tous' THEN 1 ELSE (CASE WHEN produit = :bassin THEN 1 ELSE 0 END) END as bassin_match
            FROM productions
        ) p
        WHERE filiere_match = 1 AND bassin_match = 1
    ),
    productions_agg AS (
        SELECT 
            d.adm2_pcode,
            json_agg(json_build_object('produit', p.produit, 'quantite', p.quantite, 'filiere', p.filiere)) as productions,
            SUM(p.quantite) as total_production
        FROM productions_filtered p
        JOIN departements d ON p.region_pcode = d.adm1_pcode
        GROUP BY d.adm2_pcode
    )
    SELECT 
        ST_AsGeoJSON(d.geom) as geojson, 
        d.adm2_pcode, 
        d.adm2_name1,
        d.adm1_pcode,
        pa.productions,
        COALESCE(pa.total_production, 0) as total_production
    FROM departements d
    LEFT JOIN productions_agg pa ON d.adm2_pcode = pa.adm2_pcode
    """
    
    params = {
        'filiere': filiere if filiere else 'Tous',
        'bassin': bassin if bassin else 'Tous'
    }
    conditions = []
    if region_pcode:
        conditions.append("d.adm1_pcode = :pcode")
        params['pcode'] = region_pcode

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    return jsonify(execute_geojson_query(base_query, params))

@app.route('/api/communes')
def get_communes():
    dept_pcode = request.args.get('department_pcode')
    filiere = request.args.get('filiere')
    bassin = request.args.get('bassin')

    base_query = """
    WITH productions_filtered AS (
        SELECT region_pcode, produit, quantite, filiere
        FROM (
            SELECT 
                region_pcode, 
                produit, 
                production_tonnes_estimee as quantite, 
                filiere,
                CASE WHEN :filiere = 'Tous' THEN 1 ELSE (CASE WHEN filiere = :filiere THEN 1 ELSE 0 END) END as filiere_match,
                CASE WHEN :bassin = 'Tous' THEN 1 ELSE (CASE WHEN produit = :bassin THEN 1 ELSE 0 END) END as bassin_match
            FROM productions
        ) p
        WHERE filiere_match = 1 AND bassin_match = 1
    ),
    productions_agg AS (
        SELECT 
            c.adm3_pcode,
            json_agg(json_build_object('produit', p.produit, 'quantite', p.quantite, 'filiere', p.filiere)) as productions,
            SUM(p.quantite) as total_production
        FROM productions_filtered p
        JOIN departements d ON p.region_pcode = d.adm1_pcode
        JOIN communes c ON d.adm2_pcode = c.adm2_pcode
        GROUP BY c.adm3_pcode
    )
    SELECT 
        ST_AsGeoJSON(c.geom) as geojson, 
        c.adm3_pcode, 
        c.adm3_name1,
        c.adm2_pcode,
        pa.productions,
        COALESCE(pa.total_production, 0) as total_production
    FROM communes c
    LEFT JOIN productions_agg pa ON c.adm3_pcode = pa.adm3_pcode
    """
    
    params = {
        'filiere': filiere if filiere else 'Tous',
        'bassin': bassin if bassin else 'Tous'
    }
    conditions = []
    if dept_pcode:
        conditions.append("c.adm2_pcode = :pcode")
        params['pcode'] = dept_pcode

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    return jsonify(execute_geojson_query(base_query, params))

@app.route('/api/productions')
def get_productions():
    return jsonify(execute_query("SELECT * FROM productions"))

@app.route('/api/bassins')
def get_bassins():
    filiere = request.args.get('filiere')
    if filiere and filiere != 'Tous':
        query = "SELECT DISTINCT produit FROM productions WHERE filiere = :filiere ORDER BY produit"
        params = {'filiere': filiere}
    else:
        query = "SELECT DISTINCT produit FROM productions ORDER BY produit"
        params = {}
    results = execute_query(query, params)
    return jsonify([r['produit'] for r in results])

@app.route('/api/filieres')
def get_filieres():
    results = execute_query("SELECT DISTINCT filiere FROM productions ORDER BY filiere")
    return jsonify([r['filiere'] for r in results])


@app.route('/api/comparison')
def get_comparison_data():
    dept_pcode = request.args.get('department_pcode')
    filiere = request.args.get('filiere', 'Tous')
    bassin = request.args.get('bassin', 'Tous')

    if not dept_pcode:
        return jsonify({'error': 'department_pcode is required'}), 400

    query = """
    WITH region_info AS (
        SELECT adm1_pcode FROM departements WHERE adm2_pcode = :dept_pcode
    ),
    productions_in_region AS (
        SELECT 
            d.adm2_pcode,
            d.adm2_name1,
            SUM(p.production_tonnes_estimee) as total_production
        FROM productions p
        JOIN departements d ON p.region_pcode = d.adm1_pcode
        WHERE d.adm1_pcode = (SELECT adm1_pcode FROM region_info)
        AND (:filiere = 'Tous' OR p.filiere = :filiere)
        AND (:bassin = 'Tous' OR p.produit = :bassin)
        GROUP BY d.adm2_pcode, d.adm2_name1
    )
    SELECT * FROM productions_in_region ORDER BY total_production DESC;
    """
    
    params = {
        'dept_pcode': dept_pcode,
        'filiere': filiere,
        'bassin': bassin
    }
    
    result = execute_query(query, params)
    return jsonify(result)

if __name__ == '__main__':
    print("--- Lancement du serveur Flask... ---")
    try:
        app.run(debug=True, port=5000)
    except Exception as e:
        print(f"Erreur lors du démarrage du serveur: {e}")
        import traceback
        traceback.print_exc()
        input("Appuyez sur Entrée pour quitter...")