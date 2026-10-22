/**
 * ResearchDose — Simple & Scientific Preclinical Dose Converter
 * Fast, reactive client-side calculation engine
 */

// Standard reference Km factors (US FDA CDER 2005 Table 1)
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

// Route welfare guidelines (mL/kg max thresholds from NC3Rs)
const ROUTE_LIMITS = {
    oral_gavage: { rec: 10.0, max: 20.0, name: "Oral Gavage" },
    iv_bolus: { rec: 5.0, max: 10.0, name: "Intravenous (IV)" },
    ip: { rec: 10.0, max: 20.0, name: "Intraperitoneal (IP)" },
    sc: { rec: 5.0, max: 10.0, name: "Subcutaneous (SC)" }
};

document.addEventListener("DOMContentLoaded", () => {
    // Dynamic copyright year
    const yearEl = document.getElementById("copyrightYear");
    if (yearEl) {
        yearEl.textContent = new Date().getFullYear();
    }

    setupEventListeners();
    initPWA();
    calculateAnimalToHuman();
    calculateHumanToAnimal();
    calculateAnimalToAnimal();
    calculateFormulationOnly();
    calculateCohort();
    updateMultiSpeciesMatrix("rat", 10.0);
});

/**
 * Sets up all input listeners for real-time reactivity
 */
function setupEventListeners() {
    // Mode 1: Animal to Human
    const a2hInputs = ["a2h_animal", "a2h_dose", "a2h_dose_unit", "a2h_animal_weight", "a2h_animal_weight_unit", "a2h_human_weight", "a2h_safety_factor"];
    a2hInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("input", calculateAnimalToHuman);
    });

    const a2hAnimal = document.getElementById("a2h_animal");
    if (a2hAnimal) {
        a2hAnimal.addEventListener("change", () => {
            syncAnimalWeight("a2h_animal", "a2h_animal_weight", "a2h_animal_weight_unit");
            calculateAnimalToHuman();
        });
    }

    // Mode 2: Human to Animal
    const h2aInputs = ["h2a_human_dose", "h2a_dose_type", "h2a_target_animal", "h2a_human_weight", "h2a_animal_weight", "h2a_animal_weight_unit"];
    h2aInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("input", calculateHumanToAnimal);
    });

    const h2aAnimal = document.getElementById("h2a_target_animal");
    if (h2aAnimal) {
        h2aAnimal.addEventListener("change", () => {
            syncAnimalWeight("h2a_target_animal", "h2a_animal_weight", "h2a_animal_weight_unit");
            calculateHumanToAnimal();
        });
    }

    // Mode 3: Animal to Animal
    const a2aInputs = ["a2a_source_animal", "a2a_source_dose", "a2a_target_animal"];
    a2aInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("input", calculateAnimalToAnimal);
    });

    // Tool: Formulation
    const formInputs = ["form_animal_weight", "form_weight_unit", "form_dose", "form_conc", "form_route"];
    formInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("input", calculateFormulationOnly);
    });

    // Tool: Cohort
    const cohortInputs = ["ch_species", "ch_dose", "ch_count", "ch_days", "ch_freq", "ch_waste", "ch_conc"];
    cohortInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("input", calculateCohort);
    });

    // Tool: Matrix
    const matrixInputs = ["matrixSourceSpecies", "matrixSourceDose"];
    matrixInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("input", () => {
            const sp = document.getElementById("matrixSourceSpecies")?.value || "rat";
            const dose = parseFloat(document.getElementById("matrixSourceDose")?.value) || 10.0;
            updateMultiSpeciesMatrix(sp, dose);
        });
    });
}

function syncAnimalWeight(selectId, weightInputId, unitSelectId) {
    const spId = document.getElementById(selectId)?.value;
    const refWt = WEIGHT_TABLE[spId] || 0.15;
    const wtEl = document.getElementById(weightInputId);
    const unitEl = document.getElementById(unitSelectId);
    if (wtEl && unitEl) {
        if (refWt < 1.0) {
            unitEl.value = "g";
            wtEl.value = (refWt * 1000).toFixed(0);
        } else {
            unitEl.value = "kg";
            wtEl.value = refWt.toFixed(2);
        }
    }
}

