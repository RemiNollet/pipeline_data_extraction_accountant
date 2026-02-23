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

```bash
# Via Swagger UI
open http://127.0.0.1:8000/docs

# Ou via curl
curl -X POST -F "file=@test_invoice.png" \
  http://127.0.0.1:8000/api/v1/extract | jq
```

## 📝 Licence

Prototype à usage interne.
