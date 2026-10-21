/**
 * ResearchDose — Scientific Dose Conversion & Research Platform
 * Client-side Reactive Engine & API Synchronization
 */

// Global Species Registry cache
let speciesRegistry = [];
let referencesRegistry = [];

// Standard reference Km factors (FDA CDER 2005 Table 1)
const KM_TABLE = {
    human: 37.0,
    child: 25.0,
    mouse: 3.0,
    rat: 6.0,
    hamster: 5.0,
    guinea_pig: 8.0,
    ferret: 7.0,
    rabbit: 12.0,
    dog: 20.0,
    cat: 12.0,
    monkey_cynomolgus: 12.0,
    monkey_rhesus: 12.0,
    monkey_marmoset: 6.0,
    monkey_squirrel: 7.0,
    baboon: 20.0,
    mini_pig: 27.0,
    micro_pig: 21.0
};

// Standard reference weights (kg)
const WEIGHT_TABLE = {
    human: 60.0,
    child: 20.0,
    mouse: 0.02,
    rat: 0.15,
    hamster: 0.08,
    guinea_pig: 0.40,
    ferret: 0.30,
    rabbit: 1.80,
    dog: 10.0,
    cat: 2.0,
    monkey_cynomolgus: 2.40,
    monkey_rhesus: 3.20,
    monkey_marmoset: 0.35,
    monkey_squirrel: 0.60,
    baboon: 12.0,
    mini_pig: 20.0,
    micro_pig: 8.0
};

// Route welfare guidelines (mL/kg max thresholds)
const ROUTE_LIMITS = {
    oral_gavage: { rec: 10.0, max: 20.0, name: "Oral Gavage" },
    iv_bolus: { rec: 5.0, max: 10.0, name: "Intravenous (IV)" },
    ip: { rec: 10.0, max: 20.0, name: "Intraperitoneal (IP)" },
    sc: { rec: 5.0, max: 10.0, name: "Subcutaneous (SC)" }
};

document.addEventListener("DOMContentLoaded", async () => {
    try {
        await loadSpeciesData();
        setupEventListeners();
        calculateAnimalToHuman();
        calculateHumanToAnimal();
        calculateAnimalToAnimal();
        calculateCohort();
        calculateFormulationOnly();
        updateMultiSpeciesMatrix("mouse", 10.0);
    } catch (err) {
        console.error("Initialization error:", err);
    }
});

/**
 * Loads species and reference libraries from the backend API
 */
async function loadSpeciesData() {
    try {
        const resp = await fetch("/api/species");
        if (resp.ok) {
            const data = await resp.json();
            speciesRegistry = data.species;
        }
    } catch (e) {
        console.warn("Could not fetch species API, using fallback baseline.");
    }
}

/**
 * Set up all reactive input listeners, tab switches, and presets
 */