/**
 * Quick Animal Chip selector
 */
function quickSelectA2H(animalId, defaultDose) {
    const selectEl = document.getElementById("a2h_animal");
    if (selectEl) {
        selectEl.value = animalId;
        syncAnimalWeight("a2h_animal", "a2h_animal_weight", "a2h_animal_weight_unit");
    }
    const doseEl = document.getElementById("a2h_dose");
    if (doseEl && defaultDose) {
        doseEl.value = defaultDose;
    }
    // Highlight selected chip
    document.querySelectorAll(".quick-chip").forEach(btn => {
        btn.classList.remove("btn-primary", "text-white");
        btn.classList.add("btn-outline-secondary");
    });
    if (event && event.currentTarget) {
        event.currentTarget.classList.remove("btn-outline-secondary");
        event.currentTarget.classList.add("btn-primary", "text-white");
    }
    calculateAnimalToHuman();
}

/**
 * 1. Animal to Human Calculation (HED)
 */
function calculateAnimalToHuman() {
    const spId = document.getElementById("a2h_animal")?.value || "rat";
    const doseRaw = parseFloat(document.getElementById("a2h_dose")?.value) || 0;
    const doseUnit = document.getElementById("a2h_dose_unit")?.value || "mg_kg";
    const humanWt = parseFloat(document.getElementById("a2h_human_weight")?.value) || 60.0;
    const safetyFactor = parseFloat(document.getElementById("a2h_safety_factor")?.value) || 1.0;

    if (doseRaw <= 0) return;

    // Normalize dose to mg/kg
    let doseMgKg = doseRaw;
    if (doseUnit === "ug_kg") doseMgKg = doseRaw / 1000.0;
    if (doseUnit === "g_kg") doseMgKg = doseRaw * 1000.0;

    const sourceKm = KM_TABLE[spId] || 6.0;
    const humanKm = KM_TABLE.human; // 37.0

    // FDA Allometric Formula: HED = Dose * (Km_animal / Km_human)
    const kmRatio = sourceKm / humanKm;
    const hedMgKg = doseMgKg * kmRatio;
    const totalHumanMg = hedMgKg * humanWt;

    // Display numbers
    setText("a2h_result_hed", hedMgKg.toFixed(4));
    setText("a2h_result_total", totalHumanMg.toFixed(2) + " mg");
    setText("a2h_result_ratio", kmRatio.toFixed(4));
    setText("a2h_human_wt_tag", `For ${humanWt} kg Adult`);

    // Plain English explanation
    const animalName = getSpeciesName(spId);
    const explanationEl = document.getElementById("a2h_explanation");
    if (explanationEl) {
        explanationEl.innerHTML = `
            <i class="bi bi-lightbulb-fill text-info flex-shrink-0 fs-5"></i>
            <div>
                A <strong>${doseRaw} ${doseUnit === 'mg_kg' ? 'mg/kg' : doseUnit}</strong> dose in a <strong>${animalName}</strong> equals <strong>${hedMgKg.toFixed(4)} mg/kg</strong> in an adult Human.<br>
                Total compound required for a ${humanWt} kg person: <strong>${totalHumanMg.toFixed(2)} mg</strong>.
            </div>
        `;
    }

    // Clinical MRSD safety margin
    const mrsdBox = document.getElementById("a2h_mrsd_box");
    if (mrsdBox) {
        if (safetyFactor > 1.0) {
            mrsdBox.classList.remove("d-none");
            const mrsdDose = hedMgKg / safetyFactor;
            const mrsdTotal = totalHumanMg / safetyFactor;
            setText("a2h_mrsd_val", mrsdDose.toFixed(4) + " mg/kg");
            setText("a2h_mrsd_total", mrsdTotal.toFixed(2) + " mg");
        } else {
            mrsdBox.classList.add("d-none");
        }
    }
}

/**
 * 2. Human to Animal Calculation
 */
