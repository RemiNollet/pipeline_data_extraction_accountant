"""
Client OpenAI pour l'extraction structurée de données facture via Vision.
Utilise les Structured Outputs (response_format) pour obtenir du JSON conforme au schéma.
"""

import base64
import json
import logging
from typing import Optional

from openai import OpenAI

from app.core.config import Settings, get_settings
from app.models.schemas import InvoiceData

logger = logging.getLogger(__name__)

# Instruction système pour le LLM (spécialisée pour zone OHADA).
SYSTEM_PROMPT = """Tu es un expert comptable spécialisé dans le système OHADA et la fiscalité d'Afrique Francophone (Bénin, Togo, Côte d'Ivoire, etc.).
Ton rôle est d'extraire avec une précision chirurgicale les données de factures pour un SaaS de comptabilité.

### DIRECTIVES CRUCIALES :
1. ANALYSE SPATIALE : Les factures peuvent être des scans ou des photos. Identifie bien le bloc "Vendeur" (souvent en haut) et "Client".
2. CODES DE SÉCURITÉ : Pour les factures du Bénin, extrais impérativement le "Code MECeF/DGI" et le "NIM" si présents.
3. MONTANTS :
   - Ignore les symboles (FCFA, F.CFA, F) et les espaces. Retourne des nombres (float).
   - Si la TVA n'est pas explicitement écrite mais qu'un groupe "E-TPS" ou "A-EX" est présent, la TVA peut être de 0.
   - Attention aux factures d'assurance : la "Taxe d'enregistrement" ou les "Accessoires" ne sont pas de la TVA classique mais doivent être extraits dans les lignes de détail.
4. VALIDATION : Si tu as un doute sur un montant, préfère mettre null plutôt que d'inventer (halluciner).
5. CONFIANCE : Ajoute un score "confiance" entre 0 et 1 reflétant ta certitude globale sur l'extraction.

### CAS PARTICULIERS DÉTECTÉS :
- Factures "LICOBERRE" : Le montant TTC est marqué avec un [E]. Le groupe "E-TPS" indique souvent une exonération.
- Factures "NSIA" (Assurance) : Le "Prime TTC" est le montant total. Les taxes d'enregistrement ne sont pas de la TVA.
- Factures "Notaire VITTIN" : Bien distinguer les Émoluments (souvent HT) des Frais Déboursés."""


def extract_invoice_from_image(
    image_base64: str,
    *,
    model: str,
    settings: Optional[Settings] = None,
) -> InvoiceData:
    """
    Envoie l'image (base64) au modèle OpenAI et retourne les données facture structurées.
    Utilise le schéma InvoiceData en Structured Output ; lève en cas d'échec de l'API ou de parsing.
    """
    settings = settings or get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT or "Extrait les données de la facture au format demandé."},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    },
                    {
                        "type": "text",
                        "text": "Extrais les données de cette facture (fournisseur, numéro, date YYYY-MM-DD, montants HT/TVA/TTC, devise, lignes de détail).",
                    },
                ],
            },
        ],
        response_format={"type": "json_schema", "json_schema": _invoice_json_schema()},
    )

    choice = response.choices[0]
    if not choice.message.content:
        raise ValueError("Réponse LLM vide")

    raw = choice.message.content.strip()
    # Gestion des blocs markdown ```json ... ```
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    data = json.loads(raw)
    return InvoiceData.model_validate(data)


def _invoice_json_schema() -> dict:
    """Retourne le schéma JSON pour Structured Output aligné sur InvoiceData avec champs OHADA."""
    return {
        "name": "invoice_data",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "fournisseur": {"type": ["string", "null"]},
                "numero_facture": {"type": ["string", "null"]},
                "date": {"type": ["string", "null"]},
                "montant_ht": {"type": ["string", "null"]},
                "montant_tva": {"type": ["number", "null"]},
                "montant_ttc": {"type": ["number", "null"]},
                "devise": {"type": ["string", "null"]},
                "ifu_fournisseur": {"type": ["string", "null"]},
                "code_mecef": {"type": ["string", "null"]},
                "confiance": {"type": ["number", "null"]},
                "lignes_detail": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": ["string", "null"]},
                            "quantite": {"type": ["number", "null"]},
                            "prix_unitaire": {"type": ["number", "null"]},
                            "montant_ligne": {"type": ["number", "null"]},
                        },
                        "required": ["description", "quantite", "prix_unitaire", "montant_ligne"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": [
                "fournisseur",
                "numero_facture",
                "date",
                "montant_ht",
                "montant_tva",
                "montant_ttc",
                "devise",
                "ifu_fournisseur",
                "code_mecef",
                "confiance",
                "lignes_detail",
            ],
            "additionalProperties": False,
        },
    }
