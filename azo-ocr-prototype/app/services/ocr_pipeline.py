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
    1. Extraction avec gpt-4o-mini.
    2. Validation Pydantic (dont HT + TVA == TTC).
    3. En cas d'échec : log warning, relance avec gpt-4o.
    4. Si le modèle lourd échoue encore : retourne needs_human_review=True avec données partielles ou re-raise.
    """
    settings = settings or get_settings()

    # Étape 1 : modèle léger
    try:
        data = extract_invoice_from_image(
            image_base64,
            model=settings.llm_model_light,
            settings=settings,
        )
        return ExtractionResult(data=data, needs_human_review=False)
    except (MathValidationError, ValueError) as e:
        logger.warning(
            "Validation ou parsing échoué avec %s: %s. Fallback vers %s.",
            settings.llm_model_light,
            e,
            settings.llm_model_heavy,
        )
    except Exception as e:
        logger.warning(
            "Erreur inattendue avec %s: %s. Fallback vers %s.",
            settings.llm_model_light,
            e,
            settings.llm_model_heavy,
        )

    # Étape 2 : fallback modèle lourd
    try:
        data = extract_invoice_from_image(
            image_base64,
            model=settings.llm_model_heavy,
            settings=settings,
        )
        return ExtractionResult(data=data, needs_human_review=False)
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
