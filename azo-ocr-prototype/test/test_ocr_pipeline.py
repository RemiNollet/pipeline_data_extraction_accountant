"""
Tests unitaires pour le pipeline d'orchestration (ocr_pipeline.py).

Dans un micro-service complet en production, on ajouterait ici les tests unitaires
de la logique de cascading et fallback :

Exemples de tests à implémenter :
- Tester que le pipeline appelle d'abord gpt-4o-mini
- Vérifier que le fallback vers gpt-4o se déclenche en cas d'erreur de validation
- Tester que needs_human_review=True si le modèle lourd échoue aussi
- Mocker les appels LLM pour éviter les appels réels à OpenAI
- Tester le logging des fallbacks (warnings, errors)
- Vérifier que la tolérance HT+TVA==TTC fonctionne correctement
"""

import pytest

# from unittest.mock import patch, MagicMock
# from app.services.ocr_pipeline import run_extraction_pipeline, ExtractionResult
# from app.models.constants import MathValidationError


# TODO: Implémenter les tests
# @patch("app.services.ocr_pipeline.extract_invoice_from_image")
# def test_pipeline_success_first_try(mock_extract):
#     """Test que le pipeline retourne un résultat si gpt-4o-mini réussit."""
#     mock_invoice = MagicMock()
#     mock_extract.return_value = mock_invoice
#
#     result = run_extraction_pipeline("base64_data")
#     assert result.data is not None
#     assert result.needs_human_review is False


# @patch("app.services.ocr_pipeline.extract_invoice_from_image")
# def test_pipeline_fallback_on_validation_error(mock_extract):
#     """Test que le pipeline bascule à gpt-4o si gpt-4o-mini échoue à la validation."""
#     # Premier appel lève MathValidationError, deuxième réussit
#     mock_extract.side_effect = [
#         MathValidationError("HT+TVA != TTC", 100, 20, 100),
#         MagicMock(),
#     ]
#
#     result = run_extraction_pipeline("base64_data")
#     assert mock_extract.call_count == 2  # Devrait être appelé deux fois
