# ResearchDose — Architecture & Design Specification

## 1. Architectural Philosophy
ResearchDose is engineered with a strict separation of concerns to ensure scientific reproducibility, numerical integrity, and maintainability:

```
+-------------------------------------------------------------+
|                     Presentation Layer                      |
|       Jinja2 Server-Rendered HTML + Bootstrap 5 + JS        |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
|                     FastAPI Web Layer                       |
|   Request Validation (Pydantic), Response Serializers, API  |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
|              Domain & Pure Calculation Engine               |
|      Dose Calculator, Unit Converter, Precision Handling    |
|   (Zero web/DB dependency; pure Python with Decimal math)   |
+-------------------------------------------------------------+
          |                                       |
+----------------------+              +-----------------------+
|  Species Provenance  |              | Local Storage Layer   |
| JSON Dataset & Rules |              | SQLite & SQLAlchemy   |
+----------------------+              +-----------------------+
```

## 2. Directory Layout
```
researchdose/
  app/
    __init__.py
    main.py                 # FastAPI app entry point & lifespan setup
    core/
      __init__.py
      config.py             # Settings, paths, versioning, disclaimers
    models/                 # SQLAlchemy ORM models (Workspace, History)
      __init__.py
    schemas/                # Pydantic V2 data validation models
      __init__.py
      species.py            # Laboratory species & reference citations
    services/               # Business logic & scientific algorithms
      __init__.py
      species_service.py    # Reference loading, validation, and lookup
    data/                   # Curated, verified scientific datasets
      species.json          # 13 verified species (FDA 2005) + custom profile
      references.json       # Authoritative peer-reviewed & regulatory citations
    database/               # SQLite connection & session factories
      __init__.py
    templates/              # Server-rendered Jinja2 UI templates
      base.html
    static/                 # UI assets
      css/main.css
      js/main.js
  tests/                    # Automated Pytest suite
    conftest.py
    test_species_schema.py
    test_app_scaffold.py
  docs/                     # Architectural & scientific documentation
    ARCHITECTURE.md
    SCIENTIFIC_METHODOLOGY.md
  .env.example
  .gitignore
  requirements.txt
  README.md
```

## 3. Strict Scientific Guardrails
1. **No Guessing**: A species without peer-reviewed verification is marked as `unverified` and its $K_m$ is stored as `null`. It cannot be used in BSA conversions until verified data is supplied.
2. **Precision Strategy**: Calculations utilize Python's `Decimal` type to prevent binary floating-point drift and guarantee exact step-by-step reproducibility.
3. **Audit Trail**: Every conversion computation retains full provenance (source species, target species, input units, raw factors, formula, timestamp, algorithm version, and literature citation).