function setupEventListeners() {
    // Tab 1: Animal to Human
    const a2hInputs = ["a2h_animal", "a2h_dose", "a2h_dose_unit", "a2h_animal_weight", "a2h_animal_weight_unit", "a2h_human_weight", "a2h_safety_factor", "a2h_conc", "a2h_route"];
    a2hInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("input", () => calculateAnimalToHuman());
    });

    // Auto-update animal weight when selecting species in Tab 1
    const a2hAnimal = document.getElementById("a2h_animal");
    if (a2hAnimal) {
        a2hAnimal.addEventListener("change", () => {
            const spId = a2hAnimal.value;
            const refWt = WEIGHT_TABLE[spId] || 0.15;
            const wtEl = document.getElementById("a2h_animal_weight");
            const unitEl = document.getElementById("a2h_animal_weight_unit");
            if (wtEl && unitEl) {
                if (refWt < 1.0) {
                    unitEl.value = "g";
                    wtEl.value = (refWt * 1000).toFixed(0);
                } else {
                    unitEl.value = "kg";
                    wtEl.value = refWt.toFixed(2);
                }
            }
            calculateAnimalToHuman();
        });
    }

    // Tab 2: Human to Animal
    const h2aInputs = ["h2a_dose_type", "h2a_human_dose", "h2a_human_weight", "h2a_target_animal", "h2a_animal_weight", "h2a_animal_weight_unit", "h2a_conc", "h2a_route"];
    h2aInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("input", () => calculateHumanToAnimal());
    });

    const h2aAnimal = document.getElementById("h2a_target_animal");
    if (h2aAnimal) {
        h2aAnimal.addEventListener("change", () => {
            const spId = h2aAnimal.value;
            const refWt = WEIGHT_TABLE[spId] || 0.02;
            const wtEl = document.getElementById("h2a_animal_weight");
            const unitEl = document.getElementById("h2a_animal_weight_unit");
            if (wtEl && unitEl) {
                if (refWt < 1.0) {
                    unitEl.value = "g";
                    wtEl.value = (refWt * 1000).toFixed(0);
                } else {
                    unitEl.value = "kg";
                    wtEl.value = refWt.toFixed(2);
                }
            }
            calculateHumanToAnimal();
        });
    }

    // Tab 3: Animal to Animal
    const a2aInputs = ["a2a_source_animal", "a2a_source_dose", "a2a_source_weight", "a2a_source_weight_unit", "a2a_target_animal", "a2a_target_weight", "a2a_target_weight_unit", "a2a_conc"];
    a2aInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("input", () => calculateAnimalToAnimal());
    });

    // Tab 4: Cohort Planner
    const cohortInputs = ["ch_species", "ch_dose", "ch_count", "ch_avg_weight", "ch_weight_unit", "ch_freq", "ch_days", "ch_waste", "ch_conc"];
    cohortInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("input", () => calculateCohort());
    });

    const chSpecies = document.getElementById("ch_species");
    if (chSpecies) {
        chSpecies.addEventListener("change", () => {
            const spId = chSpecies.value;
            const refWt = WEIGHT_TABLE[spId] || 0.02;
            const wtEl = document.getElementById("ch_avg_weight");
            const unitEl = document.getElementById("ch_weight_unit");
            if (wtEl && unitEl) {
                if (refWt < 1.0) {
                    unitEl.value = "g";
                    wtEl.value = (refWt * 1000).toFixed(0);
                } else {
                    unitEl.value = "kg";
                    wtEl.value = refWt.toFixed(2);
                }
            }
            calculateCohort();
        });
    }

    // Tab 5: Formulation & Volume
    const formInputs = ["form_animal_weight", "form_weight_unit", "form_dose", "form_conc", "form_route"];
    formInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("input", () => calculateFormulationOnly());
    });

    // Species table search filter
    const searchInput = document.getElementById("speciesSearchInput");
    if (searchInput) {
        searchInput.addEventListener("input", (e) => filterSpeciesTable(e.target.value));
    }

    // Tab change triggers for mobile bar synchronization
    const tabButtons = document.querySelectorAll("#calcTabs button");
    tabButtons.forEach(btn => {
        btn.addEventListener("shown.bs.tab", (e) => {
            const targetId = e.target.getAttribute("data-bs-target");
            if (targetId === "#tab-a2h") calculateAnimalToHuman();
            else if (targetId === "#tab-h2a") calculateHumanToAnimal();
            else if (targetId === "#tab-a2a") calculateAnimalToAnimal();
            else if (targetId === "#tab-cohort") calculateCohort();
            else if (targetId === "#tab-form") calculateFormulationOnly();
        });
    });
}

/**
 * Filter species in dataset table
 */
function filterSpeciesTable(query) {
    const q = query.toLowerCase().trim();
    const rows = document.querySelectorAll("#speciesTableBody tr");
    rows.forEach(r => {
        const text = r.innerText.toLowerCase();
        r.style.display = text.includes(q) ? "" : "none";
    });
}

/**
 * Tab 1: Animal to Human Dose Calculation (HED)
 */
