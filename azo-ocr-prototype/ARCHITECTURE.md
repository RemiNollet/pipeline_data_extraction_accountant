# Architecture du Microservice AZO OCR

## Vue d'ensemble

Le microservice orchestre un pipeline d'extraction de données facture via Vision-Language Model avec fallback cascading pour la fiabilité.

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
        │                                                  │
        │  ┌────────────────────────────────────────────┐  │
        │  │ Étape 1: gpt-4o-mini (Tentative 1)         │  │
        │  │ • Appel API OpenAI avec image              │  │
        │  │ • Réponse structurée (JSON)                │  │ 
        │  │ • Validation Pydantic                      │  │
        │  │   └─ Montants: HT + TVA == TTC (±0.05)     │  │
        │  └──────────────┬─────────────────────────────┘  │
        │                 │                                │
        │        ┌────────▼──────────┐                     │
        │        │ Succès?           │ Échec?              │
        │        └────────┬──────────┘                     │
        │                 │                                │
        │                 │  ┌──────────────────────────┐  │
        │                 │  │ Étape 2: gpt-4o-mini     │  │
        │                 │  │ (Tentative 2/Retry)      │  │
        │                 │  └──────┬────────────────── ┘  │
        │                 │         │                      │
        │        ┌────────▼──────────┐                     │
        │        │ Succès?           │ Échec?              │
        │        └────────┬──────────┘                     │
        │                 │                                │
        │                 │  ┌──────────────────────────┐  │
        │                 │  │ Étape 3: gpt-4o          │  │
        │                 │  │ (Fallback/Modèle lourd)  │  │
        │                 │  └──────┬────────────────── ┘  │
        │                 │         │                      │
        │                 └─────────┤ Succès?              │
        │                           │                      │
        │                    ┌──────▼────────────┐         │
        │                    │ Échec aussi?      │         │
        │                    │ → human_review    │         │
        │                    │   = true          │         │
        │                    └───────────────────┘         │
        └───────────────────────┬──────────────────────────┘
                                │
                                ▼
        ┌──────────────────────────────────────────────┐
        │  Normalisation des données (normalization)   │
        │  • Nettoyage des montants                    │
        │  • Conversion format décimal                 │ 
        │  • Normalisation dates                       │
        └──────────────────────┬───────────────────────┘
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
        │  {                                           │
        │    "data": {...} | null,                     │
        │    "needs_human_review": bool,               │
        │    "error_message": str | null               │
        │  }                                           │
        └──────────────────────┬───────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │  Stockage des résultats (resultats/csv)      │
        │  • Fichier: extractions.csv                  │
        │  • Timestamp, statut, données, erreurs       │
        └──────────────────────────────────────────────┘
```

## Structure des fichiers

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
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_client.py                # Client OpenAI + Structured Outputs
│   │   ├── ocr_pipeline.py              # Orchestration et cascading
│   │   └── normalization.py             # Nettoyage de données
│   │
│   └── prompt/
│       ├── prompt_v1.txt                # Prompt système pour extraction (v1)
│       └── prompt_v2.txt                # Prompt système alternatif (v2+)
│
├── test/
│   ├── __init__.py
│   ├── test_pipeline.py                 # Test complet du pipeline
│   ├── test_normalization.py            # Tests unitaires normalisation
│   ├── test_validation.py               # Tests unitaires validation
│   ├── test_llm_client.py               # Tests unitaires LLM client
│   ├── test_ocr_pipeline.py             # Tests unitaires pipeline OCR
│   └── test_routes.py                   # Tests unitaires API
│
├── sample_invoices/                     # Dossier de factures de test
│   ├── Facture_MEDEO_AFRICA_MOIS_DE_FEVRIER.pdf
│   ├── Facture_MEDEO_AFRICA_MOIS_DE_MARS.pdf
│   └── [autres factures de test]
│
├── resultats/                           # Résultats des extractions
│   └── extractions.csv                  # CSV avec toutes les extractions
│
├── requirements.txt                     # Dépendances Python
├── README.md                             # Guide d'utilisation
├── ARCHITECTURE.md                      # Ce fichier
└── .env                                  # Configuration (non versionné)
```