function calculateHumanToAnimal() {
    const doseType = document.getElementById("h2a_dose_type")?.value || "mg_kg";
    const humanDoseRaw = parseFloat(document.getElementById("h2a_human_dose")?.value) || 0;
    const humanWt = parseFloat(document.getElementById("h2a_human_weight")?.value) || 60.0;
    const targetSp = document.getElementById("h2a_target_animal")?.value || "mouse";
    const animalWtRaw = parseFloat(document.getElementById("h2a_animal_weight")?.value) || 20;
    const animalWtUnit = document.getElementById("h2a_animal_weight_unit")?.value || "g";

    if (humanDoseRaw <= 0) return;

    let humanMgKg = humanDoseRaw;
    if (doseType === "total_mg") {
        humanMgKg = humanDoseRaw / humanWt;
    }

    const animalWtKg = animalWtUnit === "g" ? animalWtRaw / 1000.0 : animalWtRaw;
    const humanKm = KM_TABLE.human; // 37.0
    const targetKm = KM_TABLE[targetSp] || 3.0;

    const kmRatio = humanKm / targetKm;
    const animalDoseMgKg = humanMgKg * kmRatio;
    const animalTotalMg = animalDoseMgKg * animalWtKg;

    setText("h2a_result_dose", animalDoseMgKg.toFixed(2));
    setText("h2a_result_total", animalTotalMg.toFixed(3) + " mg");
    setText("h2a_result_ratio", kmRatio.toFixed(2) + "×");

    const targetName = getSpeciesName(targetSp);
    const explanationEl = document.getElementById("h2a_explanation");
    if (explanationEl) {
        explanationEl.innerHTML = `
            <i class="bi bi-lightbulb-fill text-info flex-shrink-0 fs-5"></i>
            <div>
                A <strong>${humanDoseRaw} ${doseType === 'total_mg' ? 'total mg' : 'mg/kg'}</strong> human dose translates to <strong>${animalDoseMgKg.toFixed(2)} mg/kg</strong> in <strong>${targetName}</strong> due to higher small-mammal metabolic rate.
            </div>
        `;
    }
}

/**
 * 3. Animal to Animal Calculation
 */
function calculateAnimalToAnimal() {
    const srcSp = document.getElementById("a2a_source_animal")?.value || "mouse";
    const srcDose = parseFloat(document.getElementById("a2a_source_dose")?.value) || 0;
    const tgtSp = document.getElementById("a2a_target_animal")?.value || "rat";

    if (srcDose <= 0) return;

    const srcKm = KM_TABLE[srcSp] || 3.0;
    const tgtKm = KM_TABLE[tgtSp] || 6.0;
    const kmRatio = srcKm / tgtKm;
    const tgtDose = srcDose * kmRatio;

    const refWt = WEIGHT_TABLE[tgtSp] || 0.15;
    const tgtTotalMg = tgtDose * refWt;

    setText("a2a_result_dose", tgtDose.toFixed(2));
    setText("a2a_result_total", tgtTotalMg.toFixed(2) + " mg");
    setText("a2a_result_ratio", kmRatio.toFixed(4));

    const srcName = getSpeciesName(srcSp);
    const tgtName = getSpeciesName(tgtSp);
    const expEl = document.getElementById("a2a_explanation");
    if (expEl) {
        expEl.innerHTML = `
            <i class="bi bi-lightbulb-fill text-info flex-shrink-0 fs-5"></i>
            <div>
                <strong>${srcDose} mg/kg</strong> in <strong>${srcName}</strong> translates to <strong>${tgtDose.toFixed(2)} mg/kg</strong> in <strong>${tgtName}</strong>.
            </div>
        `;
    }
}

/**
 * 4. Formulation & Volume Calculator
 */