function calculateAnimalToHuman() {
    const spId = document.getElementById("a2h_animal")?.value || "mouse";
    const doseRaw = parseFloat(document.getElementById("a2h_dose")?.value) || 0;
    const doseUnit = document.getElementById("a2h_dose_unit")?.value || "mg_kg";
    const animalWtRaw = parseFloat(document.getElementById("a2h_animal_weight")?.value) || 0;
    const animalWtUnit = document.getElementById("a2h_animal_weight_unit")?.value || "g";
    const humanWt = parseFloat(document.getElementById("a2h_human_weight")?.value) || 60.0;
    const safetyFactor = parseFloat(document.getElementById("a2h_safety_factor")?.value) || 1.0;
    const conc = parseFloat(document.getElementById("a2h_conc")?.value) || 0;
    const route = document.getElementById("a2h_route")?.value || "oral_gavage";

    if (doseRaw <= 0) return;

    // Normalize animal dose to mg/kg
    let doseMgKg = doseRaw;
    if (doseUnit === "ug_kg") doseMgKg = doseRaw / 1000.0;
    if (doseUnit === "g_kg") doseMgKg = doseRaw * 1000.0;

    // Normalize animal weight to kg
    let animalWtKg = animalWtRaw > 0 ? (animalWtUnit === "g" ? animalWtRaw / 1000.0 : animalWtRaw) : (WEIGHT_TABLE[spId] || 0.02);

    const sourceKm = KM_TABLE[spId] || 3.0;
    const humanKm = KM_TABLE.human; // 37

    // Interspecies BSA formula: HED = Animal Dose * (Animal Km / Human Km)
    const kmRatio = sourceKm / humanKm;
    const hedMgKg = doseMgKg * kmRatio;
    const humanTotalMg = hedMgKg * humanWt;

    // Safety factor (MRSD)
    const mrsdMgKg = safetyFactor > 1 ? hedMgKg / safetyFactor : null;
    const mrsdTotalMg = mrsdMgKg ? mrsdMgKg * humanWt : null;

    // Difference vs direct unscaled mg/kg
    const directDiffPct = ((hedMgKg - doseMgKg) / doseMgKg) * 100.0;

    // Update UI elements
    setText("a2h_res_hed_mg_kg", hedMgKg.toFixed(4) + " mg/kg");
    setText("a2h_res_total_mg", humanTotalMg.toFixed(2) + " mg");
    setText("a2h_res_km_ratio", `${sourceKm} / ${humanKm} = ${kmRatio.toFixed(4)}`);
    setText("a2h_res_diff", `${directDiffPct >= 0 ? "+" : ""}${directDiffPct.toFixed(1)}% vs direct mg/kg`);

    // MRSD display
    const mrsdRow = document.getElementById("a2h_mrsd_container");
    if (mrsdRow) {
        if (safetyFactor > 1 && mrsdMgKg) {
            mrsdRow.style.display = "block";
            setText("a2h_res_mrsd_mg_kg", mrsdMgKg.toFixed(4) + " mg/kg");
            setText("a2h_res_mrsd_total_mg", mrsdTotalMg.toFixed(2) + " mg");
            setText("a2h_mrsd_factor_label", `${safetyFactor}× Safety Factor Applied`);
        } else {
            mrsdRow.style.display = "none";
        }
    }

    // Formulation volume if concentration given
    const volBox = document.getElementById("a2h_volume_box");
    if (volBox) {
        if (conc > 0) {
            volBox.style.display = "block";
            const totalAnimalDoseMg = doseMgKg * animalWtKg;
            const volMl = totalAnimalDoseMg / conc;
            const volUl = volMl * 1000.0;
            const volPerKg = volMl / animalWtKg;

            setText("a2h_res_vol_ml", volMl.toFixed(3) + " mL (" + volUl.toFixed(1) + " µL)");
            setText("a2h_res_vol_rate", volPerKg.toFixed(2) + " mL/kg");

            evaluateWelfareBadge("a2h_welfare_badge", volPerKg, route);
        } else {
            volBox.style.display = "none";
        }
    }

    // Steps list
    const steps = [
        `1. Animal dose normalized: ${doseRaw} ${doseUnit} = ${doseMgKg.toFixed(4)} mg/kg.`,
        `2. Km Factors retrieved: ${getSpeciesName(spId)} Km = ${sourceKm}; Adult Human Km = ${humanKm}.`,
        `3. Conversion ratio: Km(animal) / Km(human) = ${sourceKm} / ${humanKm} = ${kmRatio.toFixed(6)}.`,
        `4. Human Equivalent Dose: ${doseMgKg.toFixed(4)} mg/kg × (${sourceKm}/${humanKm}) = ${hedMgKg.toFixed(4)} mg/kg.`,
        `5. Total Human Dose (${humanWt} kg): ${hedMgKg.toFixed(4)} mg/kg × ${humanWt} kg = ${humanTotalMg.toFixed(4)} mg.`
    ];
    if (safetyFactor > 1 && mrsdMgKg) {
        steps.push(`6. Clinical Starting Dose (${safetyFactor}× safety margin): ${hedMgKg.toFixed(4)} / ${safetyFactor} = ${mrsdMgKg.toFixed(4)} mg/kg (${mrsdTotalMg.toFixed(4)} mg total).`);
    }
    steps.push(`7. Biological rationale: Without BSA scaling, direct mg/kg would administer ${doseMgKg.toFixed(4)} mg/kg (${(doseMgKg * humanWt).toFixed(1)} mg), causing a severe ${Math.abs(directDiffPct).toFixed(0)}% overdose!`);

    renderSteps("a2h_steps_list", steps);

    // Update real-time matrix
    updateMultiSpeciesMatrix(spId, doseMgKg);

    // Update mobile floating bar
    updateMobileFloatingBar("HED: " + hedMgKg.toFixed(4) + " mg/kg", "Human: " + humanTotalMg.toFixed(1) + " mg");
}

