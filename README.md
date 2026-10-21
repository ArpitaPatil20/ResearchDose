# ResearchDose — Scientific Dose Conversion & Research Platform

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-e92063.svg)](https://docs.pydantic.dev/)
[![Status](https://img.shields.io/badge/Status-Phase%201%20%26%202%20Complete-green.svg)]()

ResearchDose is a modern, scientifically responsible web application for preclinical pharmacological research. It supports interspecies dose translation based on Body Surface Area (BSA) / $K_m$ normalization, weight-based scaling, laboratory species databases, and transparent calculation provenance.

Inspired by standard scientific tools such as **CFTRI DoseCal** and **ICMR-NIPCR DoseMate**, ResearchDose emphasizes:
- **Scientific Provenance**: Every baseline value links directly to published peer-reviewed literature or regulatory guidance.
- **Data Integrity**: Unknown conversion factors are treated as unavailable, not zero.
- **Explicit Assumptions**: Step-by-step arithmetic, method limitations, and formulas are displayed beside results.
- **Safety First**: Clear warnings that mathematical equivalency does not guarantee clinical safety or efficacy.

---

## Scientific Principles & Formulas

### 1. Interspecies BSA ($K_m$) Normalization
$$\text{Target Dose (mg/kg)} = \text{Source Dose (mg/kg)} \times \frac{K_m(\text{source})}{K_m(\text{target})}$$

Where $K_m = \frac{\text{Body Weight (kg)}}{\text{Body Surface Area (m}^2\text{)}}$.

### 2. Total Administered Dose
$$\text{Total Dose (mg)} = \text{Dose (mg/kg)} \times \text{Body Weight (kg)}$$

### 3. Formulation Volume
$$\text{Volume (mL)} = \frac{\text{Total Dose (mg)}}{\text{Concentration (mg/mL)}}$$

---

## Laboratory Species & $K_m$ Reference (FDA 2005 Table 1)

| Species | Category | Reference Body Weight | $K_m$ Factor | Status |
|---|---|---|---|---|
| **Human (Adult)** | Human | 60 kg | 37 | Verified |
| **Human (Child)** | Human | 20 kg | 25 | Verified |
| **Mouse** | Rodent | 0.02 kg (20 g) | 3 | Verified |
| **Rat** | Rodent | 0.15 kg (150 g) | 6 | Verified |
| **Hamster** | Rodent | 0.08 kg (80 g) | 5 | Verified |
| **Guinea Pig** | Rodent | 0.40 kg (400 g) | 8 | Verified |
| **Ferret** | Carnivore | 0.30 kg (300 g) | 7 | Verified |
| **Rabbit** | Lagomorph | 1.80 kg | 12 | Verified |
| **Cat** | Carnivore | 2.0 kg | 12 | Verified |
| **Dog (Beagle)** | Carnivore | 10.0 kg | 20 | Verified |
| **Monkey (Cynomolgus)** | Nonhuman Primate | 2.40 kg | 12 | Verified |
| **Monkey (Rhesus)** | Nonhuman Primate | 3.20 kg | 12 | Verified |
| **Monkey (Marmoset)** | Nonhuman Primate | 0.35 kg (350 g) | 6 | Verified |
| **Miniature Swine** | Non-rodent Ungulate | 20.0 kg | 27 | Verified |
| **Micro-pig** | Non-rodent Ungulate | 8.0 kg | 21 | Verified |
| **Custom Profile** | Custom | User-defined | *None* | Unverified |

---

## Project Structure

```
researchdose/
├── app/
│   ├── api/                 # API routers and endpoints
│   ├── core/                # Configuration and environment settings
│   │   └── config.py
│   ├── data/                # Verified reference datasets (JSON)
│   │   ├── references.json
│   │   └── species.json
│   ├── database/            # SQLite & SQLAlchemy models and session
│   ├── models/              # Research workspace database models
│   ├── schemas/             # Pydantic validation schemas
│   │   └── species.py
│   ├── services/            # Pure calculation & data services
│   │   └── species_service.py
│   ├── static/              # CSS, JS, and UI assets
│   ├── templates/           # Jinja2 HTML templates
│   └── main.py              # Application entry point
├── docs/                    # Architectural & scientific specifications
│   ├── ARCHITECTURE.md
│   └── SCIENTIFIC_METHODOLOGY.md
├── tests/                   # Automated pytest suite
│   ├── conftest.py
│   ├── test_app_scaffold.py
│   └── test_species_schema.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Quickstart (Windows PowerShell)

### 1. Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Run Automated Tests
```powershell
pytest -v
```

### 4. Start Local Development Server
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Open your browser at `http://127.0.0.1:8000/` or `http://127.0.0.1:8000/docs` to inspect the interactive Swagger API documentation.

### 5. Generate a Public Shareable Link (Anyone Can View)
To share this website with colleagues, team members, or open it on your mobile phone:
```powershell
.\start_public_share.bat
```
or run Cloudflare Quick Tunnel manually:
```powershell
.\cloudflared.exe tunnel --url http://127.0.0.1:8000
```
This generates an instant, secure HTTPS public URL (e.g., `https://harbor-gdp-tops-pairs.trycloudflare.com`) that anyone can open from any device without installation or login.

---

## Deploying Permanently to the Cloud (Free)

If you want the website to be online 24/7 without keeping your computer running:

### Option A: Render.com (Recommended - 100% Free)
1. Push this repository to GitHub.
2. Sign up at [render.com](https://render.com) (free).
3. Click **New +** -> **Web Service** -> Connect your GitHub repo.
4. Set:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Click **Create Web Service**. You get a free permanent URL: `https://your-app.onrender.com`.

### Option B: Railway.app / Fly.io / Hugging Face Spaces
- Standard Dockerfile or Procfile with `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

---


## Regulatory and Scientific Safety Disclaimer
> **IMPORTANT**: ResearchDose is an academic calculation and educational tool intended for preclinical research and pharmacological experimental design. Interspecies dose conversion using Body Surface Area (BSA) normalization provides a mathematical estimate of equivalent systemic exposure. **It DOES NOT establish clinical safety, efficacy, or starting doses for clinical trials.** Human trials require determination of the No Observed Adverse Effect Level (NOAEL) in appropriate animal species, pharmacodynamic evaluations, and application of a safety margin (typically $\ge 10$-fold) in compliance with FDA CDER (2005) or ICH S9 guidance.

---

## 📄 Copyright & License

**Copyright &copy; 2026 Atharv Kanase / ResearchDose. All Rights Reserved.**

This platform, including its calculation engine, responsive scientific interface, verified animal species datasets, and automated cohort scaling modules, is designed and developed by **Atharv Kanase**.

- **License**: Released under the [MIT License](LICENSE) for research, academic, and scientific education.
- **Scientific Attribution**: Reference $K_m$ factors and body weights are standardized from US FDA CDER (2005) guidance, Reagan-Shaw et al. (2008), and Janhavi et al. (2022).
- **Academic Citation**:
  ```bibtex
  @software{researchdose2026,
    author = {Atharv Kanase},
    title = {ResearchDose: Preclinical Interspecies Dose Conversion & Research Platform},
    year = {2026},
    url = {https://github.com/AtharvKanase/ResearchDose}
  }
  ```