function calculateFormulationOnly() {
    const wtRaw = parseFloat(document.getElementById("form_animal_weight")?.value) || 150;
    const wtUnit = document.getElementById("form_weight_unit")?.value || "g";
    const doseMgKg = parseFloat(document.getElementById("form_dose")?.value) || 20;
    const conc = parseFloat(document.getElementById("form_conc")?.value) || 5;
    const route = document.getElementById("form_route")?.value || "oral_gavage";

    if (doseMgKg <= 0 || conc <= 0 || wtRaw <= 0) return;

    const wtKg = wtUnit === "g" ? wtRaw / 1000.0 : wtRaw;
    const totalDoseMg = doseMgKg * wtKg;
    const volMl = totalDoseMg / conc;
    const volUl = volMl * 1000.0;
    const volPerKg = volMl / wtKg;

    setText("form_vol_ml", volMl.toFixed(2) + " mL");
    setText("form_vol_ul", "(" + volUl.toFixed(1) + " µL)");

    const limits = ROUTE_LIMITS[route] || ROUTE_LIMITS.oral_gavage;
    const badge = document.getElementById("form_welfare_badge");
    const title = document.getElementById("form_welfare_title");
    const msg = document.getElementById("form_welfare_msg");

    if (badge && title && msg) {
        if (volPerKg <= limits.rec) {
            badge.className = "p-2 rounded-3 mb-2 bg-success-subtle text-success border border-success-subtle";
            title.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i> Volume Safe (${volPerKg.toFixed(1)} mL/kg)`;
            msg.innerText = `Within recommended NC3Rs guideline of ≤ ${limits.rec} mL/kg for ${limits.name}.`;
        } else if (volPerKg <= limits.max) {
            badge.className = "p-2 rounded-3 mb-2 bg-warning-subtle text-warning-emphasis border border-warning-subtle";
            title.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-1"></i> Caution (${volPerKg.toFixed(1)} mL/kg)`;
            msg.innerText = `Exceeds recommended comfort limit (${limits.rec} mL/kg). Ethical max is ${limits.max} mL/kg.`;
        } else {
            badge.className = "p-2 rounded-3 mb-2 bg-danger-subtle text-danger border border-danger-subtle";
            title.innerHTML = `<i class="bi bi-x-circle-fill me-1"></i> Limit Exceeded (${volPerKg.toFixed(1)} mL/kg)`;
            msg.innerText = `Exceeds ethical animal welfare limit (${limits.max} mL/kg). Increase drug concentration.`;
        }
    }
}

/**
 * 5. Cohort Study Bulk Drug Planner
 */
function calculateCohort() {
    const spId = document.getElementById("ch_species")?.value || "rat";
    const dose = parseFloat(document.getElementById("ch_dose")?.value) || 20;
    const count = parseInt(document.getElementById("ch_count")?.value) || 10;
    const days = parseInt(document.getElementById("ch_days")?.value) || 14;
    const freq = parseInt(document.getElementById("ch_freq")?.value) || 1;
    const wastePct = parseFloat(document.getElementById("ch_waste")?.value) || 10;
    const conc = parseFloat(document.getElementById("ch_conc")?.value) || 5;

    if (dose <= 0 || count <= 0) return;

    const refWt = WEIGHT_TABLE[spId] || 0.15;
    const singleDoseMg = dose * refWt;
    const dailyTotalMg = singleDoseMg * count * freq;
    const studyNetMg = dailyTotalMg * days;
    const totalMg = studyNetMg * (1.0 + wastePct / 100.0);
    const totalG = totalMg / 1000.0;
    const totalVolMl = totalMg / conc;
    const singleVolMl = singleDoseMg / conc;

    setText("ch_res_total_mg", totalMg.toFixed(2) + " mg");
    setText("ch_res_total_g", `(${totalG.toFixed(3)} g active compound)`);
    setText("ch_res_total_vol", totalVolMl.toFixed(1) + " mL");
    setText("ch_res_dose_per_animal", singleDoseMg.toFixed(2) + " mg");
    setText("ch_res_vol_per_animal", singleVolMl.toFixed(2) + " mL");
}

/**
 * 6. Multi-Species Realtime Matrix
 */
