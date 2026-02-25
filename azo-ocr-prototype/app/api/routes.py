"""
Routes API pour l'extraction de données facture.
"""

import base64
import csv
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pdf2image import convert_from_bytes
from pydantic import BaseModel, Field

from app.services.ocr_pipeline import run_extraction_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["extract"])


# Types MIME acceptés
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_PDF_TYPE = "application/pdf"


def _file_to_image_base64(content: bytes, content_type: str) -> str:
    """
    Convertit le contenu du fichier en image base64.
    Si PDF, prend la première page uniquement.
    """
    if content_type == ALLOWED_PDF_TYPE:
        images = convert_from_bytes(content, first_page=1, last_page=1)
        if not images:
            raise HTTPException(status_code=400, detail="Impossible de convertir le PDF en image.")
        buffer = io.BytesIO()
        images[0].save(buffer, format="PNG")
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("ascii")
    # Déjà une image
    return base64.b64encode(content).decode("ascii")


class ExtractResponse(BaseModel):
    """Réponse de l'endpoint /extract."""

    data: dict[str, Any] | None = Field(None, description="Données facture extraites (null si échec + revue manuelle)")
    needs_human_review: bool = Field(False, description="True si extraction incertaine ou échouée")
    error_message: str | None = Field(None, description="Message d'erreur lorsque needs_human_review=True")


@router.post(
    "/extract",
    response_model=ExtractResponse,
    summary="Extraire les données d'une facture",
    description="Accepte une image ou un PDF (première page), renvoie les données structurées (fournisseur, montants, lignes).",
)
async def extract(file: UploadFile = File(...)) -> ExtractResponse:
    """
    Reçoit un fichier image ou PDF, le convertit en image (1ère page pour PDF),
    lance le pipeline d'extraction (LLM + validation + fallback) et retourne le résultat.
    """
    content_type = file.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES and content_type != ALLOWED_PDF_TYPE:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non supporté. Attendu: image (JPEG, PNG, WebP, GIF) ou PDF, reçu: {content_type}",
        )

    try:
        body = await file.read()
    except Exception as e:
        logger.exception("Erreur lecture fichier uploadé")
        raise HTTPException(status_code=400, detail="Impossible de lire le fichier.") from e

    if not body:
        raise HTTPException(status_code=400, detail="Fichier vide.")

    try:
        image_base64 = _file_to_image_base64(body, content_type)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Conversion fichier -> image échouée")
        raise HTTPException(status_code=400, detail="Conversion du fichier en image impossible.") from e

    result = run_extraction_pipeline(image_base64)

    response_data = None
    if result.data is not None:
        response_data = result.data.model_dump()
        _save_extraction_to_csv(file.filename or "unknown", response_data, result.needs_human_review)
    else:
        _save_extraction_to_csv(file.filename or "unknown", None, True, error_message=result.error_message)

    if result.data is not None:
        return ExtractResponse(
            data=response_data,
            needs_human_review=result.needs_human_review,
            error_message=result.error_message,
        )
    return ExtractResponse(
        data=None,
        needs_human_review=True,
        error_message=result.error_message,
    )


def _save_extraction_to_csv(
    filename: str,
    data: dict[str, Any] | None,
    needs_human_review: bool,
    error_message: str | None = None,
) -> None:
    """Sauvegarde le résultat d'extraction dans un CSV dans le dossier resultats/."""
    results_dir = Path(__file__).parent.parent.parent / "resultats"
    results_dir.mkdir(exist_ok=True)

    csv_file = results_dir / "extractions.csv"
    file_exists = csv_file.exists()

    timestamp = datetime.now().isoformat()

    # Préparer les données à écrire
    row = {
        "timestamp": timestamp,
        "fichier_source": filename,
        "statut": "succès" if data is not None else "erreur",
        "needs_human_review": needs_human_review,
        "fournisseur": data.get("fournisseur", "") if data else "",
        "numero_facture": data.get("numero_facture", "") if data else "",
        "date": data.get("date", "") if data else "",
        "montant_ht": data.get("montant_ht", "") if data else "",
        "montant_tva": data.get("montant_tva", "") if data else "",
        "montant_ttc": data.get("montant_ttc", "") if data else "",
        "devise": data.get("devise", "") if data else "",
        "ifu_fournisseur": data.get("ifu_fournisseur", "") if data else "",
        "code_mecef": data.get("code_mecef", "") if data else "",
        "confiance": data.get("confiance", "") if data else "",
        "nombre_lignes": len(data.get("lignes_detail", [])) if data else 0,
        "error_message": error_message or "",
    }

    with open(csv_file, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    logger.info("Résultat extraction sauvegardé dans %s", csv_file)
