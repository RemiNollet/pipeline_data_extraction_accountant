"""
Application FastAPI : microservice d'extraction de données facture (zone OHADA).
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def startup():
    """Vérification de la config au démarrage."""
    try:
        get_settings()
        logger.info("Configuration chargée (OPENAI_API_KEY présente).")
    except Exception as e:
        logger.warning("Configuration incomplète au démarrage: %s", e)


app = FastAPI(
    title="AZO OCR Prototype",
    description="Extraction de données facture OHADA (PDF/images) via Vision-Language Model.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_event_handler("startup", startup)
app.include_router(router)


@app.get("/health")
def health():
    """Endpoint de santé pour vérifier que le service répond."""
    return {"status": "ok"}
