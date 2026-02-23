"""
Fonctions utilitaires de normalisation des données extraites.
Nettoyage des chaînes (espaces, symboles) avant conversion en nombres ou dates.
Le LLM fait l'essentiel via les instructions ; cette couche assure la cohérence post-extraction.
"""

import re
from typing import Optional


def clean_amount_string(value: str) -> str:
    """
    Nettoie une chaîne représentant un montant avant conversion en float.
    Enlève espaces, caractères de milliers (espaces, virgules, points selon locale), garde le décimal.
    """
    if not value or not isinstance(value, str):
        return value
    s = value.strip()
    # Supprimer espaces et symboles monétaires courants
    s = re.sub(r"[\s\xa0]", "", s)
    s = s.replace("\u202f", "").replace(",", ".")
    # Garder uniquement chiffres, point décimal et éventuel signe
    s = re.sub(r"[^\d.\-+]", "", s)
    # Éviter plusieurs points (garder le dernier comme décimal)
    parts = s.split(".")
    if len(parts) > 2:
        s = "".join(parts[:-1]) + "." + parts[-1]
    return s.strip() or "0"


def string_to_float(value: str) -> float:
    """
    Convertit une chaîne nettoyée en float. Retourne 0.0 si vide ou invalide.
    """
    cleaned = clean_amount_string(value) if isinstance(value, str) else str(value)
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def normalize_date_string(value: str) -> Optional[str]:
    """
    Tente de normaliser une date en YYYY-MM-DD.
    Pour le proto, retourne la chaîne nettoyée (espaces en moins) ; une regex ou dateutil peut être ajoutée.
    """
    if not value or not isinstance(value, str):
        return value
    return value.strip()
