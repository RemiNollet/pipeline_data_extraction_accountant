"""
Logique de validation métier pour les données de facture.
"""

from app.models.schemas import InvoiceData
from app.models.constants import MONTANT_TOLERANCE, MathValidationError

def validate_invoice_math(data: InvoiceData) -> None:
    """
    Vérifie que montant_ht + montant_tva == montant_ttc dans la tolérance autorisée.
    Lève MathValidationError si la règle n'est pas respectée.
    """

    somme = data.montant_ht + data.montant_tva
    ecart = abs(somme - data.montant_ttc)
    if ecart > MONTANT_TOLERANCE:
        raise MathValidationError(
            f"Règle métier non respectée: HT ({data.montant_ht}) + TVA ({data.montant_tva}) "
            f"= {somme:.2f} != TTC ({data.montant_ttc}). Écart: {ecart:.2f}",
            data.montant_ht,
            data.montant_tva,
            data.montant_ttc,
        )


