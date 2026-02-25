"""
Client OpenAI pour l'extraction structurée de données facture via Vision.
Utilise les Structured Outputs (response_format) pour obtenir du JSON conforme au schéma.
"""

import base64
import json
import logging
from pathlib import Path
from typing import Optional

from openai import OpenAI

from app.core.config import Settings, get_settings
from app.models.schemas import InvoiceData

logger = logging.getLogger(__name__)


def _load_system_prompt(prompt_version: str = "v1") -> str:
    """
    Charge le prompt système depuis un fichier.
    Permet de gérer plusieurs versions de prompts (v1, v2, v3, etc.)
    
    Args:
        prompt_version: Version du prompt (ex: "v1", "v2"). Défaut: "v1"
    
    Returns:
        Contenu du fichier prompt, ou prompt par défaut si fichier non trouvé.
    """
    prompt_file = Path(__file__).parent.parent / "prompt" / f"prompt_{prompt_version}.txt"
    
    if prompt_file.exists():
        try:
            content = prompt_file.read_text(encoding="utf-8").strip()
            logger.info("Prompt système chargé depuis %s", prompt_file)
            return content
        except Exception as e:
            logger.warning("Erreur lecture fichier prompt %s: %s. Utilisation prompt par défaut.", prompt_file, e)
    
    # Prompt par défaut si fichier non trouvé
    return "Extrait les données de cette facture au format JSON demandé."


# Charge le prompt système depuis le fichier (version v1 par défaut)
SYSTEM_PROMPT = _load_system_prompt("v1")


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
    # Nettoyage robuste : enlever markdown, commentaires, espaces
    raw = _clean_json_response(raw)

    data = json.loads(raw)
    return InvoiceData.model_validate(data)


def _clean_json_response(response: str) -> str:
    """
    Nettoie la réponse du LLM pour extraire du JSON valide.
    Gère les cas courants :
    - ```json ... ``` (markdown)
    - Texte avant/après le JSON
    - Commentaires // ou #
    - Espaces et caractères invisibles
    
    Args:
        response: Réponse brute du LLM
    
    Returns:
        Chaîne JSON valide et nettoyée
    """
    # Enlever markdown ```json ... ```
    if "```json" in response:
        start = response.find("```json") + 7  # Longueur de "```json"
        end = response.find("```", start)
        if end != -1:
            response = response[start:end]
    elif "```" in response:
        # Cas générique ```...```
        start = response.find("```") + 3
        end = response.find("```", start)
        if end != -1:
            response = response[start:end]
    
    # Chercher le JSON entre { et }
    response = response.strip()
    start = response.find("{")
    end = response.rfind("}")
    if start != -1 and end != -1 and end > start:
        response = response[start : end + 1]
    
    response = response.strip()
    return response


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
