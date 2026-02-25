"""
Tests unitaires pour le module de normalisation (normalization.py).

Dans un micro-service complet en production, on ajouterait ici les tests unitaires
des fonctions de nettoyage et normalisation : clean_amount_string(), string_to_float(),
normalize_date_string(), etc.

Exemple de tests à implémenter :
- Vérifier que les symboles monétaires (FCFA, F, etc.) sont bien supprimés
- Tester les espaces et caractères spéciaux
- Valider les conversions float
- Vérifier les dates au format YYYY-MM-DD
"""

import pytest

# from app.services.normalization import clean_amount_string, string_to_float


# TODO: Implémenter les tests
# @pytest.mark.parametrize(
#     "input_str, expected",
#     [
#         ("1 000 FCFA", "1000"),
#         ("100.50 F", "100.50"),
#         ("50,00 XAF", "50.00"),
#     ],
# )
# def test_clean_amount_string(input_str, expected):
#     assert clean_amount_string(input_str) == expected
