MONTANT_TOLERANCE = 0.05

class MathValidationError(ValueError):
    """Erreur levée lorsque la règle métier HT + TVA == TTC n'est pas respectée."""

    def __init__(self, message: str, montant_ht: float, montant_tva: float, montant_ttc: float):
        self.montant_ht = montant_ht
        self.montant_tva = montant_tva
        self.montant_ttc = montant_ttc
        super().__init__(message)
