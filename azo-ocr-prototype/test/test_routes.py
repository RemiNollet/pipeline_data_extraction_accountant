"""
Tests unitaires pour les routes API (routes.py).

Dans un micro-service complet en production, on ajouterait ici les tests unitaires
des endpoints :

Exemples de tests à implémenter :
- Tester le endpoint POST /api/v1/extract avec un vrai fichier
- Vérifier que le CSV resultats/extractions.csv est créé et rempli
- Tester les erreurs : fichier vide, type MIME invalide, PDF vide
- Vérifier les réponses HTTP (200, 400, 500)
- Tester la conversion PDF → image (première page)
- Vérifier que les données en CSV matchent la réponse JSON

Utiliser pytest avec TestClient de FastAPI pour les tests d'intégration.
"""

import pytest

# from fastapi.testclient import TestClient
# from app.main import app


# client = TestClient(app)


# TODO: Implémenter les tests
# def test_extract_endpoint_success(tmp_path):
#     """Test que le endpoint /extract accepte un fichier et retourne 200."""
#     # Créer un fichier PDF de test
#     test_file = tmp_path / "test.pdf"
#     test_file.write_bytes(b"fake pdf content")
#
#     with open(test_file, "rb") as f:
#         response = client.post("/api/v1/extract", files={"file": f})
#
#     assert response.status_code == 200


# def test_extract_endpoint_rejects_empty_file():
#     """Test que le endpoint rejette un fichier vide."""
#     response = client.post("/api/v1/extract", files={"file": ("empty.pdf", b"")})
#     assert response.status_code == 400
#     assert "vide" in response.json()["detail"].lower()


# def test_extract_endpoint_invalid_mime_type():
#     """Test que le endpoint rejette les types MIME non supportés."""
#     response = client.post(
#         "/api/v1/extract",
#         files={"file": ("test.txt", b"hello")},
#     )
#     assert response.status_code == 400
#     assert "non supporté" in response.json()["detail"].lower()