/**
 * Tab 2: Human to Animal Preclinical Dose Calculation
 */
function calculateHumanToAnimal() {
    const doseType = document.getElementById("h2a_dose_type")?.value || "mg_kg";
    const humanDoseRaw = parseFloat(document.getElementById("h2a_human_dose")?.value) || 0;
    const humanWt = parseFloat(document.getElementById("h2a_human_weight")?.value) || 60.0;
    const targetSp = document.getElementById("h2a_target_animal")?.value || "mouse";
    const animalWtRaw = parseFloat(document.getElementById("h2a_animal_weight")?.value) || 0;
    const animalWtUnit = document.getElementById("h2a_animal_weight_unit")?.value || "g";
    const conc = parseFloat(document.getElementById("h2a_conc")?.value) || 0;
    const route = document.getElementById("h2a_route")?.value || "oral_gavage";

    if (humanDoseRaw <= 0) return;

    // Determine human dose in mg/kg
    let humanMgKg = humanDoseRaw;
    if (doseType === "total_mg") {
        humanMgKg = humanDoseRaw / humanWt;
    }

    // Animal weight in kg
    let animalWtKg = animalWtRaw > 0 ? (animalWtUnit === "g" ? animalWtRaw / 1000.0 : animalWtRaw) : (WEIGHT_TABLE[targetSp] || 0.02);

    const humanKm = KM_TABLE.human; // 37
    const targetKm = KM_TABLE[targetSp] || 3.0;

    // Animal Dose (mg/kg) = Human Dose (mg/kg) * (Human Km / Animal Km)
    const kmRatio = humanKm / targetKm;
    const animalDoseMgKg = humanMgKg * kmRatio;

    // Total mass required for this specific individual animal
    const animalTotalMg = animalDoseMgKg * animalWtKg;
    const animalTotalUg = animalTotalMg * 1000.0;

    setText("h2a_res_dose_mg_kg", animalDoseMgKg.toFixed(3) + " mg/kg");
    setText("h2a_res_total_mg", animalTotalMg.toFixed(4) + " mg");
    setText("h2a_res_total_ug", animalTotalUg.toFixed(1) + " µg");
    setText("h2a_res_km_ratio", `${humanKm} / ${targetKm} = ${kmRatio.toFixed(3)}`);
    setText("h2a_res_animal_wt", `${animalWtRaw} ${animalWtUnit} (${animalWtKg.toFixed(4)} kg)`);

    // Formulation volume
    const volBox = document.getElementById("h2a_volume_box");
    if (volBox) {
        if (conc > 0) {
            volBox.style.display = "block";
            const volMl = animalTotalMg / conc;
            const volUl = volMl * 1000.0;
            const volPerKg = volMl / animalWtKg;

            setText("h2a_res_vol_ml", volMl.toFixed(4) + " mL (" + volUl.toFixed(1) + " µL)");
            setText("h2a_res_vol_rate", volPerKg.toFixed(2) + " mL/kg");

            evaluateWelfareBadge("h2a_welfare_badge", volPerKg, route);
        } else {
            volBox.style.display = "none";
        }
    }

    // Steps
    const steps = [
        `1. Human baseline dose: ${humanDoseRaw} ${doseType === "total_mg" ? "total mg" : "mg/kg"} (Human weight: ${humanWt} kg) = ${humanMgKg.toFixed(4)} mg/kg.`,
        `2. Km factors: Human Km = ${humanKm}; ${getSpeciesName(targetSp)} Km = ${targetKm}.`,
        `3. Allometric ratio: Km(human) / Km(animal) = ${humanKm} / ${targetKm} = ${kmRatio.toFixed(4)}.`,
        `4. Target animal dose rate: ${humanMgKg.toFixed(4)} mg/kg × ${kmRatio.toFixed(4)} = ${animalDoseMgKg.toFixed(4)} mg/kg.`,
        `5. Individual animal total dose (${animalWtRaw} ${animalWtUnit} = ${animalWtKg.toFixed(4)} kg): ${animalDoseMgKg.toFixed(4)} mg/kg × ${animalWtKg.toFixed(4)} kg = ${animalTotalMg.toFixed(4)} mg (${animalTotalUg.toFixed(1)} µg).`
    ];
    if (conc > 0) {
        const volMl = animalTotalMg / conc;
        steps.push(`6. Solution volume (${conc} mg/mL): ${animalTotalMg.toFixed(4)} mg / ${conc} mg/mL = ${volMl.toFixed(4)} mL (${(volMl * 1000).toFixed(1)} µL).`);
    }

    renderSteps("h2a_steps_list", steps);

    // Update mobile floating bar
    updateMobileFloatingBar(getSpeciesName(targetSp) + " Dose", animalDoseMgKg.toFixed(2) + " mg/kg (" + animalTotalMg.toFixed(2) + " mg)");
}

