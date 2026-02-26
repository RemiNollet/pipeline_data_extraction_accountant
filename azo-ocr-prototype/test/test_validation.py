"""
Tests unitaires pour le module de validation (validation.py, schemas.py).

Dans un micro-service complet en production, on ajouterait ici les tests unitaires
de la logique métier OHADA :

Exemples de tests à implémenter :
- Vérifier que montant_ht + montant_tva == montant_ttc (avec tolérance 0.05)
- Tester MathValidationError lorsque la règle n'est pas respectée
- Valider les formats de date (YYYY-MM-DD)
- Vérifier les champs obligatoires (fournisseur, numero_facture, etc.)
- Tester les champs optionnels OHADA (ifu_fournisseur, code_mecef, confiance)
- Vérifier que les montants sont >= 0
"""
