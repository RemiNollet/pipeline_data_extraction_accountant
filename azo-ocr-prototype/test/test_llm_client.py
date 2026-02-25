"""
Tests unitaires pour le client LLM (llm_client.py).

Dans un micro-service complet en production, on ajouterait ici les tests unitaires
de l'intégration OpenAI :

Exemples de tests à implémenter :
- Mocker les appels API OpenAI (utiliser unittest.mock ou pytest-mock)
- Tester que le client transforme correctement les images en base64
- Vérifier que le schéma JSON est correct et conforme à InvoiceData
- Tester la gestion des erreurs de l'API (timeouts, limites de taux, etc.)
- Vérifier que SYSTEM_PROMPT est bien utilisé
- Tester le parsing des réponses structurées
"""

import pytest

# from unittest.mock import patch, MagicMock
# from app.services.llm_client import extract_invoice_from_image, _invoice_json_schema


# TODO: Implémenter les tests
# @patch("app.services.llm_client.OpenAI")
# def test_extract_invoice_returns_valid_schema(mock_openai):
#     """Test que la réponse du LLM respecte le schéma InvoiceData."""
#     # Setup mock
#     mock_response = MagicMock()
#     mock_response.choices[0].message.content = json.dumps({
#         "fournisseur": "Test",
#         "numero_facture": "F001",
#         # ... autres champs
#     })
#     mock_openai.return_value.chat.completions.create.return_value = mock_response
#
#     # Test
#     result = extract_invoice_from_image("base64_data", model="gpt-4o-mini")
#     assert result.fournisseur == "Test"


# def test_invoice_json_schema_is_valid():
#     """Test que le schéma JSON généré est valide."""
#     schema = _invoice_json_schema()
#     assert schema["name"] == "invoice_data"
#     assert schema["strict"] is True
#     assert "properties" in schema["schema"]