/**
 * Tab 3: Animal to Animal Interspecies Conversion
 */
function calculateAnimalToAnimal() {
    const srcSp = document.getElementById("a2a_source_animal")?.value || "mouse";
    const srcDoseRaw = parseFloat(document.getElementById("a2a_source_dose")?.value) || 0;
    const tgtSp = document.getElementById("a2a_target_animal")?.value || "rat";
    const tgtWtRaw = parseFloat(document.getElementById("a2a_target_weight")?.value) || 0;
    const tgtWtUnit = document.getElementById("a2a_target_weight_unit")?.value || "g";
    const conc = parseFloat(document.getElementById("a2a_conc")?.value) || 0;

    if (srcDoseRaw <= 0) return;

    let tgtWtKg = tgtWtRaw > 0 ? (tgtWtUnit === "g" ? tgtWtRaw / 1000.0 : tgtWtRaw) : (WEIGHT_TABLE[tgtSp] || 0.15);

    const srcKm = KM_TABLE[srcSp] || 3.0;
    const tgtKm = KM_TABLE[tgtSp] || 6.0;

    const kmRatio = srcKm / tgtKm;
    const tgtDoseMgKg = srcDoseRaw * kmRatio;
    const tgtTotalMg = tgtDoseMgKg * tgtWtKg;
    const tgtTotalUg = tgtTotalMg * 1000.0;

    setText("a2a_res_dose_mg_kg", tgtDoseMgKg.toFixed(4) + " mg/kg");
    setText("a2a_res_total_mg", tgtTotalMg.toFixed(4) + " mg");
    setText("a2a_res_total_ug", tgtTotalUg.toFixed(1) + " µg");
    setText("a2a_res_km_ratio", `${srcKm} / ${tgtKm} = ${kmRatio.toFixed(4)}`);

    const volBox = document.getElementById("a2a_vol_box");
    if (volBox) {
        if (conc > 0) {
            volBox.style.display = "block";
            const volMl = tgtTotalMg / conc;
            setText("a2a_res_vol", `${volMl.toFixed(4)} mL (${(volMl * 1000).toFixed(1)} µL)`);
        } else {
            volBox.style.display = "none";
        }
    }

    const steps = [
        `1. Source: ${getSpeciesName(srcSp)} (Km = ${srcKm}), Source dose = ${srcDoseRaw.toFixed(4)} mg/kg.`,
        `2. Target: ${getSpeciesName(tgtSp)} (Km = ${tgtKm}).`,
        `3. Interspecies ratio: Km(source) / Km(target) = ${srcKm} / ${tgtKm} = ${kmRatio.toFixed(6)}.`,
        `4. Target dose: ${srcDoseRaw.toFixed(4)} mg/kg × ${kmRatio.toFixed(6)} = ${tgtDoseMgKg.toFixed(4)} mg/kg.`,
        `5. Target total mass for individual animal (${tgtWtRaw} ${tgtWtUnit}): ${tgtDoseMgKg.toFixed(4)} mg/kg × ${tgtWtKg.toFixed(4)} kg = ${tgtTotalMg.toFixed(4)} mg (${tgtTotalUg.toFixed(1)} µg).`
    ];

    renderSteps("a2a_steps_list", steps);

    // Update mobile floating bar
    updateMobileFloatingBar(getSpeciesName(tgtSp) + " Dose", tgtDoseMgKg.toFixed(2) + " mg/kg (" + tgtTotalMg.toFixed(2) + " mg)");
}

