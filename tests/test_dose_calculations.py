"""
Automated validation of Interspecies Dose Calculations against FDA (2005) & Reagan-Shaw (2008).
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.schemas.dose import DoseCalculationRequest, CohortCalculationRequest
from app.services.dose_calculator import dose_calculator


def test_mouse_to_human_hed_benchmark():
    """
    Benchmark test based on FDA CDER (2005) Table 1 & Reagan-Shaw et al. (2008):
    Mouse Km = 3, Human Km = 37.
    Mouse dose = 10 mg/kg.
    HED (mg/kg) = 10 * (3 / 37) = 0.8108 mg/kg.
    Total adult human dose (60 kg) = 0.8108 * 60 = 48.6486 mg.
    """
    req = DoseCalculationRequest(
        source_species_id="mouse",
        target_species_id="human",
        source_dose=Decimal("10.0"),
        source_dose_unit="mg_kg",
        target_weight=Decimal("60.0"),
        target_weight_unit="kg",
        safety_factor=Decimal("10.0"),
    )
    result = dose_calculator.calculate(req)

    assert result.source_km == Decimal("3.0")
    assert result.target_km == Decimal("37.0")
    assert abs(result.target_dose_mg_kg - Decimal("0.8108")) < Decimal("0.001")
    assert abs(result.total_dose_mg - Decimal("48.6486")) < Decimal("0.05")
    assert result.mrsd_mg_kg is not None
    assert abs(result.mrsd_mg_kg - Decimal("0.0811")) < Decimal("0.001")


def test_rat_to_human_hed_benchmark():
    """
    Rat Km = 6, Human Km = 37.
    Rat dose = 50 mg/kg.
    HED = 50 * (6 / 37) = 8.1081 mg/kg.
    Total dose for 60 kg human = 8.1081 * 60 = 486.4865 mg.
    """
    req = DoseCalculationRequest(
        source_species_id="rat",
        target_species_id="human",
        source_dose=Decimal("50.0"),
        source_dose_unit="mg_kg",
        target_weight=Decimal("60.0"),
        target_weight_unit="kg",
    )
    result = dose_calculator.calculate(req)

    assert abs(result.target_dose_mg_kg - Decimal("8.1081")) < Decimal("0.001")
    assert abs(result.total_dose_mg - Decimal("486.4865")) < Decimal("0.05")


def test_human_total_dose_to_mouse_preclinical():
    """
    Human dose = 500 mg total in a 60 kg adult human.
    Human mg/kg = 500 / 60 = 8.3333 mg/kg.
    Mouse Km = 3, Human Km = 37.
    Mouse dose = 8.3333 * (37 / 3) = 102.7778 mg/kg.
    Total dose for a 25 g mouse (0.025 kg) = 102.7778 * 0.025 = 2.5694 mg = 2569.4 µg.
    """
    req = DoseCalculationRequest(
        source_species_id="human",
        target_species_id="mouse",
        source_dose=Decimal("500.0"),
        source_dose_unit="total_mg",
        source_weight=Decimal("60.0"),
        source_weight_unit="kg",
        target_weight=Decimal("25.0"),
        target_weight_unit="g",
    )
    result = dose_calculator.calculate(req)

    assert abs(result.source_dose_mg_kg - Decimal("8.3333")) < Decimal("0.001")
    assert abs(result.target_dose_mg_kg - Decimal("102.7778")) < Decimal("0.01")
    assert abs(result.total_dose_mg - Decimal("2.5694")) < Decimal("0.01")
    assert abs(result.total_dose_ug - Decimal("2569.44")) < Decimal("0.1")


def test_formulation_volume_and_nc3rs_welfare_check():
    """
    Testing formulation volume calculation and NC3Rs guidelines.
    Rat: 200 g (0.2 kg), dose 20 mg/kg -> Total dose = 4 mg.
    Concentration = 2 mg/mL -> Volume = 2 mL.
    Volume per kg = 2 mL / 0.2 kg = 10 mL/kg (within oral gavage good practice limit).
    """
    req = DoseCalculationRequest(
        source_species_id="rat",
        target_species_id="rat",
        source_dose=Decimal("20.0"),
        source_dose_unit="mg_kg",
        target_weight=Decimal("200.0"),
        target_weight_unit="g",
        concentration=Decimal("2.0"),
        concentration_unit="mg_ml",
        administration_route="oral_gavage",
    )
    result = dose_calculator.calculate(req)

    assert result.formulation_volume_ml == Decimal("2.0000")
    assert result.volume_per_kg_ml == Decimal("10.00")
    assert result.route_welfare_status == "safe"


def test_cohort_calculation():
    """
    10 mice, average weight 20 g, 10 mg/kg once daily for 14 days, 10% waste contingency.
    Single dose per mouse = 10 mg/kg * 0.02 kg = 0.2 mg.
    Daily group total = 0.2 * 10 * 1 = 2 mg/day.
    14-day study total = 28 mg.
    With 10% contingency = 30.8 mg.
    """
    req = CohortCalculationRequest(
        species_id="mouse",
        dose_mg_kg=Decimal("10.0"),
        animal_count=10,
        average_weight=Decimal("20.0"),
        weight_unit="g",
        frequency_per_day=1,
        duration_days=14,
        concentration_mg_ml=Decimal("1.0"),
        waste_margin_percent=Decimal("10.0"),
    )
    res = dose_calculator.calculate_cohort(req)

    assert res.single_dose_per_animal_mg == Decimal("0.2000")
    assert res.daily_total_all_animals_mg == Decimal("2.0000")
    assert res.study_total_active_compound_mg == Decimal("28.0000")
    assert res.grand_total_compound_required_mg == Decimal("30.8000")
    assert res.single_volume_per_animal_ml == Decimal("0.2000")


def test_api_calculate_endpoint(client: TestClient):
    """Test POST /api/calculate endpoint."""
    payload = {
        "source_species_id": "mouse",
        "target_species_id": "human",
        "source_dose": 10.0,
        "source_dose_unit": "mg_kg",
        "target_weight": 60.0,
        "target_weight_unit": "kg",
    }
    resp = client.post("/api/calculate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["target_dose_mg_kg"]) == pytest.approx(0.8108, 0.001)
    assert "Target Dose (mg/kg)" in data["formula_used"]


def test_api_compare_endpoint(client: TestClient):
    """Test GET /api/compare endpoint."""
    resp = client.get("/api/compare?source_species_id=rat&source_dose=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "comparisons" in data
    assert len(data["comparisons"]) >= 14
    # Check that mouse equivalent is 20 mg/kg (Km 6 / Km 3 = 2x)
    mouse_item = next((c for c in data["comparisons"] if c["species_id"] == "mouse"), None)
    assert mouse_item is not None
    assert float(mouse_item["equivalent_dose_mg_kg"]) == pytest.approx(20.0, 0.01)


def test_api_cohort_endpoint(client: TestClient):
    """Test POST /api/cohort endpoint."""
    payload = {
        "species_id": "rat",
        "dose_mg_kg": 25.0,
        "animal_count": 8,
        "average_weight": 200.0,
        "weight_unit": "g",
        "frequency_per_day": 1,
        "duration_days": 7,
        "concentration_mg_ml": 5.0,
        "waste_margin_percent": 10.0,
    }
    resp = client.post("/api/cohort", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["animal_count"] == 8
    assert float(data["single_dose_per_animal_mg"]) == 5.0
