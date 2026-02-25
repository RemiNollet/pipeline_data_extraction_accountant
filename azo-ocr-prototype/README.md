# AZO OCR Prototype

Microservice d'extraction de données factures de la zone OHADA (PDF ou images) utilisant un Vision-Language Model.

## 🚀 Démarrage rapide

### Prérequis

- **Python 3.9+**
- **Clé API OpenAI** (https://platform.openai.com/api-keys)
- **Poppler** (pour la conversion PDF→image)
  - **macOS** : `brew install poppler`
  - **Ubuntu/Debian** : `apt install poppler-utils`
  - **Windows** : https://github.com/oschwartz10612/poppler-windows/releases

### Installation

```bash
# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer la clé API
echo "OPENAI_API_KEY=sk-..." > .env
```

### Lancer le serveur

```bash
uvicorn app.main:app --reload
```

Le serveur est accessible sur **http://127.0.0.1:8000**.

## 📚 Documentation API

- **Swagger UI** : http://127.0.0.1:8000/docs
- **ReDoc** : http://127.0.0.1:8000/redoc

## 🔌 Endpoints

### `GET /health`

Vérifie que le service répond.

```bash
curl http://127.0.0.1:8000/health
```

**Réponse** :
```json
{"status": "ok"}
```

### `POST /api/v1/extract`

Extrait les données d'une facture (image ou PDF, première page).

**Paramètres** :
- `file` (UploadFile) : Image JPEG/PNG/WebP/GIF ou PDF

**Réponse** :
```json
{
  "data": {
    "fournisseur": "Entreprise XYZ",
    "numero_facture": "F-2025-001",
    "date": "2025-02-23",
    "montant_ht": 1000.00,
    "montant_tva": 200.00,
    "montant_ttc": 1200.00,
    "devise": "XAF",
    "lignes_detail": [
      {
        "description": "Service consulting",
        "quantite": 10,
        "prix_unitaire": 100.00
      }
    ]
  },
  "needs_human_review": false,
  "error_message": null
}
```

**Exemple avec curl** :
```bash
curl -X POST -F "file=@facture.pdf" http://127.0.0.1:8000/api/v1/extract
```

## 🏗️ Architecture

Voir [ARCHITECTURE.md](ARCHITECTURE.md) pour les détails sur l'architecture du système.

## ⚙️ Configuration

Les paramètres sont chargés depuis le fichier `.env` :

```env
# Obligatoire
OPENAI_API_KEY=sk-...

# Optionnel (valeurs par défaut)
LLM_MODEL_LIGHT=gpt-4o-mini      # Premier essai (économique)
LLM_MODEL_HEAVY=gpt-4o            # Fallback (plus puissant)
```

## 📦 Dépendances

- **fastapi** : Framework web
- **pydantic** : Validation de schémas
- **openai** : Client OpenAI
- **pdf2image** : Conversion PDF → image
- **pillow** : Manipulation d'images

Voir `requirements.txt` pour les versions exactes.

## 🧪 Tester le prototype

### Tester via Swagger UI (recommandé)

```bash
# Le serveur doit être lancé
uvicorn app.main:app --reload

# Ouvrir l'interface Swagger
open http://127.0.0.1:8000/docs
```

Puis :
1. Cliquer sur **POST /api/v1/extract**
2. Cliquer **"Try it out"**
3. Upload une facture (PDF ou image)
4. Les résultats sont sauvegardés automatiquement dans `resultats/extractions.csv`

### Tester via curl

```bash
curl -X POST -F "file=@/chemin/vers/facture.pdf" \
  http://127.0.0.1:8000/api/v1/extract | jq
```

### Tester le pipeline complet

Le script `test/test_pipeline.py` teste automatiquement toutes les factures du dossier `sample_invoices/` :

```bash
# 1. Créer le dossier et ajouter des factures
mkdir -p sample_invoices
cp /chemin/vers/vos/factures/*.pdf sample_invoices/

# 2. Lancer le serveur (dans un terminal séparé)
uvicorn app.main:app --reload

# 3. Lancer le script de test (dans un autre terminal)
cd /chemin/vers/azo-ocr-prototype
python test/test_pipeline.py
```

Les résultats seront sauvegardés dans **`resultats/extractions.csv`** avec les colonnes :
- `timestamp` : moment du traitement
- `fichier_source` : nom du fichier
- `statut` : succès ou erreur
- `needs_human_review` : True si revue manuelle nécessaire
- `fournisseur`, `numero_facture`, `date`, montants, devise, etc.
- `error_message` : message d'erreur si applicable

### Tests unitaires

Pour tester les différents modules (quand les tests seront implémentés) :

```bash
# Installer pytest (déjà dans requirements.txt)
pip install pytest

# Lancer les tests
pytest test/ -v

# Lancer les tests d'un module spécifique
pytest test/test_validation.py -v
```

Les fichiers de test `test/test_*.py` contiennent les structures et commentaires
montrant où implémenter les tests unitaires pour :
- `test_normalization.py` : Nettoyage des données
- `test_validation.py` : Validation métier OHADA
- `test_llm_client.py` : Intégration OpenAI
- `test_ocr_pipeline.py` : Logique de cascading/fallback
- `test_routes.py` : Tests d'intégration API

## 📁 Structure des résultats

Après chaque extraction, un fichier CSV est créé/mis à jour :

```
resultats/
└── extractions.csv
    ├── timestamp
    ├── fichier_source
    ├── statut (succès/erreur)
    ├── needs_human_review
    ├── fournisseur
    ├── numero_facture
    ├── date
    ├── montant_ht, montant_tva, montant_ttc
    ├── devise
    ├── ifu_fournisseur (OHADA)
    ├── code_mecef (OHADA)
    ├── confiance (score 0-1)
    ├── nombre_lignes
    └── error_message
```

## ⚠️ Problèmes rencontrés et solutions

### 1. **Format de fichier non reconnu lors de l'upload (curl)**

**Problème** : Erreur "Type de fichier non supporté, reçu: ''"

**Cause** : La bibliothèque `requests` (utilisée dans `test/test_pipeline.py`) n'envoyait pas le type MIME.

**Solution** : Spécifier explicitement le type MIME dans le tuple d'upload :
```python
files = {"file": (filename, file_object, "application/pdf")}  # Ajouter le type MIME
```

---

### 2. **Format décimal français mal parsé (300.000 → 300.0 au lieu de 300000.0)**

**Problème** : Les factures françaises utilisent le point (.) comme séparateur de milliers et la virgule (,) comme décimal. Le LLM parsait "300.000" comme 300.0 (format US).

**Cause** : Le LLM n'avait pas d'instructions claires sur le format décimal francophone.

**Solution** : Amélioration du `SYSTEM_PROMPT` avec des exemples concrets :
```
ZONE FRANCOPHONE : point (.) = milliers, virgule (,) = décimal
Exemples : "300.000,50 XOF" → 300000.50 | "14.489.448 XOF" → 14489448.0
RÈGLE : Enlève TOUS les points, remplace la virgule par un point
```

---

### 3. **gpt-4o-mini retournait du JSON mal formé (None, markdown, etc.)**

**Problème** : Le modèle léger retournait des champs None ou du JSON enrobé en markdown (```json...```).

**Causes** :
- Manque de clarté dans les instructions
- Le modèle ajoutait du markdown au JSON

**Solutions appliquées** :
1. Renforcement du prompt avec des règles immuables :
   ```
   - Les montants DOIVENT TOUS être des nombres (float) : jamais null ou string
   - Commence immédiatement avec { et termine avec }
   - Ne JAMAIS enrober le JSON en markdown
   ```

2. Ajout d'une fonction de parsing robuste `_clean_json_response()` pour :
   - Enlever les blocs markdown ```json...```
   - Extraire le JSON valide entre les accolades
   - Gérer les cas limites

---

### 4. **TVA = 0 levait une erreur de validation (factures assurance/notaire)**

**Problème** : Les factures d'assurance et de notaire ont souvent une TVA = 0, ce qui déclenchait l'erreur "HT + TVA ≠ TTC".

**Cause** : La validation Pydantic appliquait la règle `montant_ht + montant_tva == montant_ttc` même pour les structures spéciales.

**Solution** : Modification du validateur pour détecter et accepter le cas TVA = 0.0 :
```python
@model_validator(mode="after")
def check_ht_tva_ttc(self):
    # TVA = 0 : cas spécial (assurance, notaire), accepté mais signalé
    if self.montant_tva == 0.0:
        return self
    
    # Cas normal : vérifier HT + TVA == TTC
    somme = self.montant_ht + self.montant_tva
    if abs(somme - self.montant_ttc) > MONTANT_TOLERANCE:
        raise MathValidationError(...)
    return self
```

Le pipeline marque `needs_human_review = True` pour ces cas spéciaux.

---

## 📝 Licence

Prototype à usage interne.
