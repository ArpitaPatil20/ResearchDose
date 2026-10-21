"""
ResearchDose — Pure Python Dose Calculation Engine.

Executes transparent, reproducible interspecies dose scaling, total mass arithmetic,
liquid formulation volume conversion, NC3Rs welfare checks, and preclinical study cohort requirements.
Strictly decoupled from web and UI layers.
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple

from app.core.config import settings
from app.schemas.dose import (
    DoseCalculationRequest,
    DoseCalculationResult,
    ConversionMode,
    MultiSpeciesComparisonItem,
    MultiSpeciesComparisonResponse,
    CohortCalculationRequest,
    CohortCalculationResult,
)
from app.schemas.species import SpeciesReference, VerificationStatus
from app.services.species_service import species_service, SpeciesService
from app.services.unit_converter import UnitConverter, WeightUnit, DoseUnit, ConcentrationUnit


class DoseCalculator:
    """Core mathematical engine for preclinical dose conversion."""

    # NC3Rs and laboratory standard maximum recommended administration volume thresholds (mL/kg)
    ROUTE_RECOMMENDED_LIMITS = {
        "oral_gavage": Decimal("10.0"),
        "iv_bolus": Decimal("5.0"),
        "ip": Decimal("10.0"),
        "sc": Decimal("5.0"),
    }
    ROUTE_MAX_LIMITS = {
        "oral_gavage": Decimal("20.0"),
        "iv_bolus": Decimal("10.0"),
        "ip": Decimal("20.0"),
        "sc": Decimal("10.0"),
    }

    def __init__(self, sp_service: SpeciesService = species_service):
        self.species_service = sp_service

    def _round_dec(self, val: Decimal, places: int = settings.DEFAULT_DECIMAL_PLACES) -> Decimal:
        """Rounds decimal safely using standard round-half-up scientific rule."""
        q = Decimal(10) ** -places
        return val.quantize(q, rounding=ROUND_HALF_UP)

    def determine_mode(self, source: SpeciesReference, target: SpeciesReference) -> ConversionMode:
        """Determines the conversion mode based on taxonomic category."""
        if source.category.value == "human" and target.category.value != "human":
            return ConversionMode.HUMAN_TO_ANIMAL
        elif source.category.value != "human" and target.category.value == "human":
            return ConversionMode.ANIMAL_TO_HUMAN
        else:
            return ConversionMode.ANIMAL_TO_ANIMAL

    def _check_route_welfare(
        self, volume_per_kg_ml: Decimal, route: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Evaluates administration volume against NC3Rs animal welfare guidelines."""
        if not route or route not in self.ROUTE_RECOMMENDED_LIMITS:
            return "safe", "Administration volume within general laboratory limits."

        rec_limit = self.ROUTE_RECOMMENDED_LIMITS[route]
        max_limit = self.ROUTE_MAX_LIMITS[route]

        route_label = route.replace("_", " ").title()

        if volume_per_kg_ml <= rec_limit:
            return (
                "safe",
                f"{route_label} volume ({self._round_dec(volume_per_kg_ml, 2)} mL/kg) is within NC3Rs good practice guidelines (≤ {rec_limit} mL/kg)."
            )
        elif volume_per_kg_ml <= max_limit:
            return (
                "warning",
                f"{route_label} volume ({self._round_dec(volume_per_kg_ml, 2)} mL/kg) exceeds good practice threshold (≤ {rec_limit} mL/kg). May cause subject discomfort."
            )
        else:
            return (
                "exceeded",
                f"Caution: {route_label} volume ({self._round_dec(volume_per_kg_ml, 2)} mL/kg) exceeds maximum permissible welfare limit (max {max_limit} mL/kg)! Please increase formulation concentration."
            )

    def calculate(self, request: DoseCalculationRequest) -> DoseCalculationResult:
        """
        Executes an interspecies dose conversion with full arithmetic provenance,
        weight scaling, optional formulation volume check, and clinical starting dose (MRSD).
        """
        # 1. Lookup species
        source = self.species_service.get_species_by_id(request.source_species_id)
        if not source:
            raise ValueError(f"Source species '{request.source_species_id}' was not found.")

        target = self.species_service.get_species_by_id(request.target_species_id)
        if not target:
            raise ValueError(f"Target species '{request.target_species_id}' was not found.")

        # 2. Verify scientific applicability
        is_supported, error_msg = self.species_service.is_conversion_supported(source.id, target.id)
        if not is_supported:
            raise ValueError(error_msg)

        # 3. Determine Source Weight
        is_source_ref_weight = False
        if request.source_weight is not None:
            source_weight_kg = UnitConverter.normalize_weight_to_kg(
                request.source_weight, request.source_weight_unit
            )
        else:
            is_source_ref_weight = True
            if source.reference_weight_kg is None:
                raise ValueError(
                    f"Species '{source.common_name}' does not have a standard reference weight. "
                    "You must provide a source body weight."
                )
            source_weight_kg = Decimal(str(source.reference_weight_kg))

        # 4. Normalize source dose to mg/kg
        unit_str = str(request.source_dose_unit).lower().replace("/", "_")
        if unit_str in ("total_mg", "total_g", "total_ug"):
            dec_dose = UnitConverter.to_decimal(request.source_dose)
            if dec_dose <= 0:
                raise ValueError("Source dose must be strictly positive (> 0).")
            if unit_str == "total_g":
                total_mg = dec_dose * Decimal("1000.0")
            elif unit_str == "total_ug":
                total_mg = dec_dose * Decimal("0.001")
            else:
                total_mg = dec_dose
            source_dose_mg_kg = total_mg / source_weight_kg
        else:
            source_dose_mg_kg = UnitConverter.normalize_dose_to_mg_kg(
                request.source_dose, request.source_dose_unit
            )

        source_km = Decimal(str(source.km_factor))
        target_km = Decimal(str(target.km_factor))

        # 5. Interspecies BSA Normalization:
        # Target dose (mg/kg) = Source dose (mg/kg) * Km(source) / Km(target)
        km_ratio = source_km / target_km
        target_dose_mg_kg = source_dose_mg_kg * km_ratio

        # 6. Determine Target Weight
        is_target_ref_weight = False
        if request.target_weight is not None:
            target_weight_kg = UnitConverter.normalize_weight_to_kg(
                request.target_weight, request.target_weight_unit
            )
        else:
            is_target_ref_weight = True
            if target.reference_weight_kg is None:
                raise ValueError(
                    f"Species '{target.common_name}' does not have a standard reference weight. "
                    "You must provide a specific target body weight."
                )
            target_weight_kg = Decimal(str(target.reference_weight_kg))

        # 7. Total Dose:
        # Total dose (mg) = Target dose (mg/kg) * Weight (kg)
        total_dose_mg = target_dose_mg_kg * target_weight_kg
        total_dose_ug = total_dose_mg * Decimal("1000.0")

        # 8. Clinical Safety Factor for Human (MRSD)
        safety_factor = Decimal(str(request.safety_factor or 1.0))
        mrsd_mg_kg = None
        mrsd_total_mg = None
        if safety_factor > 1:
            mrsd_mg_kg = target_dose_mg_kg / safety_factor
            mrsd_total_mg = mrsd_mg_kg * target_weight_kg

        # 9. Liquid Formulation Volume & Welfare Check
        conc_mg_ml = None
        volume_ml = None
        volume_ul = None
        vol_per_kg_ml = None
        route_status = None
        route_msg = None

        if request.concentration is not None:
            conc_mg_ml = UnitConverter.normalize_concentration_to_mg_ml(
                request.concentration, request.concentration_unit
            )
            volume_ml = total_dose_mg / conc_mg_ml
            volume_ul = volume_ml * Decimal("1000.0")
            vol_per_kg_ml = volume_ml / target_weight_kg
            route_status, route_msg = self._check_route_welfare(vol_per_kg_ml, request.administration_route)

        # 10. Comparison with Direct mg/kg Scaling
        direct_unscaled_mg_kg = source_dose_mg_kg
        scaling_diff_pct = ((target_dose_mg_kg - direct_unscaled_mg_kg) / direct_unscaled_mg_kg) * Decimal("100.0")

        # 11. Build Step-by-Step Arithmetic Audit
        mode = self.determine_mode(source, target)
        steps = [
            f"1. Input source dose: {request.source_dose} {request.source_dose_unit} normalized to {self._round_dec(source_dose_mg_kg, 4)} mg/kg (Source weight: {self._round_dec(source_weight_kg, 4)} kg).",
            f"2. Authoritative Km factors retrieved: {source.common_name} Km = {source_km}; {target.common_name} Km = {target_km}.",
            f"3. Allometric conversion ratio: Km(source) / Km(target) = {source_km} / {target_km} = {self._round_dec(km_ratio, 6)}.",
            f"4. Target dose calculation: {self._round_dec(source_dose_mg_kg, 4)} mg/kg × ({source_km} / {target_km}) = {self._round_dec(target_dose_mg_kg, 4)} mg/kg.",
            f"5. Target subject weight: {self._round_dec(target_weight_kg, 4)} kg ({'Reference standard' if is_target_ref_weight else 'Researcher custom weight'}).",
            f"6. Total mass required: {self._round_dec(target_dose_mg_kg, 4)} mg/kg × {self._round_dec(target_weight_kg, 4)} kg = {self._round_dec(total_dose_mg, 4)} mg ({self._round_dec(total_dose_ug, 2)} µg).",
        ]

        if mrsd_mg_kg is not None:
            steps.append(
                f"7. Clinical Safety Factor ({safety_factor}×) applied: Maximum Recommended Starting Dose (MRSD) = {self._round_dec(target_dose_mg_kg, 4)} / {safety_factor} = {self._round_dec(mrsd_mg_kg, 4)} mg/kg (Total: {self._round_dec(mrsd_total_mg, 4)} mg)."
            )

        if conc_mg_ml is not None:
            steps.append(
                f"{len(steps) + 1}. Formulation volume: {self._round_dec(total_dose_mg, 4)} mg / {self._round_dec(conc_mg_ml, 4)} mg/mL = {self._round_dec(volume_ml, 4)} mL ({self._round_dec(volume_ul, 2)} µL). Volume rate = {self._round_dec(vol_per_kg_ml, 2)} mL/kg."
            )

        steps.append(
            f"{len(steps) + 1}. Direct mg/kg scaling comparison: Direct translation without BSA scaling would yield {self._round_dec(direct_unscaled_mg_kg, 4)} mg/kg "
            f"({'+' if scaling_diff_pct >= 0 else ''}{self._round_dec(scaling_diff_pct, 2)}% difference)."
        )

        # 12. Limitations & Disclaimers
        limitations = [
            "Mathematical BSA scaling is an empirical allometric approximation based on standard metabolic rates.",
            "Does not account for non-linear pharmacokinetics, species-specific cytochrome P450 isoenzymes, receptor binding affinities, or plasma protein differences.",
            "Clinical Maximum Recommended Starting Dose (MRSD) in first-in-human clinical trials requires established NOAEL and appropriate safety factors (typically ≥ 10×).",
        ]

        citation = source.source_citation if source.source_citation == target.source_citation else f"{source.source_citation} & {target.source_citation}"

        return DoseCalculationResult(
            mode=mode.value,
            source_species_id=source.id,
            source_species_name=source.common_name,
            target_species_id=target.id,
            target_species_name=target.common_name,
            source_dose_input=request.source_dose,
            source_dose_unit=request.source_dose_unit,
            source_dose_mg_kg=self._round_dec(source_dose_mg_kg, 4),
            source_weight_kg=self._round_dec(source_weight_kg, 4),
            is_source_reference_weight=is_source_ref_weight,
            source_km=source_km,
            target_km=target_km,
            km_ratio=self._round_dec(km_ratio, 6),
            target_dose_mg_kg=self._round_dec(target_dose_mg_kg, 4),
            target_weight_kg=self._round_dec(target_weight_kg, 4),
            is_reference_weight=is_target_ref_weight,
            total_dose_mg=self._round_dec(total_dose_mg, 4),
            total_dose_ug=self._round_dec(total_dose_ug, 2),
            safety_factor=safety_factor,
            mrsd_mg_kg=self._round_dec(mrsd_mg_kg, 4) if mrsd_mg_kg is not None else None,
            mrsd_total_mg=self._round_dec(mrsd_total_mg, 4) if mrsd_total_mg is not None else None,
            concentration_mg_ml=self._round_dec(conc_mg_ml, 4) if conc_mg_ml is not None else None,
            formulation_volume_ml=self._round_dec(volume_ml, 4) if volume_ml is not None else None,
            formulation_volume_ul=self._round_dec(volume_ul, 2) if volume_ul is not None else None,
            volume_per_kg_ml=self._round_dec(vol_per_kg_ml, 2) if vol_per_kg_ml is not None else None,
            route_welfare_status=route_status,
            route_welfare_message=route_msg,
            direct_unscaled_dose_mg_kg=self._round_dec(direct_unscaled_mg_kg, 4),
            scaling_differential_percent=self._round_dec(scaling_diff_pct, 2),
            formula_used="Target Dose (mg/kg) = Source Dose (mg/kg) × [Km(source) / Km(target)]",
            arithmetic_steps=steps,
            scientific_citation=citation,
            reference_url=source.source_url or target.source_url,
            limitations=limitations,
            timestamp=datetime.now(timezone.utc).isoformat(),
            algorithm_version=settings.CALCULATION_ENGINE_VERSION,
        )

    def compare_across_all_species(
        self, source_species_id: str, source_dose: Decimal, source_unit: str = "mg_kg"
    ) -> MultiSpeciesComparisonResponse:
        """
        Calculates equivalent doses for ALL verified laboratory species simultaneously.
        """
        source = self.species_service.get_species_by_id(source_species_id)
        if not source or source.verification_status != VerificationStatus.VERIFIED or source.km_factor is None:
            raise ValueError(f"Source species '{source_species_id}' is not a verified reference model.")

        source_mg_kg = UnitConverter.normalize_dose_to_mg_kg(source_dose, source_unit)
        source_km = Decimal(str(source.km_factor))

        verified_species = self.species_service.get_verified_species()
        items: List[MultiSpeciesComparisonItem] = []

        for sp in verified_species:
            sp_km = Decimal(str(sp.km_factor))
            equiv_dose = source_mg_kg * (source_km / sp_km)
            ref_weight = Decimal(str(sp.reference_weight_kg))
            total_dose = equiv_dose * ref_weight
            fold_diff = equiv_dose / source_mg_kg

            items.append(
                MultiSpeciesComparisonItem(
                    species_id=sp.id,
                    common_name=sp.common_name,
                    category=sp.category.value,
                    km_factor=sp_km,
                    reference_weight_kg=ref_weight,
                    equivalent_dose_mg_kg=self._round_dec(equiv_dose, 4),
                    total_dose_mg=self._round_dec(total_dose, 4),
                    fold_difference_vs_source=self._round_dec(fold_diff, 4),
                )
            )

        return MultiSpeciesComparisonResponse(
            source_species_id=source.id,
            source_species_name=source.common_name,
            source_dose_mg_kg=self._round_dec(source_mg_kg, 4),
            comparisons=items,
            methodology="Allometric Body Surface Area (BSA) / Km Normalization (FDA CDER 2005 Table 1)",
            citation=source.source_citation,
        )

    def calculate_cohort(self, req: CohortCalculationRequest) -> CohortCalculationResult:
        """
        Calculates total drug mass, daily dosing, and stock solution volume needed
        for an experimental animal cohort / study group.
        """
        species = self.species_service.get_species_by_id(req.species_id)
        if not species:
            raise ValueError(f"Species '{req.species_id}' was not found.")

        # Normalize animal weight to kg
        avg_weight_kg = UnitConverter.normalize_weight_to_kg(req.average_weight, req.weight_unit)
        dose_mg_kg = UnitConverter.to_decimal(req.dose_mg_kg)

        # Single dose per animal
        single_dose_mg = dose_mg_kg * avg_weight_kg
        single_dose_ug = single_dose_mg * Decimal("1000.0")

        # Daily total for all animals in group
        animals = Decimal(str(req.animal_count))
        freq = Decimal(str(req.frequency_per_day))
        daily_total_mg = single_dose_mg * animals * freq

        # Study total
        days = Decimal(str(req.duration_days))
        study_total_mg = daily_total_mg * days
        study_total_g = study_total_mg / Decimal("1000.0")

        # Waste contingency
        waste_pct = Decimal(str(req.waste_margin_percent))
        waste_mg = study_total_mg * (waste_pct / Decimal("100.0"))
        grand_total_mg = study_total_mg + waste_mg
        grand_total_g = grand_total_mg / Decimal("100.0")

        # Liquid formulation volumes (if concentration provided)
        single_vol_ml = None
        single_vol_ul = None
        total_vol_ml = None

        if req.concentration_mg_ml is not None:
            conc_mg_ml = UnitConverter.to_decimal(req.concentration_mg_ml)
            if conc_mg_ml <= 0:
                raise ValueError("Formulation concentration must be > 0.")
            single_vol_ml = single_dose_mg / conc_mg_ml
            single_vol_ul = single_vol_ml * Decimal("1000.0")
            total_vol_ml = grand_total_mg / conc_mg_ml

        summary = (
            f"Study cohort of {req.animal_count} {species.common_name}s (mean weight {req.average_weight} {req.weight_unit}) "
            f"dosed at {self._round_dec(dose_mg_kg, 2)} mg/kg {req.frequency_per_day}× daily for {req.duration_days} days. "
            f"Requires {self._round_dec(single_dose_mg, 4)} mg per animal per dose ({self._round_dec(daily_total_mg, 2)} mg/day for cohort). "
            f"Total active compound needed including {self._round_dec(waste_pct, 1)}% contingency: {self._round_dec(grand_total_mg, 2)} mg ({self._round_dec(grand_total_g, 4)} g)."
        )

        return CohortCalculationResult(
            species_id=species.id,
            species_name=species.common_name,
            dose_mg_kg=self._round_dec(dose_mg_kg, 4),
            animal_count=req.animal_count,
            average_weight_kg=self._round_dec(avg_weight_kg, 4),
            single_dose_per_animal_mg=self._round_dec(single_dose_mg, 4),
            single_dose_per_animal_ug=self._round_dec(single_dose_ug, 2),
            daily_total_all_animals_mg=self._round_dec(daily_total_mg, 4),
            study_total_active_compound_mg=self._round_dec(study_total_mg, 4),
            study_total_active_compound_g=self._round_dec(study_total_g, 4),
            waste_contingency_mg=self._round_dec(waste_mg, 4),
            grand_total_compound_required_mg=self._round_dec(grand_total_mg, 4),
            grand_total_compound_required_g=self._round_dec(grand_total_g, 4),
            single_volume_per_animal_ml=self._round_dec(single_vol_ml, 4) if single_vol_ml is not None else None,
            single_volume_per_animal_ul=self._round_dec(single_vol_ul, 2) if single_vol_ul is not None else None,
            total_formulation_volume_required_ml=self._round_dec(total_vol_ml, 2) if total_vol_ml is not None else None,
            summary_text=summary,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


# Global singleton instance
dose_calculator = DoseCalculator()
