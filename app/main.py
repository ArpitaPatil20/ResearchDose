"""
ResearchDose — Scientific Dose Conversion & Research Platform
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.services.species_service import species_service
from app.services.dose_calculator import dose_calculator
from app.schemas.species import SpeciesListResponse
from app.schemas.dose import (
    DoseCalculationRequest,
    DoseCalculationResult,
    MultiSpeciesComparisonResponse,
    CohortCalculationRequest,
    CohortCalculationResult,
)

templates = Jinja2Templates(directory=str(settings.APP_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize and validate species reference dataset
    species_service.initialize()
    yield
    # Shutdown logic if needed


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "A scientifically verified preclinical dose conversion platform "
        "supporting BSA (Km) scaling, weight adjustments, and research provenance."
    ),
    lifespan=lifespan,
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory if present
if (settings.APP_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=str(settings.APP_DIR / "static")), name="static")


@app.get("/manifest.json", include_in_schema=False)
async def pwa_manifest():
    """Serves the Progressive Web App manifest."""
    manifest_path = settings.APP_DIR / "static" / "manifest.json"
    if manifest_path.exists():
        return FileResponse(manifest_path, media_type="application/manifest+json")
    raise HTTPException(status_code=404, detail="PWA manifest not found")


@app.get("/sw.js", include_in_schema=False)
async def pwa_service_worker():
    """Serves the PWA Service Worker with root scope permissions."""
    sw_path = settings.APP_DIR / "static" / "sw.js"
    if sw_path.exists():
        return FileResponse(
            sw_path,
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/"},
        )
    raise HTTPException(status_code=404, detail="Service worker not found")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serves the application favicon."""
    icon_path = settings.APP_DIR / "static" / "icons" / "favicon.ico"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/x-icon")
    raise HTTPException(status_code=404, detail="Favicon not found")


@app.get("/", tags=["UI"])
async def home(request: Request):
    """Renders the main scientific dashboard and species overview."""
    all_species = species_service.get_all_species(include_unverified=True)
    references = species_service.get_all_references()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "species_list": all_species,
            "references": references,
            "app_name": settings.APP_NAME,
            "disclaimer": settings.SCIENTIFIC_DISCLAIMER,
            "version": settings.APP_VERSION,
        },
    )


@app.get("/health", tags=["System"])
async def health_check():
    """System health check and scientific dataset status."""
    verified_count = len(species_service.get_verified_species())
    total_count = len(species_service.get_all_species(include_unverified=True))
    ref_count = len(species_service.get_all_references())

    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "calculation_engine_version": settings.CALCULATION_ENGINE_VERSION,
        "dataset_version": settings.DATASET_VERSION,
        "verified_species_count": verified_count,
        "total_species_count": total_count,
        "scientific_references_count": ref_count,
        "scientific_disclaimer": settings.SCIENTIFIC_DISCLAIMER,
    }


@app.get("/api/species", response_model=SpeciesListResponse, tags=["Species"])
async def list_species(include_unverified: bool = True):
    """Returns laboratory species profiles with verified reference Km factors."""
    all_species = species_service.get_all_species(include_unverified=include_unverified)
    verified = [s for s in all_species if s.verification_status == "verified"]
    return SpeciesListResponse(
        species=all_species,
        total_count=len(all_species),
        verified_count=len(verified),
        dataset_version=settings.DATASET_VERSION,
    )


@app.get("/api/references", tags=["References"])
async def list_references():
    """Returns the library of authoritative scientific guidelines and citations."""
    return {
        "dataset_version": settings.DATASET_VERSION,
        "references": species_service.get_all_references(),
    }


@app.post("/api/calculate", response_model=DoseCalculationResult, tags=["Calculations"])
async def calculate_dose(request: DoseCalculationRequest):
    """
    Computes interspecies dose translation based on BSA (Km) scaling,
    target weight, optional formulation concentration, and MRSD clinical safety factors.
    """
    try:
        return dose_calculator.calculate(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@app.get("/api/compare", response_model=MultiSpeciesComparisonResponse, tags=["Calculations"])
async def compare_all_species(
    source_species_id: str = "rat",
    source_dose: float = 10.0,
    source_unit: str = "mg_kg",
):
    """
    Returns equivalent dose across ALL verified laboratory species simultaneously.
    """
    try:
        from decimal import Decimal
        return dose_calculator.compare_across_all_species(
            source_species_id=source_species_id,
            source_dose=Decimal(str(source_dose)),
            source_unit=source_unit,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/cohort", response_model=CohortCalculationResult, tags=["Calculations"])
async def calculate_cohort(request: CohortCalculationRequest):
    """
    Calculates total active drug mass, group daily totals, and required
    solution volumes for an experimental animal cohort or study protocol.
    """
    try:
        return dose_calculator.calculate_cohort(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