/**
 * Tab 4: Cohort Study Bulk Drug Requirement Planner
 */
function calculateCohort() {
    const spId = document.getElementById("ch_species")?.value || "mouse";
    const doseRaw = parseFloat(document.getElementById("ch_dose")?.value) || 0;
    const count = parseInt(document.getElementById("ch_count")?.value) || 10;
    const avgWtRaw = parseFloat(document.getElementById("ch_avg_weight")?.value) || 20;
    const wtUnit = document.getElementById("ch_weight_unit")?.value || "g";
    const freq = parseInt(document.getElementById("ch_freq")?.value) || 1;
    const days = parseInt(document.getElementById("ch_days")?.value) || 14;
    const wastePct = parseFloat(document.getElementById("ch_waste")?.value) || 10.0;
    const conc = parseFloat(document.getElementById("ch_conc")?.value) || 0;

    if (doseRaw <= 0 || count <= 0) return;

    const avgWtKg = wtUnit === "g" ? avgWtRaw / 1000.0 : avgWtRaw;
    const singleDoseMg = doseRaw * avgWtKg;
    const dailyTotalMg = singleDoseMg * count * freq;
    const studyNetMg = dailyTotalMg * days;
    const wasteMg = studyNetMg * (wastePct / 100.0);
    const grandTotalMg = studyNetMg + wasteMg;
    const grandTotalG = grandTotalMg / 1000.0;

    setText("ch_res_single_mg", singleDoseMg.toFixed(4) + " mg (" + (singleDoseMg * 1000).toFixed(1) + " µg)");
    setText("ch_res_daily_mg", dailyTotalMg.toFixed(2) + " mg/day");
    setText("ch_res_study_net_mg", studyNetMg.toFixed(2) + " mg");
    setText("ch_res_waste_mg", `+${wasteMg.toFixed(2)} mg (${wastePct}%)`);
    setText("ch_res_grand_total_mg", grandTotalMg.toFixed(2) + " mg");
    setText("ch_res_grand_total_g", grandTotalG.toFixed(4) + " g");

    const volContainer = document.getElementById("ch_res_volume_container");
    if (volContainer) {
        if (conc > 0) {
            volContainer.style.display = "block";
            const singleVolMl = singleDoseMg / conc;
            const totalVolMl = grandTotalMg / conc;
            setText("ch_res_single_vol", `${singleVolMl.toFixed(3)} mL (${(singleVolMl * 1000).toFixed(1)} µL) per animal`);
            setText("ch_res_total_vol", `${totalVolMl.toFixed(1)} mL total stock formulation`);
        } else {
            volContainer.style.display = "none";
        }
    }

    const summary = `Cohort of ${count} ${getSpeciesName(spId)}s (${avgWtRaw} ${wtUnit}) dosed at ${doseRaw} mg/kg (${freq}×/day) for ${days} days. Total active compound needed with ${wastePct}% contingency: ${grandTotalMg.toFixed(2)} mg (${grandTotalG.toFixed(4)} g).`;
    setText("ch_summary_text", summary);

    // Update mobile floating bar
    updateMobileFloatingBar("Total Study Compound", grandTotalMg.toFixed(1) + " mg (" + grandTotalG.toFixed(3) + " g)");
}

/**
 * Tab 5: Formulation & Administration Volume Standalone
 */
function calculateFormulationOnly() {
    const wtRaw = parseFloat(document.getElementById("form_animal_weight")?.value) || 20;
    const wtUnit = document.getElementById("form_weight_unit")?.value || "g";
    const doseMgKg = parseFloat(document.getElementById("form_dose")?.value) || 10;
    const conc = parseFloat(document.getElementById("form_conc")?.value) || 1.0;
    const route = document.getElementById("form_route")?.value || "oral_gavage";

    if (doseMgKg <= 0 || conc <= 0 || wtRaw <= 0) return;

    const wtKg = wtUnit === "g" ? wtRaw / 1000.0 : wtRaw;
    const totalDoseMg = doseMgKg * wtKg;
    const volMl = totalDoseMg / conc;
    const volUl = volMl * 1000.0;
    const volPerKg = volMl / wtKg;

    setText("form_res_total_dose", `${totalDoseMg.toFixed(4)} mg (${(totalDoseMg * 1000).toFixed(1)} µg)`);
    setText("form_res_vol_ml", `${volMl.toFixed(4)} mL`);
    setText("form_res_vol_ul", `${volUl.toFixed(1)} µL`);
    setText("form_res_vol_rate", `${volPerKg.toFixed(2)} mL/kg`);

    evaluateWelfareBadge("form_welfare_badge", volPerKg, route);

    // Update mobile floating bar
    updateMobileFloatingBar("Admin Volume", volMl.toFixed(3) + " mL (" + volUl.toFixed(0) + " µL)");
}

