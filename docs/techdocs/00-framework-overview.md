# Legacy Database Modernisation Framework
## Tooling Suite - Technical Overview

## Executive Summary

This document provides a technical overview of the four proprietary tools that comprise the Legacy Database Modernisation Framework. These tools work together to enable rapid, safe modernisation of legacy systems in regulated industries.

**Business Model**: Services-first, transitioning to licensed product sales. Tools are distributed as compiled Python binaries (Nuitka) with license key validation. Target exit at €500K+ ARR.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LEGACY DATABASE MODERNISATION FRAMEWORK                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Stage 1              Stage 2              Stage 3              Stage 4    │
│  ┌─────────┐         ┌─────────┐         ┌─────────┐         ┌─────────┐   │
│  │Database │  JSON   │  API    │ OpenAPI │   UI    │         │  Logic  │   │
│  │ Insight │────────▶│  Forge  │────────▶│  Forge  │         │ Mapper  │   │
│  └─────────┘         └─────────┘         └─────────┘         └─────────┘   │
│       │                   │                   │                    │        │
│       ▼                   ▼                   ▼                    ▼        │
│  Schema Docs         .NET Core API       React App           Logic         │
│  Gap Analysis        (V1) / Java (V2)    CRUD Interface      Inventory     │
│  Dependency Map      Audit Trails        Type-safe           Migration     │
│                      OpenAPI Spec                            Scaffolding   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Tool Summary

| Tool | Purpose | Input | Output | V1 Scope |
|------|---------|-------|--------|----------|
| **Database Insight** | Schema analysis & documentation | Oracle DB / Toad DDL / JSON | JSON Schema, HTML Docs, Gap Report | Oracle + Toad import |
| **API Forge** | REST API generation | Schema JSON | .NET Core Project, OpenAPI Spec | .NET Core |
| **UI Forge** | UI generation | OpenAPI Spec | HTML/CSS/JS Application | Plain JS |
| **Logic Mapper** | Legacy code analysis | Source Code | Logic Inventory, Migration Scaffolding | ASP/VBScript, PL/SQL |

## Database Insight Input Modes

| Mode | Description | Credentials Required | Best For |
|------|-------------|---------------------|----------|
| **Live** | Direct Oracle connection | Yes | Full extraction, indexes, FKs |
| **Toad DDL** | Parse Toad export .sql file | No | Existing exports, air-gapped |
| **JSON** | Import our JSON format | No | SaaS, customer-extracted |

## Version Roadmap

| Tool | V1 | V2 |
|------|----|----|
| **Database Insight** | Oracle (live + Toad import) | + SQL Server |
| **API Forge** | .NET Core 8 | + Java Spring Boot |
| **UI Forge** | Plain HTML/CSS/JS | + Vue.js |
| **Logic Mapper** | ASP/VBScript, PL/SQL | + T-SQL, Java |

## Data Flow Between Tools

```
                            ┌─────────────────┐
                            │  Legacy         │
                            │  Database       │
                            └────────┬────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │   Database Insight   │
                          └──────────┬───────────┘
                                     │
                        ┌────────────┴────────────┐
                        │                         │
                        ▼                         ▼
              ┌─────────────────┐      ┌─────────────────┐
              │   schema.json   │      │  Schema Docs    │
              └────────┬────────┘      │  Gap Report     │
                       │               └─────────────────┘
                       │
                       ├─────────────────────────────┐
                       │                             │
                       ▼                             ▼
            ┌──────────────────────┐     ┌──────────────────────┐
            │      API Forge       │     │    Logic Mapper      │◀── Legacy Code
            └──────────┬───────────┘     └──────────┬───────────┘
                       │                            │
          ┌────────────┴────────────┐              │
          │                         │              │
          ▼                         ▼              ▼
┌─────────────────┐      ┌─────────────────┐  ┌─────────────────┐
│  .NET Core API  │      │  openapi.json   │  │ Logic Inventory │
│  Project        │      └────────┬────────┘  │ Migration Plan  │
└─────────────────┘               │           └─────────────────┘
                                  │
                                  ▼
                       ┌──────────────────────┐
                       │      UI Forge        │
                       └──────────┬───────────┘
                                  │
                                  ▼
                       ┌─────────────────┐
                       │  React App      │
                       └─────────────────┘
```

## Shared Infrastructure

### Common Python Project Configuration

All tools share a common project structure using Poetry:

