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
