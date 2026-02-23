# Architecture du Microservice AZO OCR

## 🎯 Vue d'ensemble

Le microservice orchestre un pipeline d'extraction de données facture via Vision-Language Model avec **fallback cascading** pour la fiabilité.

```
┌─────────────────────────────────────────────────────────────────┐
│                        API FastAPI                               │
│                    POST /api/v1/extract                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────┐
        │  Conversion fichier → image      │
        │  • Image → base64                │
        │  • PDF (1ère page) → image →    │
        │    base64                        │
        └──────────────────────┬───────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────────┐
        │         Pipeline Cascading (ocr_pipeline)        │
        │                                                   │
        │  ┌────────────────────────────────────────────┐ │
        │  │ Étape 1: gpt-4o-mini (rapide/économique)  │ │
        │  │ • Appel API OpenAI avec image             │ │
        │  │ • Réponse structurée (JSON)               │ │
        │  │ • Validation Pydantic                     │ │
        │  │   └─ Montants: HT + TVA == TTC (±0.05)   │ │
        │  └──────────────┬─────────────────────────────┘ │
        │                 │                                │
        │        ┌────────▼──────────┐                     │
        │        │ Succès? ✓         │ Échec? ✗          │
        │        └────────┬──────────┘                     │
        │                 │                                │
        │                 │  ┌──────────────────────────┐  │
        │                 │  │ Étape 2: gpt-4o (robust)│  │
        │                 │  │ • Fallback si          │  │
        │                 │  │   validation échouée    │  │
        │                 │  │ • Log warning           │  │
        │                 │  └──────┬──────────────────┘  │
        │                 │         │                     │
        │                 └─────────┤ Succès? ✓           │
        │                           │                     │
        │                    ┌──────▼────────────┐        │
        │                    │ Échec aussi? ✗    │        │
        │                    │ → human_review    │        │
        │                    │   = true           │        │
        │                    └───────────────────┘        │
        └───────────────────────┬──────────────────────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────────┐
        │  ExtractionResult                             │
        │  • data: InvoiceData | None                   │
        │  • needs_human_review: bool                   │
        │  • error_message: str | None                  │
        └───────────────────┬───────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────────────┐
        │        Réponse API                           │
        │  {                                            │
        │    "data": {...} | null,                    │
        │    "needs_human_review": bool,              │
        │    "error_message": str | null              │
        │  }                                            │
        └──────────────────────────────────────────────┘
```

## 📂 Structure des fichiers

```
azo-ocr-prototype/
│
├── app/
│   ├── __init__.py
│   ├── main.py                          # Application FastAPI
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                    # Settings (BaseSettings Pydantic)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                    # Endpoint POST /extract
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py                   # Schémas Pydantic (InvoiceData, LigneDetail)
│   │   ├── validation.py                # validate_invoice_math()
│   │   └── constants.py                 # MONTANT_TOLERANCE, MathValidationError
│   │
│   └── services/
│       ├── __init__.py
│       ├── llm_client.py                # Client OpenAI + Structured Outputs
│       ├── ocr_pipeline.py              # Orchestration et cascading
│       └── normalization.py             # Nettoyage de données
│
├── requirements.txt                     # Dépendances Python
├── README.md                             # Guide d'utilisation
├── ARCHITECTURE.md                      # Ce fichier
└── .env                                  # Configuration (non versionné)
```

## 🔄 Flux de traitement détaillé

### 1. **Réception du fichier** (`routes.py`)

```python
POST /api/v1/extract
└─ UploadFile (image JPEG/PNG/WebP/GIF ou PDF)
```

- Validation du type MIME
- Lecture du fichier
- Conversion en image base64 (PDF: 1ère page uniquement via `pdf2image`)

### 2. **Pipeline d'extraction** (`ocr_pipeline.py`)

**Étape 1 : modèle léger**
```
image_base64 → gpt-4o-mini → JSON → Pydantic validation
                              ↓
                        Validation OK?
                        /            \
                      OUI            NON
                       ↓               ↓
                    Retourner      Log warning
                    (OK)           Fallback
```