/**
 * Multi-Species Real-time Comparison Table
 */
function updateMultiSpeciesMatrix(srcSpeciesId, doseMgKg) {
    const tableBody = document.getElementById("matrixTableBody");
    if (!tableBody) return;

    const srcKm = KM_TABLE[srcSpeciesId] || 3.0;

    let html = "";
    Object.keys(KM_TABLE).forEach(spKey => {
        const spKm = KM_TABLE[spKey];
        const refWt = WEIGHT_TABLE[spKey];
        const equivDose = doseMgKg * (srcKm / spKm);
        const totalDose = equivDose * refWt;
        const foldDiff = equivDose / doseMgKg;
        const isSource = spKey === srcSpeciesId;

        html += `
            <tr class="${isSource ? 'highlight-source' : ''}">
                <td class="fw-bold">${getSpeciesName(spKey)} ${isSource ? '<span class="badge bg-primary ms-1">Source</span>' : ''}</td>
                <td><span class="badge-km">${spKm}</span></td>
                <td>${refWt >= 1 ? refWt.toFixed(2) + " kg" : (refWt * 1000).toFixed(0) + " g"}</td>
                <td class="font-mono fw-bold text-primary">${equivDose.toFixed(4)} mg/kg</td>
                <td class="font-mono">${totalDose.toFixed(3)} mg</td>
                <td class="font-mono text-secondary">${foldDiff.toFixed(2)}×</td>
            </tr>
        `;
    });

    tableBody.innerHTML = html;
    setText("matrix_source_label", `${doseMgKg} mg/kg in ${getSpeciesName(srcSpeciesId)}`);
}

/**
 * Evaluates volume rate against NC3Rs animal welfare guidelines
 */
function evaluateWelfareBadge(elementId, volPerKg, route) {
    const el = document.getElementById(elementId);
    if (!el) return;

    const limits = ROUTE_LIMITS[route] || ROUTE_LIMITS.oral_gavage;

    if (volPerKg <= limits.rec) {
        el.className = "welfare-badge-safe";
        el.innerHTML = `<i class="bi bi-check-circle-fill"></i> <strong>Safe (${volPerKg.toFixed(2)} mL/kg):</strong> Within standard ${limits.name} guidelines (≤ ${limits.rec} mL/kg).`;
    } else if (volPerKg <= limits.max) {
        el.className = "welfare-badge-warning";
        el.innerHTML = `<i class="bi bi-exclamation-triangle-fill"></i> <strong>Caution (${volPerKg.toFixed(2)} mL/kg):</strong> Exceeds standard comfort limit (≤ ${limits.rec} mL/kg). Monitor animal closely.`;
    } else {
        el.className = "welfare-badge-exceeded";
        el.innerHTML = `<i class="bi bi-x-octagon-fill"></i> <strong>Exceeded (${volPerKg.toFixed(2)} mL/kg):</strong> Exceeds maximum ethical limit (${limits.max} mL/kg)! Please increase drug concentration.`;
    }
}

/**
 * Apply predefined scientific preset
 */
