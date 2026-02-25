"""
Orchestration du pipeline d'extraction : appel LLM, validation Pydantic, fallback en cas d'échec.
Étape 1 : gpt-4o-mini → validation.
Étape 2 (fallback) : si échec (MathValidationError ou parsing), relance avec gpt-4o.
Retourne un résultat avec flag needs_human_review si le modèle lourd échoue aussi.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from app.core.config import Settings, get_settings
from app.models.schemas import InvoiceData
from app.models.constants import MathValidationError
from app.services.llm_client import extract_invoice_from_image

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Résultat du pipeline d'extraction avec indicateur de revue manuelle."""

    data: Optional[InvoiceData] = None
    needs_human_review: bool = False
    """True si le fallback gpt-4o a aussi échoué ; data peut être None."""
    error_message: Optional[str] = None
    """Message d'erreur lorsque needs_human_review=True et data est None."""


def run_extraction_pipeline(
    image_base64: str,
    *,
    settings: Optional[Settings] = None,
) -> ExtractionResult:
    """
    Exécute le pipeline en cascading :
    1. Extraction avec gpt-4o-mini (tentative 1).
    2. Validation Pydantic (dont HT + TVA == TTC).
    3. En cas d'échec : retry avec gpt-4o-mini (tentative 2).
    4. Si toujours échoué : fallback vers gpt-4o (modèle lourd).
    5. Si gpt-4o échoue aussi : retourne needs_human_review=True avec données partielles.
    """
    settings = settings or get_settings()

    # Étape 1 : modèle léger - Tentative 1
    try:
        data = extract_invoice_from_image(
            image_base64,
            model=settings.llm_model_light,
            settings=settings,
        )
        logger.info("Extraction réussie avec %s (tentative 1)", settings.llm_model_light)
        
        # Cas spécial : TVA = 0 (probable assurance, notaire, structure spéciale)
        needs_review = data.montant_tva == 0.0
        if needs_review:
            logger.info("TVA = 0.0 détectée (assurance/notaire/cas spécial). Revue manuelle recommandée.")
        
        return ExtractionResult(data=data, needs_human_review=needs_review)
    except (MathValidationError, ValueError) as e:
        logger.warning(
            "Validation ou parsing échoué avec %s (tentative 1): %s. Retry...",
            settings.llm_model_light,
            e,
        )
    except Exception as e:
        logger.warning(
            "Erreur inattendue avec %s (tentative 1): %s. Retry...",
            settings.llm_model_light,
            e,
        )

    # Étape 2 : modèle léger - Tentative 2 (retry)
    try:
        data = extract_invoice_from_image(
            image_base64,
            model=settings.llm_model_light,
            settings=settings,
        )
        logger.info("Extraction réussie avec %s (tentative 2/retry)", settings.llm_model_light)
        
        # Cas spécial : TVA = 0 (probable assurance, notaire, structure spéciale)
        needs_review = data.montant_tva == 0.0
        if needs_review:
            logger.info("TVA = 0.0 détectée (assurance/notaire/cas spécial). Revue manuelle recommandée.")
        
        return ExtractionResult(data=data, needs_human_review=needs_review)
    except (MathValidationError, ValueError) as e:
        logger.warning(
            "Validation ou parsing échoué avec %s (tentative 2): %s. Fallback vers %s.",
            settings.llm_model_light,
            e,
            settings.llm_model_heavy,
        )
    except Exception as e:
        logger.warning(
            "Erreur inattendue avec %s (tentative 2): %s. Fallback vers %s.",
            settings.llm_model_light,
            e,
            settings.llm_model_heavy,
        )

    # Étape 3 : fallback modèle lourd
    try:
        data = extract_invoice_from_image(
            image_base64,
            model=settings.llm_model_heavy,
            settings=settings,
        )
        logger.info("Extraction réussie avec %s (fallback)", settings.llm_model_heavy)
        
        # Cas spécial : TVA = 0 (probable assurance, notaire, structure spéciale)
        needs_review = data.montant_tva == 0.0
        if needs_review:
            logger.info("TVA = 0.0 détectée (assurance/notaire/cas spécial). Revue manuelle recommandée.")
        
        return ExtractionResult(data=data, needs_human_review=needs_review)
    except (MathValidationError, ValueError) as e:
        logger.warning("Fallback %s: validation/parsing échoué: %s", settings.llm_model_heavy, e)
        return ExtractionResult(
            data=None,
            needs_human_review=True,
            error_message=str(e),
        )
    except Exception as e:
        logger.error("Fallback %s échoué: %s. Nécessite revue manuelle.", settings.llm_model_heavy, e)
        return ExtractionResult(
            data=None,
            needs_human_review=True,
            error_message=str(e),
        )