```toml
# pyproject.toml
[tool.poetry]
name = "tool-name"
version = "1.0.0"
description = "Tool description"
authors = ["Your Name <you@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
pydantic = "^2.5"
typer = "^0.9"
jinja2 = "^3.1"
rich = "^13.0"  # Pretty console output

[tool.poetry.group.dev.dependencies]
pytest = "^7.4"
pytest-asyncio = "^0.21"
ruff = "^0.1"  # Linting
mypy = "^1.7"  # Type checking

[tool.poetry.scripts]
tool-name = "tool_name.cli:app"
```

### Common Project Structure

```
tool-name/
├── pyproject.toml
├── README.md
├── LICENSE
│
├── tool_name/
│   ├── __init__.py
│   ├── __main__.py           # Entry point
│   ├── cli.py                # Typer CLI commands
│   ├── config.py             # Configuration loading
│   ├── license.py            # License validation
│   │
│   ├── models/               # Pydantic models
│   │   └── ...
│   │
│   ├── core/                 # Core business logic
│   │   └── ...
│   │
│   ├── generators/           # Output generators
│   │   └── ...
│   │
│   └── templates/            # Jinja2 templates
│       └── ...
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── ...
```

### Common Dependencies

```toml
# Shared across all tools
pydantic = "^2.5"      # Data validation
typer = "^0.9"         # CLI framework
jinja2 = "^3.1"        # Templating
rich = "^13.0"         # Console output
httpx = "^0.25"        # HTTP client (for license server)
```

### Error Handling Pattern

All tools use consistent error handling:

```python
# Shared error base class
class ToolError(Exception):
    """Base exception for all tools"""
    def __init__(self, message: str, code: str, context: dict = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}

# Tool-specific errors extend this
class DatabaseInsightError(ToolError):
    pass

class ApiForgeError(ToolError):
    pass
```

### CLI Pattern

All tools use Typer with consistent patterns:

```python
#!/usr/bin/env python3
import typer
from rich.console import Console

app = typer.Typer(help="Tool description")
console = Console()

@app.command()
def main_command(
    input_path: Path = typer.Option(..., "--input", "-i"),
    output_path: Path = typer.Option(..., "--output", "-o"),
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
):
    """Main command description."""
    # Validate license first
    from .license import validate_license
    validate_license()
    
    # Then run command
    console.print("[green]Processing...[/green]")
    # ...

if __name__ == "__main__":
    app()
```

### License Validation (Shared)

```python
# shared/license.py - Used by all tools
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional
import httpx

class LicenseValidator:
    LICENSE_SERVER = "https://license.yourcompany.com/validate"
    
    def __init__(self, license_file: Optional[Path] = None):
        self.license_file = license_file or Path.home() / ".modernisation-framework" / "license.key"
    
    def validate(self) -> bool:
        """Validate license - tries online first, falls back to offline."""
        license_data = self._load_license()
        
        # Try online validation (annual check)
        if self._should_check_online(license_data):
            try:
                self._validate_online(license_data)
            except httpx.RequestError:
                # Offline grace period
                if not self._within_grace_period(license_data):
                    raise LicenseError("License validation failed - please connect to internet", "OFFLINE_EXPIRED")
        
        # Verify local signature and expiry
        self._validate_offline(license_data)
        return True
    
    def _validate_offline(self, data: dict) -> None:
        """Verify signature and check expiry."""
        # Check expiry
        expiry = datetime.fromisoformat(data['expires'])
        if datetime.now() > expiry:
            raise LicenseError("License expired", "LICENSE_EXPIRED")
        
        # Verify signature (simplified - real implementation uses RSA)
        # ...
```

## Development Roadmap

### Phase 1: Foundation (Weeks 1-4)
**Goal**: Database Insight MVP

- Week 1-2: Core infrastructure, Oracle adapter
- Week 3: Schema extraction, JSON output
- Week 4: Audit rules engine, HTML documentation

**Deliverable**: Working Database Insight for Oracle databases

### Phase 2: API Generation (Weeks 5-8)
**Goal**: API Forge MVP

- Week 5-6: Schema parser, entity generation
- Week 7-8: Controller generation, audit patterns

**Deliverable**: Generate .NET Core API from Database Insight output

### Phase 3: UI Generation (Weeks 9-12)
**Goal**: UI Forge MVP

- Week 9-10: OpenAPI parser, component library
- Week 11-12: CRUD generation, routing

**Deliverable**: Generate React UI from API Forge output

### Phase 4: Logic Analysis (Weeks 13-18)
**Goal**: Logic Mapper MVP

- Week 13-15: ASP/VBScript parser
- Week 16-17: AI integration, rule extraction
- Week 18: Migration scaffolding

