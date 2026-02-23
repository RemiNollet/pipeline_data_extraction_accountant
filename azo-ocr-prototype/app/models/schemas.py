"""
Schémas Pydantic pour les entrées/sorties de l'API et la réponse structurée du LLM.
"""

from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.constants import MONTANT_TOLERANCE, MathValidationError


class LigneDetail(BaseModel):
    """Une ligne de détail d'une facture (article ou service)."""

    description: str = Field(..., description="Libellé de la ligne")
    quantite: float = Field(..., ge=0, description="Quantité")
    prix_unitaire: float = Field(..., ge=0, description="Prix unitaire")
    montant_ligne: float = Field(None, ge=0, description="Montant total de la ligne")


class InvoiceData(BaseModel):
    """
    Données extraites d'une facture OHADA.
    Utilisé comme schéma de réponse structurée du LLM et pour la validation métier.
    """

    fournisseur: str = Field(..., description="Nom du fournisseur / émetteur")
    numero_facture: str = Field(..., description="Numéro de la facture")
    date: str = Field(..., description="Date de la facture au format YYYY-MM-DD")
    montant_ht: float = Field(..., ge=0, description="Montant hors taxes")
    montant_tva: float = Field(..., ge=0, description="Montant de la TVA")
    montant_ttc: float = Field(..., ge=0, description="Montant toutes taxes comprises")
    devise: str = Field(..., description="Code ou symbole de la devise (ex: XAF, FCFA)")
    lignes_detail: list[LigneDetail] = Field(
        default_factory=list,
        description="Liste des lignes de détail de la facture",
    )
    ifu_fournisseur: Optional[str] = Field(None, description="Numéro IFU du fournisseur (zone OHADA)")
    code_mecef: Optional[str] = Field(None, description="Code MECeF/DGI (zone OHADA, ex: Bénin)")
    confiance: Optional[float] = Field(None, ge=0, le=1, description="Score de confiance de l'extraction (0.0-1.0)")

    @model_validator(mode="after")
    def check_ht_tva_ttc(self) -> "InvoiceData":
        """Vérifie que montant_ht + montant_tva == montant_ttc (tolérance 0.05)."""
        somme = self.montant_ht + self.montant_tva
        ecart = abs(somme - self.montant_ttc)
        if ecart > MONTANT_TOLERANCE:
            raise MathValidationError(
                f"HT + TVA = {somme:.2f} != TTC {self.montant_ttc} (écart {ecart:.2f})",
                self.montant_ht,
                self.montant_tva,
                self.montant_ttc,
            )
        return self