function applyPreset(presetType) {
    switch (presetType) {
        case "mouse_10_human":
            switchToTab("tab-a2h");
            setValue("a2h_animal", "mouse");
            setValue("a2h_dose", "10.0");
            setValue("a2h_dose_unit", "mg_kg");
            setValue("a2h_animal_weight", "20");
            setValue("a2h_animal_weight_unit", "g");
            setValue("a2h_human_weight", "60.0");
            setValue("a2h_safety_factor", "10.0");
            calculateAnimalToHuman();
            break;
        case "rat_50_human":
            switchToTab("tab-a2h");
            setValue("a2h_animal", "rat");
            setValue("a2h_dose", "50.0");
            setValue("a2h_dose_unit", "mg_kg");
            setValue("a2h_animal_weight", "150");
            setValue("a2h_animal_weight_unit", "g");
            setValue("a2h_human_weight", "60.0");
            setValue("a2h_safety_factor", "10.0");
            calculateAnimalToHuman();
            break;
        case "human_500_mouse":
            switchToTab("tab-h2a");
            setValue("h2a_dose_type", "total_mg");
            setValue("h2a_human_dose", "500.0");
            setValue("h2a_human_weight", "60.0");
            setValue("h2a_target_animal", "mouse");
            setValue("h2a_animal_weight", "25");
            setValue("h2a_animal_weight_unit", "g");
            calculateHumanToAnimal();
            break;
        case "rabbit_20_rat":
            switchToTab("tab-a2a");
            setValue("a2a_source_animal", "rabbit");
            setValue("a2a_source_dose", "20.0");
            setValue("a2a_target_animal", "rat");
            setValue("a2a_target_weight", "200");
            setValue("a2a_target_weight_unit", "g");
            calculateAnimalToAnimal();
            break;
        case "dog_10_human":
            switchToTab("tab-a2h");
            setValue("a2h_animal", "dog");
            setValue("a2h_dose", "10.0");
            setValue("a2h_dose_unit", "mg_kg");
            setValue("a2h_animal_weight", "10");
            setValue("a2h_animal_weight_unit", "kg");
            setValue("a2h_human_weight", "60.0");
            setValue("a2h_safety_factor", "6.0");
            calculateAnimalToHuman();
            break;
        case "cohort_mouse_study":
            switchToTab("tab-cohort");
            setValue("ch_species", "mouse");
            setValue("ch_dose", "10.0");
            setValue("ch_count", "10");
            setValue("ch_avg_weight", "22");
            setValue("ch_weight_unit", "g");
            setValue("ch_freq", "1");
            setValue("ch_days", "14");
            setValue("ch_waste", "10.0");
            setValue("ch_conc", "1.0");
            calculateCohort();
            break;
    }
}

function switchToTab(tabId) {
    const tabTrigger = document.querySelector(`[data-bs-target="#${tabId}"]`);
    if (tabTrigger) {
        const tab = new bootstrap.Tab(tabTrigger);
        tab.show();
    }
}

/**
 * Copies text to clipboard with notification feedback
 */
function copyToClipboard(text, triggerBtn) {
    navigator.clipboard.writeText(text).then(() => {
        if (triggerBtn) {
            const originalHTML = triggerBtn.innerHTML;
            triggerBtn.innerHTML = `<i class="bi bi-check2"></i> Copied!`;
            setTimeout(() => {
                triggerBtn.innerHTML = originalHTML;
            }, 1800);
        }
    }).catch(err => {
        console.error("Clipboard copy failed:", err);
    });
}

function copyA2HSteps(btn) {
    const stepsEl = document.getElementById("a2h_steps_list");
    if (stepsEl) copyToClipboard(stepsEl.innerText, btn);
}

function copyH2ASteps(btn) {
    const stepsEl = document.getElementById("h2a_steps_list");
    if (stepsEl) copyToClipboard(stepsEl.innerText, btn);
}

function copyCohortSummary(btn) {
    const textEl = document.getElementById("ch_summary_text");
    if (textEl) copyToClipboard(textEl.innerText, btn);
}

// Mobile Floating Bar & Smooth Scroll
function updateMobileFloatingBar(label, value) {
    setText("mobile_bar_label", label);
    setText("mobile_bar_val", value);
}

function scrollToResultCard() {
    const activeTabPane = document.querySelector(".tab-pane.active");
    if (activeTabPane) {
        const resultCard = activeTabPane.querySelector(".result-card-primary");
        if (resultCard) {
            resultCard.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    }
}

// Helpers
function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.innerText = text;
}

function setValue(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val;
}

function renderSteps(containerId, steps) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = steps.map(s => `<div class="step-item">${s}</div>`).join("");
}

function getSpeciesName(spId) {
    const names = {
        human: "Human (Adult)",
        child: "Human (Child)",
        mouse: "Mouse",
        rat: "Rat",
        hamster: "Hamster",
        guinea_pig: "Guinea Pig",
        ferret: "Ferret",
        rabbit: "Rabbit",
        dog: "Dog (Beagle)",
        cat: "Cat",
        monkey_cynomolgus: "Monkey (Cynomolgus)",
        monkey_rhesus: "Monkey (Rhesus)",
        monkey_marmoset: "Monkey (Marmoset)",
        monkey_squirrel: "Monkey (Squirrel)",
        baboon: "Baboon",
        mini_pig: "Miniature Swine",
        micro_pig: "Micro-pig"
    };
    return names[spId] || spId.toUpperCase();
}