## Flux de traitement détaillé

### 1. Réception du fichier (routes.py)

```python
POST /api/v1/extract
└─ UploadFile (image JPEG/PNG/WebP/GIF ou PDF)
```

- Validation du type MIME
- Lecture du fichier
- Conversion en image base64 (PDF: 1ère page uniquement via `pdf2image`)

### 2. Pipeline d'extraction (ocr_pipeline.py)

**Étape 1 : gpt-4o-mini (Tentative 1)**
```
image_base64 → gpt-4o-mini → JSON → Pydantic validation
                              ↓
                        Validation OK?
                        /            \
                      OUI            NON
                       ↓               ↓
                    Retourner      Log warning
                    (OK)           Retry
```

**Étape 2 : gpt-4o-mini (Tentative 2/Retry)**
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

**Étape 3 : gpt-4o (Fallback - Modèle lourd)**
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

### 3. Schéma de réponse (schemas.py)

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

### 4. Normalisation (normalization.py)

Fonctions utilitaires pour nettoyer les données :
- `clean_amount_string()` : enlever espaces, symboles monétaires
- `string_to_float()` : convertir chaîne en float
- `normalize_date_string()` : formater dates

## Configuration

### Fichier config.py

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

## Intégration OpenAI

### Client (llm_client.py)

- **Synchrone** (pas d'async pour le proto)
- **Vision** : support des images en base64 (`data:image/jpeg;base64,...`)
- **Structured Outputs** : schéma JSON strict pour garantir la conformité
- `SYSTEM_PROMPT` : rempli avec directives OHADA (IFU, MECeF, TVA, etc.)

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

## Gestion des erreurs

### Cas d'erreur et fallback

| Étape | Erreur | Action | Resultat |
|-------|--------|--------|----------|
| Étape 1 (gpt-4o-mini) | MathValidationError | Fallback → gpt-4o | Retry |
| Étape 1 (gpt-4o-mini) | JSON parsing | Fallback → gpt-4o | Retry |
| Étape 1 (gpt-4o-mini) | API error | Fallback → gpt-4o | Retry |
| Étape 2 (gpt-4o) | Tout erreur | Log error | needs_human_review=True |

### Code d'erreur métier

**MathValidationError** : levée si HT + TVA ≠ TTC (écart > 0.05)

```python
raise MathValidationError(
    "HT + TVA = 120 != TTC 125",
    montant_ht=100,
    montant_tva=20,
    montant_ttc=125,
)
```

## Évolutions futures

- [ ] Optimisation du prompt en fonctions des resultats
- [ ] Intégrer une basse de données pour historique extractions
- [ ] Ajouter un endpoint de revue/correction manuelle
- [ ] Création d'un golden dataset pour l'evaluation et l'amelioration continue
- [ ] Métriques : taux de succès, latence moyenne par modèle, accuracy champs par champs, metriques de couts...
- [ ] Tester une plus grande diversité de models et fournisseurs, ou un intégrer un model Mistral local si RGPD prioritaire.
- [ ] Cache pour factures identiques
- [ ] Support multi-pages PDF (pas juste 1ère page)
- [ ] Pipeline totalement Asynchrone avec plusieurs workers pour reduire la latence.

## Métriques de performance

**Modèles** :
- `gpt-4o-mini` : ~2 sec, ~0.2 cents/appel → **1ère tentative**
- `gpt-4o` : ~5 sec, ~1.5 cents/appel → **fallback**

**Pipeline** :
- Succès immédiat : ~2-3 sec
- Fallback nécessaire : ~7-8 sec
- Revue manuelle : ∞ (attente utilisateur)

## Dépendances clés

| Package | Rôle |
|---------|------|
| `fastapi` | Framework API REST |
| `pydantic` | Validation de schémas |
| `openai` | Client Vision-Language |
| `pdf2image` | Conversion PDF → image |
| `pillow` | Manipulation d'images |
| `python-multipart` | Upload fichiers |
| `uvicorn` | Serveur ASGI |
