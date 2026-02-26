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