**Étape 2 : fallback (modèle lourd)**
```
image_base64 → gpt-4o → JSON → Pydantic validation
                         ↓
                   Validation OK?
                   /            \
                 OUI            NON
                  ↓               ↓
               Retourner    Retourner avec
               (OK)         human_review=True
```

### 3. **Schéma de réponse** (`schemas.py`)

```python
InvoiceData {
    fournisseur: str
    numero_facture: str
    date: str (YYYY-MM-DD)
    montant_ht: float (≥ 0)
    montant_tva: float (≥ 0)
    montant_ttc: float (≥ 0)
    devise: str
    lignes_detail: [
        {
            description: str
            quantite: float (≥ 0)
            prix_unitaire: float (≥ 0)
        }
    ]
}
```

**Validation métier** : `montant_ht + montant_tva == montant_ttc` (tolérance ±0.05)

### 4. **Normalisation** (`normalization.py`)

Fonctions utilitaires pour nettoyer les données :
- `clean_amount_string()` : enlever espaces, symboles monétaires
- `string_to_float()` : convertir chaîne en float
- `normalize_date_string()` : formater dates

## 🔐 Configuration

### Fichier `config.py`

Utilise **Pydantic BaseSettings** pour charger depuis `.env` :

```python
class Settings(BaseSettings):
    openai_api_key: str                # Obligatoire
    llm_model_light: str = "gpt-4o-mini"
    llm_model_heavy: str = "gpt-4o"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )
```

## 🤖 Intégration OpenAI

### Client (`llm_client.py`)

- **Synchrone** (pas d'async pour le proto)
- **Vision** : support des images en base64 (`data:image/jpeg;base64,...`)
- **Structured Outputs** : schéma JSON strict pour garantir la conformité
- `SYSTEM_PROMPT` : vide par défaut (à personnaliser selon besoin OHADA)

### Appel API

```python
response = client.chat.completions.create(
    model=settings.llm_model_light,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": [
            {"type": "image_url", ...},
            {"type": "text", "text": "Extrais les données..."}
        ]}
    ],
    response_format={
        "type": "json_schema",
        "json_schema": _invoice_json_schema()
    }
)
```

## ⚙️ Gestion des erreurs

### Cas d'erreur et fallback

| Étape | Erreur | Action | Resultat |
|-------|--------|--------|----------|
| Étape 1 (gpt-4o-mini) | MathValidationError | Fallback → gpt-4o | Retry |
| Étape 1 (gpt-4o-mini) | JSON parsing | Fallback → gpt-4o | Retry |
| Étape 1 (gpt-4o-mini) | API error | Fallback → gpt-4o | Retry |
| Étape 2 (gpt-4o) | Tout erreur | Log error | needs_human_review=True |

### Code d'erreur métier

**`MathValidationError`** : levée si `HT + TVA ≠ TTC` (écart > 0.05)

```python
raise MathValidationError(
    "HT + TVA = 120 != TTC 125",
    montant_ht=100,
    montant_tva=20,
    montant_ttc=125,
)
```

## 🚀 Évolutions futures

- [ ] Ajouter un `SYSTEM_PROMPT` personnalisé pour zone OHADA
- [ ] Intégrer une basse de données pour historique extractions
- [ ] Ajouter un endpoint de revue/correction manuelle
- [ ] Métriques : taux de succès, latence moyenne par modèle
- [ ] Cache pour images identiques
- [ ] Support multi-pages PDF (pas juste 1ère page)
- [ ] Async complet (await sur appels API)

## 📊 Métriques de performance

**Modèles** :
- `gpt-4o-mini` : ~2 sec, ~0.2 cents/appel → **1ère tentative**
- `gpt-4o` : ~5 sec, ~1.5 cents/appel → **fallback**

**Pipeline** :
- Succès immédiat : ~2-3 sec
- Fallback nécessaire : ~7-8 sec
- Revue manuelle : ∞ (attente utilisateur)

## 🔗 Dépendances clés

| Package | Rôle |
|---------|------|
| `fastapi` | Framework API REST |
| `pydantic` | Validation de schémas |
| `openai` | Client Vision-Language |
| `pdf2image` | Conversion PDF → image |
| `pillow` | Manipulation d'images |
| `python-multipart` | Upload fichiers |
| `uvicorn` | Serveur ASGI |
