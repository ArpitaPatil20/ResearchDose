"""
ResearchDose — Core Application Configuration.
Manages application settings, filesystem paths, dataset versions, and scientific safety disclaimers.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Metadata
    APP_NAME: str = "ResearchDose — Scientific Dose Conversion & Research Platform"
    APP_VERSION: str = "1.0.0"
    CALCULATION_ENGINE_VERSION: str = "1.0.0"
    DATASET_VERSION: str = "2025.1"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Server Defaults
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    APP_DIR: Path = BASE_DIR / "app"
    DATA_DIR: Path = APP_DIR / "data"
    SPECIES_DATA_FILE: Path = DATA_DIR / "species.json"
    REFERENCES_DATA_FILE: Path = DATA_DIR / "references.json"
    EXPORTS_DIR: Path = BASE_DIR / "exports"

    # Database
    DATABASE_URL: str = "sqlite:///./researchdose.db"

    # Scientific Precision & Rules
    DEFAULT_DECIMAL_PLACES: int = 4
    MAX_DECIMAL_PLACES: int = 6

    # Mandatory Scientific Disclaimer
    SCIENTIFIC_DISCLAIMER: str = (
        "ResearchDose is a scientific calculation and educational aid for preclinical research "
        "and pharmacological experimental design. Interspecies dose conversion via Body Surface "
        "Area (BSA) normalization (Km scaling) provides a mathematical estimate of equivalent "
        "systemic exposure based on allometric metabolic scaling. It DOES NOT establish clinical safety, "
        "efficacy, or human starting doses. Regulatory determination of a Maximum Recommended Starting "
        "Dose (MRSD) in clinical trials requires determination of the No Observed Adverse Effect Level "
        "(NOAEL), species sensitivity comparison, and application of safety margins (typically >= 10-fold), "
        "in strict accordance with FDA CDER (2005) or ICH S9 guidance."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
