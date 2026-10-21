"""
Pytest configuration and shared test fixtures for ResearchDose.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.species_service import SpeciesService, species_service


@pytest.fixture(scope="session")
def client():
    """Provides a TestClient for testing FastAPI routes."""
    species_service.initialize()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def service():
    """Provides an initialized SpeciesService instance."""
    species_service.initialize()
    return species_service