function updateMultiSpeciesMatrix(srcSpeciesId, doseMgKg) {
    const tbody = document.getElementById("matrixTableBody");
    if (!tbody) return;

    const srcKm = KM_TABLE[srcSpeciesId] || 6.0;
    let html = "";

    const speciesCategories = {
        human: "Human",
        child: "Human (Child)",
        mouse: "Rodent",
        rat: "Rodent",
        hamster: "Rodent",
        guinea_pig: "Rodent",
        rabbit: "Lagomorph",
        ferret: "Carnivore",
        dog: "Carnivore",
        cat: "Carnivore",
        monkey_cynomolgus: "Primate",
        monkey_rhesus: "Primate",
        monkey_marmoset: "Primate",
        mini_pig: "Swine",
        micro_pig: "Swine"
    };

    Object.keys(speciesCategories).forEach(spKey => {
        const spKm = KM_TABLE[spKey];
        const refWt = WEIGHT_TABLE[spKey];
        const equivDose = doseMgKg * (srcKm / spKm);
        const totalMass = equivDose * refWt;
        const isCurrent = spKey === srcSpeciesId;

        html += `
            <tr class="${isCurrent ? 'table-primary fw-bold' : ''}">
                <td>${getSpeciesName(spKey)} ${isCurrent ? '<span class="badge bg-primary ms-1">Source</span>' : ''}</td>
                <td><span class="badge bg-light text-dark border">${speciesCategories[spKey]}</span></td>
                <td>${refWt >= 1 ? refWt.toFixed(2) + " kg" : (refWt * 1000).toFixed(0) + " g"}</td>
                <td><span class="badge bg-secondary-subtle text-secondary-emphasis">${spKm}</span></td>
                <td class="fw-bold text-primary">${equivDose.toFixed(4)} mg/kg</td>
                <td>${totalMass.toFixed(2)} mg</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

/**
 * Copy Result to Clipboard with Toast Notification
 */
function copyResult(mode) {
    let copyText = "";
    if (mode === "a2h") {
        const animal = getSpeciesName(document.getElementById("a2h_animal")?.value || "rat");
        const dose = document.getElementById("a2h_dose")?.value;
        const hed = document.getElementById("a2h_result_hed")?.innerText;
        const total = document.getElementById("a2h_result_total")?.innerText;
        copyText = `ResearchDose Conversion:\nAnimal: ${animal} (${dose} mg/kg)\nHuman Equivalent Dose (HED): ${hed} mg/kg\nTotal Human Dose: ${total} (60 kg adult)\nStandard: US FDA CDER 2005 Table 1`;
    } else if (mode === "h2a") {
        const humanDose = document.getElementById("h2a_human_dose")?.value;
        const animal = getSpeciesName(document.getElementById("h2a_target_animal")?.value || "mouse");
        const dose = document.getElementById("h2a_result_dose")?.innerText;
        const total = document.getElementById("h2a_result_total")?.innerText;
        copyText = `ResearchDose Translation:\nHuman Dose: ${humanDose} mg/kg\nTarget Animal: ${animal} (${dose} mg/kg)\nPer Animal Dose: ${total}\nStandard: Allometric Km Scaling`;
    } else if (mode === "a2a") {
        const srcAnimal = getSpeciesName(document.getElementById("a2a_source_animal")?.value || "mouse");
        const srcDose = document.getElementById("a2a_source_dose")?.value;
        const tgtAnimal = getSpeciesName(document.getElementById("a2a_target_animal")?.value || "rat");
        const tgtDose = document.getElementById("a2a_result_dose")?.innerText;
        copyText = `ResearchDose Interspecies:\nSource: ${srcAnimal} (${srcDose} mg/kg)\nTarget: ${tgtAnimal} (${tgtDose} mg/kg)`;
    }

    navigator.clipboard.writeText(copyText).then(() => {
        const toastEl = document.getElementById("copyToast");
        if (toastEl && window.bootstrap) {
            const toast = new bootstrap.Toast(toastEl, { delay: 2500 });
            toast.show();
        }
    }).catch(err => {
        console.error("Failed to copy:", err);
    });
}

// Helpers
function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.innerText = text;
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
    return names[spId] || spId;
}

// ==========================================
// Progressive Web App (PWA) Support Engine
// ==========================================
let deferredInstallPrompt = null;

function initPWA() {
    registerServiceWorker();
    setupPwaInstallPrompt();
    setupNetworkStatusMonitoring();
}

/**
 * Registers the Service Worker for offline capability
 */
function registerServiceWorker() {
    if ("serviceWorker" in navigator) {
        window.addEventListener("load", () => {
            navigator.serviceWorker
                .register("/sw.js", { scope: "/" })
                .then((registration) => {
                    console.log("[PWA] Service Worker registered successfully with scope:", registration.scope);
                })
                .catch((error) => {
                    console.warn("[PWA] Service Worker registration failed:", error);
                });
        });
    }
}

/**
 * Sets up beforeinstallprompt and user install actions
 */
function setupPwaInstallPrompt() {
    const installBtn = document.getElementById("btnInstallPwa");
    if (!installBtn) return;

    const isRunningStandalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
    if (isRunningStandalone) {
        // App is already installed and running standalone
        installBtn.classList.add("d-none");
        return;
    }

    // Android, Chrome, Edge beforeinstallprompt event
    window.addEventListener("beforeinstallprompt", (e) => {
        // Prevent default mini-infobar
        e.preventDefault();
        deferredInstallPrompt = e;

        // Reveal the Install App button
        installBtn.classList.remove("d-none");
        installBtn.classList.add("d-inline-flex");
    });

    // iOS Safari detection
    const isIOSDevice = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    if (isIOSDevice && !isRunningStandalone) {
        installBtn.classList.remove("d-none");
        installBtn.classList.add("d-inline-flex");
    }

    // Button click handler
    installBtn.addEventListener("click", async () => {
        if (deferredInstallPrompt) {
            // Native install prompt (Chrome / Android / Edge)
            deferredInstallPrompt.prompt();
            const choiceResult = await deferredInstallPrompt.userChoice;
            if (choiceResult.outcome === "accepted") {
                console.log("[PWA] User accepted the install prompt");
                installBtn.classList.add("d-none");
            }
            deferredInstallPrompt = null;
        } else if (isIOSDevice) {
            // Show iOS modal instructions
            const modalEl = document.getElementById("iosInstallModal");
            if (modalEl && typeof bootstrap !== "undefined") {
                const modal = new bootstrap.Modal(modalEl);
                modal.show();
            } else {
                alert("To install on iOS: Tap Share and select 'Add to Home Screen'.");
            }
        } else {
            // General desktop fallback info
            alert("To install ResearchDose: Click the install icon in your browser's address bar (or Menu > Install ResearchDose).");
        }
    });

    // Listen for successful installation
    window.addEventListener("appinstalled", () => {
        console.log("[PWA] ResearchDose installed successfully!");
        installBtn.classList.add("d-none");
        deferredInstallPrompt = null;
    });
}

/**
 * Monitors and displays network status (Online / Offline mode)
 */
function setupNetworkStatusMonitoring() {
    const badge = document.getElementById("networkStatusBadge");
    const textEl = document.getElementById("networkStatusText");
    const dotEl = document.getElementById("networkStatusDot");
    const offlineToast = document.getElementById("pwaOfflineToast");

    function updateStatus(isOnline) {
        if (!badge || !textEl || !dotEl) return;

        if (isOnline) {
            badge.className = "badge bg-success-subtle text-success border border-success-subtle d-flex align-items-center gap-1 px-2 py-1";
            dotEl.className = "spinner-grow spinner-grow-sm text-success";
            textEl.textContent = "Online";
            if (offlineToast) {
                offlineToast.classList.add("d-none");
                offlineToast.classList.remove("d-flex");
            }
        } else {
            badge.className = "badge bg-warning-subtle text-warning border border-warning-subtle d-flex align-items-center gap-1 px-2 py-1";
            dotEl.className = "spinner-grow spinner-grow-sm text-warning";
            textEl.textContent = "Offline Mode";
            if (offlineToast) {
                offlineToast.classList.remove("d-none");
                offlineToast.classList.add("d-flex");
                setTimeout(() => {
                    if (offlineToast) {
                        offlineToast.classList.add("d-none");
                        offlineToast.classList.remove("d-flex");
                    }
                }, 4500);
            }
        }
    }

    window.addEventListener("online", () => updateStatus(true));
    window.addEventListener("offline", () => updateStatus(false));

    // Initial check
    updateStatus(navigator.onLine);
}

