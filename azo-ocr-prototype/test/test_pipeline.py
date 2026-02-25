"""
Script de test du pipeline d'extraction sur les factures du dossier sample_invoices/.
Lance l'endpoint /api/v1/extract pour chaque fichier et sauvegarde les résultats dans resultats/extractions.csv
"""

import os
import sys
from pathlib import Path

import requests

# Ajouter le parent du dossier test au PYTHONPATH pour pouvoir importer app
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SAMPLE_INVOICES_DIR = PROJECT_ROOT / "sample_invoices"
API_ENDPOINT = "http://127.0.0.1:8000/api/v1/extract"


def test_extract_all_invoices():
    """
    Parcourt tous les fichiers du dossier sample_invoices/ et appelle l'endpoint d'extraction.
    Les résultats sont automatiquement sauvegardés dans resultats/extractions.csv par le serveur.
    """
    if not SAMPLE_INVOICES_DIR.exists():
        print(f"Dossier sample_invoices/ introuvable à : {SAMPLE_INVOICES_DIR}")
        print("Crée le dossier et ajoute des PDF de factures pour tester.")
        return

    files = list(SAMPLE_INVOICES_DIR.glob("*.*"))
    if not files:
        print(f"Aucun fichier trouvé dans {SAMPLE_INVOICES_DIR}")
        return

    print(f"Traitement de {len(files)} fichier(s) du dossier sample_invoices/\n")

    for file_path in files:
        if file_path.is_file():
            print(f"Traitement : {file_path.name}")

            try:
                with open(file_path, "rb") as f:
                    files_payload = {"file": (file_path.name, f, "application/pdf")}
                    response = requests.post(API_ENDPOINT, files=files_payload, timeout=60)

                if response.status_code == 200:
                    result = response.json()
                    needs_review = result.get("needs_human_review", False)
                    status = "REVUE MANUELLE" if needs_review else "OK"
                    print(f"   {status}")
                    if result.get("data"):
                        print(f"      Fournisseur: {result['data'].get('fournisseur', 'N/A')}")
                        print(f"      Montant TTC: {result['data'].get('montant_ttc', 'N/A')}")
                else:
                    print(f"rreur API ({response.status_code}): {response.text[:100]}")

            except Exception as e:
                print(f"Erreur : {e}")

    print(f"\nTraitement terminé. Les résultats sont dans resultats/extractions.csv")


if __name__ == "__main__":
    print("=" * 60)
    print("AZO OCR Prototype - Test du Pipeline d'Extraction")
    print("=" * 60 + "\n")

    test_extract_all_invoices()