**Deliverable**: Analyze legacy code, generate migration plan

### Phase 5: Polish & Integration (Weeks 19-22)
**Goal**: Production-ready suite

- Week 19-20: Additional database support (SQL Server)
- Week 21: End-to-end testing
- Week 22: Documentation, packaging

**Deliverable**: Complete, tested tooling suite

## Development Guidelines

### Code Quality Standards

1. **TypeScript Strict Mode**: All code must pass strict type checking
2. **Test Coverage**: Minimum 80% coverage for core logic
3. **Documentation**: JSDoc comments on all public APIs
4. **Linting**: ESLint with recommended rules

### Git Workflow

1. `main` branch is always deployable
2. Feature branches: `feature/tool-name/description`
3. Pull requests require review and passing tests
4. Semantic versioning for releases

### Testing Requirements

1. **Unit Tests**: All pure functions
2. **Integration Tests**: Database connections, file generation
3. **Snapshot Tests**: Generated code output
4. **Manual Testing**: Full pipeline with sample project

## Claude Code Integration

These tools are designed to be developed using Claude Code. Recommended approach:

### Starting a New Tool

```bash
# Initialize project with Poetry
mkdir database-insight && cd database-insight
poetry init

# Have Claude Code set up the project
# Prompt: "Set up a Python project with Poetry, Typer CLI,
# Pydantic models, pytest testing, and the structure defined 
# in the technical design doc"
```

### Implementing Features

```bash
# Work incrementally with Claude Code
# Prompt: "Implement the Oracle database adapter following the
# DatabaseAdapter abstract class in the technical design doc"
```

### Testing

```bash
# Have Claude Code generate tests
# Prompt: "Generate pytest tests for the Oracle adapter using the
# fixtures in tests/fixtures/oracle-schema.json"
```

### Building for Distribution

```bash
# Compile with Nuitka
# Prompt: "Create a build script that uses Nuitka to compile
# the tool to a standalone executable with license validation"
```

## Deployment & Distribution

### Compiled Binary Distribution (Primary)

Each tool is compiled to a standalone executable using Nuitka:

```bash
# Build standalone executable
python -m nuitka \
    --standalone \
    --onefile \
    --enable-plugin=anti-bloat \
    --include-package=database_insight \
    --include-data-dir=database_insight/templates=templates \
    --output-filename=database-insight \
    database_insight/__main__.py

# Result: Single executable (~50-80MB)
# - No Python installation required on target
# - IP protected (compiled to C, then native code)
# - License validation built-in
```

### Customer Installation

```bash
# Customer receives:
# - database-insight (executable)
# - license.key (provided after purchase)

# Place license file
mkdir -p ~/.modernisation-framework
cp license.key ~/.modernisation-framework/

# Run tool
./database-insight analyze --config ./config.json
```

### License Tiers

| Tier | Scope | Price/Year | License Key Includes |
|------|-------|------------|---------------------|
| Team | 1 database, 5 users | €5,000 | company, databases=1, users=5 |
| Site | Unlimited DBs, 1 facility | €15,000 | company, databases=unlimited, site=1 |
| Enterprise | Multi-site, priority support | €40,000 | company, databases=unlimited, sites=unlimited |

### Docker Images (Optional)

For customers who prefer containerised deployment:

```bash
docker run -v $(pwd):/workspace \
    -v ~/.modernisation-framework:/root/.modernisation-framework \
    modernisation-framework/database-insight analyze \
    --config /workspace/config.json
```

## Success Metrics

### Database Insight
- Extracts schema from Oracle database in < 5 minutes (typical)
- 100% accuracy on table/column metadata
- Identifies 80%+ of regulatory gaps

### API Forge
- Generates compilable .NET Core project
- 100% CRUD coverage for all tables
- Audit trails on all write operations

### UI Forge
- Generates buildable React project
- Functional list/detail/form for all resources
- Type-safe API integration

### Logic Mapper
- Parses 95%+ of valid VBScript code
- Extracts 70%+ of identifiable business rules (with AI)
- Generates useful migration scaffolding

---

## Document Index

1. [Database Insight - Technical Design](./database-insight-technical-design.md)
2. [API Forge - Technical Design](./api-forge-technical-design.md)
3. [UI Forge - Technical Design](./ui-forge-technical-design.md)
4. [Logic Mapper - Technical Design](./logic-mapper-technical-design.md)

---

**Document Version**: 1.0  
**Last Updated**: November 2024  
**Status**: Ready for Development
