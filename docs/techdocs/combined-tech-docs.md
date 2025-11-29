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
-e 

---


# Database Insight - Technical Design Document

## Overview

Database Insight is a schema analysis and documentation tool that connects to legacy databases, extracts comprehensive metadata, and produces documentation suitable for regulatory environments. Its output feeds directly into API Forge.

## Purpose

- Generate complete schema documentation from live databases
- Map dependencies (foreign keys, triggers, procedures, views)
- Identify regulatory compliance gaps
- Produce structured output for downstream tooling

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Database Insight                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Database   │    │   Schema     │    │   Output     │      │
│  │   Adapters   │───▶│   Analyzer   │───▶│   Generator  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Oracle (V1)  │    │ Dependency   │    │ JSON Schema  │      │
│  │ SQL Server   │    │ Graph        │    │ HTML Docs    │      │
│  │ (V2)         │    │ Builder      │    │ Markdown     │      │
│  │              │    │              │    │ Gap Report   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

- **Runtime**: Python 3.11+
- **Database Drivers**: 
  - `oracledb` for Oracle (V1)
  - `pyodbc` or `pymssql` for SQL Server (V2)
- **Data Validation**: Pydantic
- **Output**: JSON, HTML (Jinja2 templates), Markdown
- **Testing**: pytest
- **CLI Framework**: Typer (or Click)
- **Distribution**: Nuitka (compiled binary for IP protection)

### Rationale

Python chosen for:
- Best-in-class database introspection ecosystem
- Excellent Oracle support via `oracledb`
- Pydantic for robust data models with validation
- Jinja2 templating is mature and flexible
- Nuitka compilation protects IP for licensed distribution
- Strong in regulated industries (data science, validation)

## Version Roadmap

| Version | Database Support | Target |
|---------|------------------|--------|
| V1 | Oracle | Initial release |
| V2 | + SQL Server | 3-6 months post V1 |

## Input Modes

Database Insight supports multiple input modes to accommodate different customer environments:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INPUT MODE OPTIONS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  MODE 1: Live Connection        MODE 2: Toad DDL Import                     │
│  ┌─────────────┐               ┌─────────────┐                              │
│  │   Oracle    │               │  schema.sql │  (Toad export)               │
│  │   Database  │               │  37K+ lines │                              │
│  └──────┬──────┘               └──────┬──────┘                              │
│         │                             │                                      │
│         ▼                             ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                    Database Insight                          │            │
│  │                                                              │            │
│  │   Input Adapters:                                           │            │
│  │   - OracleAdapter (live connection)                         │            │
│  │   - SqlServerAdapter (live connection) [V2]                 │            │
│  │   - ToadDdlParser (SQL DDL file)                           │            │
│  │   - JsonSchemaImporter (our JSON format)                   │            │
│  │                                                              │            │
│  └─────────────────────────────────────────────────────────────┘            │
│                              │                                               │
│  MODE 3: JSON Import         │         MODE 4: Generate Extract Script      │
│  ┌─────────────┐             │        ┌─────────────┐                       │
│  │ schema.json │             │        │ Customer    │                       │
│  │ (our format)│             │        │ runs script │──▶ JSON output        │
│  └─────────────┘             │        └─────────────┘                       │
│                              ▼                                               │
│                    ┌─────────────────┐                                      │
│                    │  Unified Output │                                      │
│                    │  (SchemaModel)  │                                      │
│                    └─────────────────┘                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Input Mode Comparison

| Mode | Use Case | Requires DB Access | Data Completeness |
|------|----------|-------------------|-------------------|
| Live Connection | Full extraction with credentials | Yes | Complete |
| Toad DDL Import | Customer has existing exports | No | Good (may lack FKs/indexes) |
| JSON Import | Customer ran our extract script | No | Complete |
| Extract Script | Air-gapped / security-sensitive | Customer runs | Complete |

### Why Multiple Modes?

1. **Security**: Some customers won't provide database credentials to external tools
2. **Air-gapped**: Manufacturing environments often have no external network access
3. **Existing Assets**: Many Oracle shops already have Toad exports
4. **SaaS Enabler**: JSON import allows cloud processing without credential exposure

## Data Models

### Input: Connection Configuration

```python
from pydantic import BaseModel, SecretStr
from typing import Literal, Optional

class DatabaseConnection(BaseModel):
    type: Literal['oracle', 'sqlserver']
    host: str
    port: int
    database: str  # or service_name for Oracle
    username: str
    password: Optional[SecretStr] = None  # or use environment variable
    password_env_var: Optional[str] = None  # e.g., "DB_PASSWORD"
    schema_name: Optional[str] = None  # specific schema to analyze
```

### Core Schema Model

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class SchemaModel(BaseModel):
    metadata: "SchemaMetadata"
    tables: list["Table"]
    views: list["View"]
    stored_procedures: list["StoredProcedure"]
    functions: list["DatabaseFunction"]
    triggers: list["Trigger"]
    sequences: list["Sequence"]
    indexes: list["Index"]
    constraints: list["Constraint"]
    dependencies: "DependencyGraph"
    audit_assessment: "AuditAssessment"

class SchemaMetadata(BaseModel):
    extracted_at: datetime
    database_type: str
    database_version: str
    schema_name: str
    tool_version: str

class Table(BaseModel):
    name: str
    schema_name: str
    columns: list["Column"]
    primary_key: Optional["PrimaryKey"] = None
    foreign_keys: list["ForeignKey"]
    indexes: list["Index"]
    triggers: list["TriggerReference"]
    row_count: int  # approximate
    size_bytes: int  # approximate
    last_analyzed: Optional[datetime] = None
    comments: Optional[str] = None

class Column(BaseModel):
    name: str
    data_type: str  # native type
    normalized_type: str  # normalized across databases
    nullable: bool
    default_value: Optional[str] = None
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_reference: Optional["ForeignKeyReference"] = None
    is_indexed: bool = False
    is_unique: bool = False
    comments: Optional[str] = None
    sample_values: Optional[list[str]] = None

class ForeignKey(BaseModel):
    name: str
    columns: list[str]
    referenced_table: str
    referenced_schema: str
    referenced_columns: list[str]
    on_delete: Literal['CASCADE', 'SET NULL', 'NO ACTION', 'RESTRICT']
    on_update: Literal['CASCADE', 'SET NULL', 'NO ACTION', 'RESTRICT']

class StoredProcedure(BaseModel):
    name: str
    schema_name: str
    parameters: list["Parameter"]
    return_type: Optional[str] = None
    source_code: str
    referenced_tables: list[str]  # extracted from source
    called_procedures: list[str]  # extracted from source
    comments: Optional[str] = None

class Trigger(BaseModel):
    name: str
    schema_name: str
    table_name: str
    timing: Literal['BEFORE', 'AFTER', 'INSTEAD OF']
    events: list[Literal['INSERT', 'UPDATE', 'DELETE']]
    for_each: Literal['ROW', 'STATEMENT']
    source_code: str
    is_enabled: bool

class DependencyGraph(BaseModel):
    nodes: list["DependencyNode"]
    edges: list["DependencyEdge"]

class DependencyNode(BaseModel):
    id: str  # schema.object_name
    type: Literal['table', 'view', 'procedure', 'function', 'trigger']
    name: str
    schema_name: str

class DependencyEdge(BaseModel):
    from_node: str  # node id
    to_node: str  # node id
    edge_type: Literal['foreign_key', 'references', 'calls', 'triggers']
```

### Audit Assessment Model

```python
class Severity(str, Enum):
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'

class AuditAssessment(BaseModel):
    overall_score: int  # 0-100
    categories: list["AuditCategory"]
    gaps: list["AuditGap"]
    recommendations: list["Recommendation"]

class AuditCategory(BaseModel):
    name: str
    description: str
    score: int
    max_score: int
    checks: list["AuditCheck"]

class AuditCheck(BaseModel):
    id: str
    name: str
    description: str
    passed: bool
    severity: Severity
    details: str
    affected_objects: list[str]
    regulation: str  # e.g., "21 CFR Part 11.10(e)"

class AuditGap(BaseModel):
    id: str
    title: str
    description: str
    severity: Severity
    regulation: str
    affected_objects: list[str]
    remediation: str
    estimated_effort: Literal['hours', 'days', 'weeks']
```

## Core Components

### 1. Database Adapter Interface

```python
from abc import ABC, abstractmethod
from typing import Optional

class DatabaseAdapter(ABC):
    @abstractmethod
    async def connect(self) -> None:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    # Schema extraction
    @abstractmethod
    async def get_tables(self, schema: Optional[str] = None) -> list[Table]:
        pass
    
    @abstractmethod
    async def get_views(self, schema: Optional[str] = None) -> list[View]:
        pass
    
    @abstractmethod
    async def get_stored_procedures(self, schema: Optional[str] = None) -> list[StoredProcedure]:
        pass
    
    @abstractmethod
    async def get_functions(self, schema: Optional[str] = None) -> list[DatabaseFunction]:
        pass
    
    @abstractmethod
    async def get_triggers(self, schema: Optional[str] = None) -> list[Trigger]:
        pass
    
    @abstractmethod
    async def get_sequences(self, schema: Optional[str] = None) -> list[Sequence]:
        pass
    
    # Metadata
    @abstractmethod
    async def get_database_version(self) -> str:
        pass
    
    @abstractmethod
    async def get_schemas(self) -> list[str]:
        pass
    
    # Optional: sampling for documentation
    async def get_sample_values(self, table: str, column: str, limit: int = 5) -> list[str]:
        return []  # Default implementation returns empty


### 1b. Toad DDL Parser

Parses Toad "Create Schema Script" exports (.sql files):

```python
import re
from pathlib import Path
from dataclasses import dataclass

@dataclass
class ToadParseResult:
    """Intermediate parse result before conversion to SchemaModel"""
    tables: list[dict]
    views: list[dict]
    sequences: list[dict]
    triggers: list[dict]
    packages: list[dict]
    package_bodies: list[dict]
    functions: list[dict]
    table_comments: dict[str, str]  # table_name -> comment
    column_comments: dict[str, dict[str, str]]  # table_name -> {col_name -> comment}
    metadata: dict

class ToadDdlParser:
    """
    Parses Toad 'Create Schema Script' SQL exports.
    
    Toad exports contain:
    - CREATE TABLE statements with column definitions
    - COMMENT ON TABLE/COLUMN statements
    - CREATE SEQUENCE statements
    - CREATE OR REPLACE TRIGGER statements
    - CREATE OR REPLACE PACKAGE [BODY] statements
    - CREATE OR REPLACE VIEW statements
    - Row counts in comments (-- Row Count: 1234)
    - Dependencies in comments (-- Dependencies:)
    
    Limitations of Toad exports:
    - Foreign keys may not be included (depends on export settings)
    - Indexes may not be included
    - Grants/permissions typically excluded
    """
    
    # Regex patterns for parsing
    HEADER_PATTERN = re.compile(
        r'--\s+Database Version\s+:\s+(.+?)\n.*?'
        r'--\s+Schema\s+:\s+(\w+)',
        re.DOTALL
    )
    
    TABLE_PATTERN = re.compile(
        r'--\s*\n--\s*(\w+)\s+\(Table\)\s*\n'
        r'(?:--\s*\n)?'
        r'(?:--\s+Row Count:\s*(\d+)\s*\n)?'
        r'CREATE TABLE\s+(\w+)\.(\w+)\s*\(\s*\n(.*?)\n\)\s*\n'
        r'TABLESPACE',
        re.DOTALL | re.IGNORECASE
    )
    
    COLUMN_PATTERN = re.compile(
        r'^\s*(\w+)\s+'  # column name
        r'(VARCHAR2|NUMBER|DATE|TIMESTAMP|CHAR|CLOB|BLOB|INTEGER|XMLTYPE|RAW)'  # data type
        r'(?:\((\d+)(?:,(\d+))?\s*(?:BYTE|CHAR)?\))?'  # precision/scale
        r'(\s+DEFAULT\s+.+?)?'  # default value
        r'(\s+NOT\s+NULL)?',  # nullable
        re.IGNORECASE | re.MULTILINE
    )
    
    TABLE_COMMENT_PATTERN = re.compile(
        r"COMMENT\s+ON\s+TABLE\s+(\w+)\.(\w+)\s+IS\s+'((?:[^']|'')*)'",
        re.IGNORECASE
    )
    
    COLUMN_COMMENT_PATTERN = re.compile(
        r"COMMENT\s+ON\s+COLUMN\s+(\w+)\.(\w+)\.(\w+)\s+IS\s+'((?:[^']|'')*)'",
        re.IGNORECASE
    )
    
    SEQUENCE_PATTERN = re.compile(
        r'CREATE\s+SEQUENCE\s+(\w+)\.(\w+)\s*\n'
        r'\s+START\s+WITH\s+(\d+)',
        re.IGNORECASE
    )
    
    VIEW_PATTERN = re.compile(
        r'CREATE\s+OR\s+REPLACE\s+(?:FORCE\s+)?VIEW\s+(\w+)\.(\w+)\s*'
        r'(?:\([^)]+\))?\s*AS\s*\n(.*?)(?=\n\n--|$)',
        re.DOTALL | re.IGNORECASE
    )
    
    TRIGGER_PATTERN = re.compile(
        r'CREATE\s+OR\s+REPLACE\s+TRIGGER\s+(\w+)\.(\w+)\s+'
        r'(BEFORE|AFTER|INSTEAD\s+OF)\s*\n?\s*'
        r'(INSERT|UPDATE|DELETE).*?ON\s+(\w+)\.(\w+).*?'
        r'(FOR\s+EACH\s+ROW)?\s*\n'
        r'(.*?)\n/',
        re.DOTALL | re.IGNORECASE
    )
    
    PACKAGE_PATTERN = re.compile(
        r'CREATE\s+OR\s+REPLACE\s+PACKAGE\s+(\w+)\.[""]?(\w+)[""]?\s+'
        r'(?:AS|IS)\s*\n(.*?)\nEND\s+\w+;\s*\n/',
        re.DOTALL | re.IGNORECASE
    )
    
    PACKAGE_BODY_PATTERN = re.compile(
        r'CREATE\s+OR\s+REPLACE\s+PACKAGE\s+BODY\s+(\w+)\.[""]?(\w+)[""]?\s+'
        r'(?:AS|IS)\s*\n(.*?)\nEND\s+\w+;\s*\n/',
        re.DOTALL | re.IGNORECASE
    )
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content = file_path.read_text(encoding='utf-8')
    
    def parse(self) -> ToadParseResult:
        """Parse the Toad DDL file and return structured data."""
        return ToadParseResult(
            tables=self._parse_tables(),
            views=self._parse_views(),
            sequences=self._parse_sequences(),
            triggers=self._parse_triggers(),
            packages=self._parse_packages(),
            package_bodies=self._parse_package_bodies(),
            functions=self._parse_functions(),
            table_comments=self._parse_table_comments(),
            column_comments=self._parse_column_comments(),
            metadata=self._parse_metadata()
        )
    
    def _parse_metadata(self) -> dict:
        """Extract header metadata from Toad export."""
        match = self.HEADER_PATTERN.search(self.content)
        if match:
            return {
                'database_version': match.group(1).strip(),
                'schema_name': match.group(2).strip(),
                'source': 'toad_ddl_export'
            }
        return {'source': 'toad_ddl_export'}
    
    def _parse_tables(self) -> list[dict]:
        """Extract table definitions."""
        tables = []
        
        # Find all CREATE TABLE blocks
        table_blocks = re.findall(
            r'CREATE TABLE\s+(\w+)\.(\w+)\s*\((.*?)\)\s*TABLESPACE',
            self.content,
            re.DOTALL | re.IGNORECASE
        )
        
        for schema, table_name, columns_block in table_blocks:
            # Look for row count in preceding comment
            row_count_match = re.search(
                rf'--\s+Row Count:\s*(\d+)\s*\n.*?CREATE TABLE\s+{schema}\.{table_name}',
                self.content,
                re.DOTALL | re.IGNORECASE
            )
            row_count = int(row_count_match.group(1)) if row_count_match else 0
            
            columns = self._parse_columns(columns_block)
            
            tables.append({
                'schema': schema,
                'name': table_name,
                'columns': columns,
                'row_count': row_count
            })
        
        return tables
    
    def _parse_columns(self, columns_block: str) -> list[dict]:
        """Parse column definitions from CREATE TABLE block."""
        columns = []
        
        # Split by lines and parse each column
        for line in columns_block.split('\n'):
            line = line.strip().rstrip(',')
            if not line or line.startswith('--') or 'SUPPLEMENTAL LOG' in line:
                continue
            
            match = self.COLUMN_PATTERN.match(line)
            if match:
                col_name, data_type, precision, scale, default, not_null = match.groups()
                
                columns.append({
                    'name': col_name,
                    'data_type': data_type.upper(),
                    'precision': int(precision) if precision else None,
                    'scale': int(scale) if scale else None,
                    'nullable': not_null is None,
                    'default': default.replace('DEFAULT', '').strip() if default else None
                })
        
        return columns
    
    def _parse_table_comments(self) -> dict[str, str]:
        """Extract table-level comments."""
        comments = {}
        for match in self.TABLE_COMMENT_PATTERN.finditer(self.content):
            schema, table, comment = match.groups()
            comments[table] = comment.replace("''", "'")
        return comments
    
    def _parse_column_comments(self) -> dict[str, dict[str, str]]:
        """Extract column-level comments."""
        comments = {}
        for match in self.COLUMN_COMMENT_PATTERN.finditer(self.content):
            schema, table, column, comment = match.groups()
            if table not in comments:
                comments[table] = {}
            comments[table][column] = comment.replace("''", "'")
        return comments
    
    def _parse_sequences(self) -> list[dict]:
        """Extract sequence definitions."""
        sequences = []
        for match in self.SEQUENCE_PATTERN.finditer(self.content):
            schema, name, start_with = match.groups()
            sequences.append({
                'schema': schema,
                'name': name,
                'start_with': int(start_with)
            })
        return sequences
    
    def _parse_views(self) -> list[dict]:
        """Extract view definitions."""
        views = []
        for match in self.VIEW_PATTERN.finditer(self.content):
            schema, name, definition = match.groups()
            views.append({
                'schema': schema,
                'name': name,
                'definition': definition.strip()
            })
        return views
    
    def _parse_triggers(self) -> list[dict]:
        """Extract trigger definitions."""
        triggers = []
        for match in self.TRIGGER_PATTERN.finditer(self.content):
            schema, name, timing, event, table_schema, table_name, for_each, body = match.groups()
            triggers.append({
                'schema': schema,
                'name': name,
                'timing': timing.upper(),
                'event': event.upper(),
                'table_name': table_name,
                'for_each_row': for_each is not None,
                'body': body.strip()
            })
        return triggers
    
    def _parse_packages(self) -> list[dict]:
        """Extract package specifications."""
        packages = []
        for match in self.PACKAGE_PATTERN.finditer(self.content):
            schema, name, body = match.groups()
            packages.append({
                'schema': schema,
                'name': name,
                'specification': body.strip()
            })
        return packages
    
    def _parse_package_bodies(self) -> list[dict]:
        """Extract package bodies."""
        bodies = []
        for match in self.PACKAGE_BODY_PATTERN.finditer(self.content):
            schema, name, body = match.groups()
            bodies.append({
                'schema': schema,
                'name': name,
                'body': body.strip()
            })
        return bodies
    
    def _parse_functions(self) -> list[dict]:
        """Extract standalone functions."""
        # Similar pattern to packages
        return []
    
    def to_schema_model(self) -> SchemaModel:
        """Convert parsed Toad DDL to unified SchemaModel."""
        result = self.parse()
        
        # Convert tables
        tables = []
        for t in result.tables:
            columns = []
            for c in t['columns']:
                col_comment = result.column_comments.get(t['name'], {}).get(c['name'])
                columns.append(Column(
                    name=c['name'],
                    data_type=c['data_type'],
                    normalized_type=self._normalize_type(c['data_type']),
                    nullable=c['nullable'],
                    default_value=c['default'],
                    max_length=c['precision'] if c['data_type'] in ('VARCHAR2', 'CHAR') else None,
                    precision=c['precision'] if c['data_type'] == 'NUMBER' else None,
                    scale=c['scale'],
                    comments=col_comment
                ))
            
            tables.append(Table(
                name=t['name'],
                schema_name=t['schema'],
                columns=columns,
                row_count=t['row_count'],
                comments=result.table_comments.get(t['name'])
            ))
        
        # Build SchemaModel
        return SchemaModel(
            metadata=SchemaMetadata(
                extracted_at=datetime.now(),
                database_type='oracle',
                database_version=result.metadata.get('database_version', 'unknown'),
                schema_name=result.metadata.get('schema_name', 'unknown'),
                tool_version='1.0.0',
                source='toad_ddl_import'
            ),
            tables=tables,
            views=[...],  # Convert views
            stored_procedures=[...],  # Extract from packages
            triggers=[...],  # Convert triggers
            sequences=[...],  # Convert sequences
            # Note: Foreign keys likely missing from Toad export
            dependencies=DependencyGraph(nodes=[], edges=[]),
            audit_assessment=None  # Will be populated by audit engine
        )
    
    def _normalize_type(self, oracle_type: str) -> str:
        """Map Oracle types to normalized types."""
        mapping = {
            'VARCHAR2': 'string',
            'CHAR': 'string',
            'CLOB': 'text',
            'NUMBER': 'decimal',
            'INTEGER': 'integer',
            'DATE': 'datetime',
            'TIMESTAMP': 'datetime',
            'BLOB': 'binary',
            'RAW': 'binary',
            'XMLTYPE': 'xml'
        }
        return mapping.get(oracle_type.upper(), 'unknown')


### 1c. JSON Schema Importer

For importing our own JSON format (from extract scripts or previous runs):

```python
class JsonSchemaImporter:
    """
    Imports schema from our JSON format.
    
    This is the cleanest input path - use when customer can run
    our extraction scripts against their database.
    """
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
    
    def load(self) -> SchemaModel:
        """Load and validate JSON schema file."""
        content = self.file_path.read_text(encoding='utf-8')
        data = json.loads(content)
        
        # Pydantic validates the structure
        return SchemaModel.model_validate(data)
    
    @staticmethod
    def generate_extract_script(database_type: str, schema_name: str) -> str:
        """
        Generate SQL script for customer to run.
        
        Customer runs this script, gets JSON output, 
        sends JSON to us (no credentials needed).
        """
        if database_type == 'oracle':
            return f'''
-- Database Insight Extract Script for Oracle
-- Run as: sqlplus user/pass@db @extract_schema.sql > schema.json
-- Schema: {schema_name}

SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 2000000000
SET LONGCHUNKSIZE 32767
SET FEEDBACK OFF
SET HEADING OFF
SET ECHO OFF

SELECT JSON_OBJECT(
  'metadata' VALUE JSON_OBJECT(
    'extracted_at' VALUE TO_CHAR(SYSDATE, 'YYYY-MM-DD"T"HH24:MI:SS'),
    'database_type' VALUE 'oracle',
    'database_version' VALUE (SELECT banner FROM v$version WHERE ROWNUM = 1),
    'schema_name' VALUE '{schema_name}',
    'tool_version' VALUE '1.0.0'
  ),
  'tables' VALUE (
    SELECT JSON_ARRAYAGG(
      JSON_OBJECT(
        'name' VALUE t.table_name,
        'schema_name' VALUE t.owner,
        'row_count' VALUE t.num_rows,
        'columns' VALUE (
          SELECT JSON_ARRAYAGG(
            JSON_OBJECT(
              'name' VALUE c.column_name,
              'data_type' VALUE c.data_type,
              'nullable' VALUE CASE WHEN c.nullable = 'Y' THEN 'true' ELSE 'false' END FORMAT JSON,
              'max_length' VALUE c.data_length,
              'precision' VALUE c.data_precision,
              'scale' VALUE c.data_scale,
              'default_value' VALUE c.data_default,
              'comments' VALUE (
                SELECT cc.comments 
                FROM all_col_comments cc 
                WHERE cc.owner = c.owner 
                  AND cc.table_name = c.table_name 
                  AND cc.column_name = c.column_name
              )
            ) ORDER BY c.column_id
          )
          FROM all_tab_columns c
          WHERE c.owner = t.owner AND c.table_name = t.table_name
        ),
        'primary_key' VALUE (
          SELECT JSON_OBJECT(
            'name' VALUE ac.constraint_name,
            'columns' VALUE (
              SELECT JSON_ARRAYAGG(acc.column_name ORDER BY acc.position)
              FROM all_cons_columns acc
              WHERE acc.owner = ac.owner AND acc.constraint_name = ac.constraint_name
            )
          )
          FROM all_constraints ac
          WHERE ac.owner = t.owner 
            AND ac.table_name = t.table_name 
            AND ac.constraint_type = 'P'
        ),
        'foreign_keys' VALUE (
          SELECT JSON_ARRAYAGG(
            JSON_OBJECT(
              'name' VALUE ac.constraint_name,
              'columns' VALUE (
                SELECT JSON_ARRAYAGG(acc.column_name ORDER BY acc.position)
                FROM all_cons_columns acc
                WHERE acc.owner = ac.owner AND acc.constraint_name = ac.constraint_name
              ),
              'referenced_table' VALUE (
                SELECT ac2.table_name 
                FROM all_constraints ac2 
                WHERE ac2.owner = ac.r_owner AND ac2.constraint_name = ac.r_constraint_name
              ),
              'referenced_columns' VALUE (
                SELECT JSON_ARRAYAGG(acc.column_name ORDER BY acc.position)
                FROM all_cons_columns acc
                WHERE acc.owner = ac.r_owner AND acc.constraint_name = ac.r_constraint_name
              )
            )
          )
          FROM all_constraints ac
          WHERE ac.owner = t.owner 
            AND ac.table_name = t.table_name 
            AND ac.constraint_type = 'R'
        ),
        'comments' VALUE (
          SELECT tc.comments 
          FROM all_tab_comments tc 
          WHERE tc.owner = t.owner AND tc.table_name = t.table_name
        )
      )
    )
    FROM all_tables t
    WHERE t.owner = '{schema_name}'
  )
  RETURNING CLOB
) AS schema_json
FROM dual;

EXIT;
'''
        else:
            raise ValueError(f"Unsupported database type: {database_type}")
```
```

### 2. Audit Rules Engine

The audit assessment runs a series of checks against the extracted schema:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class AuditCheckResult:
    passed: bool
    affected_objects: list[str]
    details: str

class AuditRule(ABC):
    id: str
    name: str
    description: str
    regulation: str
    severity: Severity
    
    @abstractmethod
    def evaluate(self, schema: SchemaModel) -> AuditCheckResult:
        pass

# Example rules implementation
class PrimaryKeyExistsRule(AuditRule):
    id = 'PK_EXISTS'
    name = 'Primary Key Exists'
    description = 'Every table should have a primary key'
    regulation = '21 CFR Part 11.10(a)'
    severity = Severity.CRITICAL
    
    def evaluate(self, schema: SchemaModel) -> AuditCheckResult:
        tables_without_pk = [t.name for t in schema.tables if not t.primary_key]
        return AuditCheckResult(
            passed=len(tables_without_pk) == 0,
            affected_objects=tables_without_pk,
            details=f"{len(tables_without_pk)} tables without primary key"
        )

class AuditTrailColumnsRule(AuditRule):
    id = 'AUDIT_COLUMNS'
    name = 'Audit Trail Columns'
    description = 'Tables should have created/modified timestamp and user columns'
    regulation = '21 CFR Part 11.10(e)'
    severity = Severity.HIGH
    
    def evaluate(self, schema: SchemaModel) -> AuditCheckResult:
        audit_patterns = [
            'created_at', 'created_by', 'modified_at', 'modified_by',
            'create_date', 'create_user', 'update_date', 'update_user'
        ]
        
        tables_missing_audit = []
        for table in schema.tables:
            column_names = {c.name.lower() for c in table.columns}
            has_created = any(p in column_names for p in ['created_at', 'create_date'])
            has_modified = any(p in column_names for p in ['modified_at', 'update_date'])
            has_user = any(p in column_names for p in ['created_by', 'create_user'])
            
            if not (has_created and has_modified and has_user):
                tables_missing_audit.append(table.name)
        
        return AuditCheckResult(
            passed=len(tables_missing_audit) == 0,
            affected_objects=tables_missing_audit,
            details=f"{len(tables_missing_audit)} tables missing audit columns"
        )

# Registry of all audit rules
AUDIT_RULES: list[AuditRule] = [
    PrimaryKeyExistsRule(),
    AuditTrailColumnsRule(),
    # Additional rules:
    # - Foreign key integrity
    # - Soft delete patterns (no hard deletes)
    # - Timestamp columns for all data tables
    # - User tracking columns
    # - Version/revision columns for critical tables
    # - Constraint naming conventions
    # - Index coverage for foreign keys
]
```

### 3. Dependency Graph Builder

```python
class DependencyGraphBuilder:
    def __init__(self):
        self._nodes: dict[str, DependencyNode] = {}
        self._edges: list[DependencyEdge] = []
    
    def add_table(self, table: Table) -> None:
        node_id = f"{table.schema_name}.{table.name}"
        self._nodes[node_id] = DependencyNode(
            id=node_id,
            type='table',
            name=table.name,
            schema_name=table.schema_name
        )
        
        # Add foreign key edges
        for fk in table.foreign_keys:
            self._edges.append(DependencyEdge(
                from_node=node_id,
                to_node=f"{fk.referenced_schema}.{fk.referenced_table}",
                edge_type='foreign_key'
            ))
    
    def add_procedure(self, proc: StoredProcedure) -> None:
        node_id = f"{proc.schema_name}.{proc.name}"
        self._nodes[node_id] = DependencyNode(
            id=node_id,
            type='procedure',
            name=proc.name,
            schema_name=proc.schema_name
        )
        
        # Add reference edges from source code analysis
        for ref in proc.referenced_tables:
            self._edges.append(DependencyEdge(
                from_node=node_id,
                to_node=ref,
                edge_type='references'
            ))
    
    def analyze(self) -> "DependencyAnalysis":
        """Analyze for circular dependencies, orphaned tables, etc."""
        # Implementation
        pass
    
    def to_graph(self) -> DependencyGraph:
        return DependencyGraph(
            nodes=list(self._nodes.values()),
            edges=self._edges
        )
```

## Database-Specific Queries

### Oracle System Catalog Queries

```sql
-- Tables
SELECT table_name, num_rows, last_analyzed
FROM all_tables
WHERE owner = :schema;

-- Columns
SELECT table_name, column_name, data_type, data_length, 
       data_precision, data_scale, nullable, data_default
FROM all_tab_columns
WHERE owner = :schema;

-- Primary Keys
SELECT acc.constraint_name, acc.column_name, acc.position
FROM all_cons_columns acc
JOIN all_constraints ac ON acc.constraint_name = ac.constraint_name
WHERE ac.constraint_type = 'P' AND ac.owner = :schema;

-- Foreign Keys
SELECT ac.constraint_name, acc.column_name, 
       ac.r_constraint_name, rac.table_name as ref_table,
       racc.column_name as ref_column
FROM all_constraints ac
JOIN all_cons_columns acc ON ac.constraint_name = acc.constraint_name
JOIN all_constraints rac ON ac.r_constraint_name = rac.constraint_name
JOIN all_cons_columns racc ON rac.constraint_name = racc.constraint_name
WHERE ac.constraint_type = 'R' AND ac.owner = :schema;

-- Stored Procedures
SELECT object_name, object_type, status
FROM all_objects
WHERE object_type IN ('PROCEDURE', 'FUNCTION', 'PACKAGE')
  AND owner = :schema;

-- Procedure Source
SELECT text
FROM all_source
WHERE name = :proc_name AND owner = :schema
ORDER BY line;

-- Triggers
SELECT trigger_name, table_name, trigger_type, triggering_event,
       status, trigger_body
FROM all_triggers
WHERE owner = :schema;
```

### SQL Server System Catalog Queries

```sql
-- Tables
SELECT t.name, p.rows
FROM sys.tables t
JOIN sys.partitions p ON t.object_id = p.object_id
WHERE p.index_id IN (0, 1) AND SCHEMA_NAME(t.schema_id) = @schema;

-- Columns
SELECT c.name, TYPE_NAME(c.user_type_id) as data_type,
       c.max_length, c.precision, c.scale, c.is_nullable
FROM sys.columns c
JOIN sys.tables t ON c.object_id = t.object_id
WHERE SCHEMA_NAME(t.schema_id) = @schema;

-- And so on for other objects...
```

## Output Generators

### 1. JSON Schema Output

Primary output for downstream tools (API Forge):

```python
import json
from pathlib import Path

async def generate_json_output(schema: SchemaModel, output_path: Path) -> None:
    json_str = schema.model_dump_json(indent=2)
    output_path.write_text(json_str)
```

### 2. HTML Documentation

Interactive documentation for human consumption using Jinja2:

```python
from jinja2 import Environment, PackageLoader

async def generate_html_docs(schema: SchemaModel, output_dir: Path) -> None:
    env = Environment(loader=PackageLoader('database_insight', 'templates'))
    
    # Generate index.html with navigation
    index_template = env.get_template('index.html.j2')
    (output_dir / 'index.html').write_text(
        index_template.render(schema=schema)
    )
    
    # Generate page per table with column details
    table_template = env.get_template('table.html.j2')
    tables_dir = output_dir / 'tables'
    tables_dir.mkdir(exist_ok=True)
    
    for table in schema.tables:
        (tables_dir / f'{table.name}.html').write_text(
            table_template.render(table=table, schema=schema)
        )
    
    # Generate ERD visualization (using Mermaid)
    # Generate dependency graph visualization
    # Generate audit report page
```

### 3. Markdown Output

For inclusion in repositories:

```python
async def generate_markdown(schema: SchemaModel, output_dir: Path) -> None:
    env = Environment(loader=PackageLoader('database_insight', 'templates'))
    
    # README.md with overview
    readme_template = env.get_template('README.md.j2')
    (output_dir / 'README.md').write_text(
        readme_template.render(schema=schema)
    )
    
    # tables/ directory with one file per table
    tables_dir = output_dir / 'tables'
    tables_dir.mkdir(exist_ok=True)
    table_template = env.get_template('table.md.j2')
    
    for table in schema.tables:
        (tables_dir / f'{table.name}.md').write_text(
            table_template.render(table=table)
        )
    
    # AUDIT_REPORT.md with gap analysis
    audit_template = env.get_template('audit_report.md.j2')
    (output_dir / 'AUDIT_REPORT.md').write_text(
        audit_template.render(assessment=schema.audit_assessment)
    )
```

## CLI Interface

Using Typer for a clean CLI with multiple input modes:

```python
import typer
from pathlib import Path
from typing import Optional
from enum import Enum

app = typer.Typer(help="Database schema analysis and documentation tool")

class DatabaseType(str, Enum):
    oracle = "oracle"
    sqlserver = "sqlserver"

class OutputFormat(str, Enum):
    json = "json"
    html = "html"
    markdown = "markdown"

class InputMode(str, Enum):
    live = "live"       # Direct database connection
    toad = "toad"       # Toad DDL export file
    json = "json"       # Our JSON format

@app.command()
def analyze(
    # Input mode selection
    mode: InputMode = typer.Option(InputMode.live, "--mode", "-m", help="Input mode"),
    
    # For live connection mode
    db_type: Optional[DatabaseType] = typer.Option(None, "--type", "-t", help="Database type"),
    host: Optional[str] = typer.Option(None, "--host", "-h", help="Database host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Database port"),
    database: Optional[str] = typer.Option(None, "--database", "-d", help="Database name"),
    username: Optional[str] = typer.Option(None, "--username", "-u", help="Username"),
    schema: Optional[str] = typer.Option(None, "--schema", "-s", help="Schema to analyze"),
    
    # For file import modes (toad/json)
    input_file: Optional[Path] = typer.Option(None, "--input", "-i", help="Input file path"),
    
    # Output options
    output: Path = typer.Option(..., "--output", "-o", help="Output directory"),
    formats: list[OutputFormat] = typer.Option(
        [OutputFormat.json], "--format", "-f", help="Output formats"
    ),
    
    # Config file (overrides other options)
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
):
    """
    Analyze database schema and generate documentation.
    
    Supports three input modes:
    
    - live: Direct connection to database (requires credentials)
    - toad: Import from Toad DDL export file (.sql)
    - json: Import from our JSON schema format
    """
    # Validate license first
    from .license import validate_license
    validate_license()
    
    if mode == InputMode.live:
        # Live connection mode
        if not all([db_type, host, port, database, username]):
            raise typer.BadParameter("Live mode requires: --type, --host, --port, --database, --username")
        
        import os
        password = os.environ.get("DATABASE_INSIGHT_PASSWORD")
        if not password:
            password = typer.prompt("Database password", hide_input=True)
        
        # Run live extraction
        # ...
        
    elif mode == InputMode.toad:
        # Toad DDL import mode
        if not input_file:
            raise typer.BadParameter("Toad mode requires: --input <file.sql>")
        
        from .adapters.toad_parser import ToadDdlParser
        parser = ToadDdlParser(input_file)
        schema_model = parser.to_schema_model()
        # Continue with analysis...
        
    elif mode == InputMode.json:
        # JSON import mode
        if not input_file:
            raise typer.BadParameter("JSON mode requires: --input <file.json>")
        
        from .adapters.json_importer import JsonSchemaImporter
        importer = JsonSchemaImporter(input_file)
        schema_model = importer.load()
        # Continue with analysis...


@app.command()
def extract_script(
    db_type: DatabaseType = typer.Option(..., "--type", "-t", help="Database type"),
    schema: str = typer.Option(..., "--schema", "-s", help="Schema name"),
    output: Path = typer.Option(..., "--output", "-o", help="Output file path"),
):
    """
    Generate SQL extraction script for customer to run.
    
    Customer runs the generated script against their database,
    captures JSON output, and provides it to you for analysis.
    No credentials required.
    """
    from .adapters.json_importer import JsonSchemaImporter
    
    script = JsonSchemaImporter.generate_extract_script(db_type.value, schema)
    output.write_text(script)
    
    typer.echo(f"Extraction script written to: {output}")
    typer.echo(f"\nCustomer should run:")
    typer.echo(f"  sqlplus user/pass@db @{output.name} > schema.json")


@app.command()
def validate(
    input_file: Path = typer.Option(..., "--input", "-i", help="File to validate"),
):
    """
    Validate input file (Toad DDL or JSON schema).
    """
    suffix = input_file.suffix.lower()
    
    if suffix == '.sql':
        from .adapters.toad_parser import ToadDdlParser
        parser = ToadDdlParser(input_file)
        result = parser.parse()
        typer.echo(f"✓ Valid Toad DDL export")
        typer.echo(f"  Tables: {len(result.tables)}")
        typer.echo(f"  Views: {len(result.views)}")
        typer.echo(f"  Triggers: {len(result.triggers)}")
        typer.echo(f"  Packages: {len(result.packages)}")
        
    elif suffix == '.json':
        from .adapters.json_importer import JsonSchemaImporter
        importer = JsonSchemaImporter(input_file)
        schema = importer.load()
        typer.echo(f"✓ Valid JSON schema")
        typer.echo(f"  Tables: {len(schema.tables)}")
        typer.echo(f"  Views: {len(schema.views)}")
        
    else:
        raise typer.BadParameter(f"Unknown file type: {suffix}")


if __name__ == "__main__":
    app()
```

**Usage examples:**

```bash
# MODE 1: Live database connection
DATABASE_INSIGHT_PASSWORD=secret database-insight analyze \
  --mode live \
  --type oracle \
  --host localhost \
  --port 1521 \
  --database ORCL \
  --username app_user \
  --schema APP_SCHEMA \
  --output ./output

# MODE 2: Import Toad DDL export
database-insight analyze \
  --mode toad \
  --input ./IMAS.sql \
  --output ./output \
  --format json --format html

# MODE 3: Import JSON (from our extract script)
database-insight analyze \
  --mode json \
  --input ./schema.json \
  --output ./output

# Generate extraction script for customer
database-insight extract-script \
  --type oracle \
  --schema IMAS \
  --output ./extract_imas.sql

# Validate an input file
database-insight validate --input ./IMAS.sql
database-insight validate --input ./schema.json
```

## Development Phases

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Project setup (Python, Poetry, pytest)
- [ ] Pydantic models for all data structures
- [ ] Database adapter interface
- [ ] Oracle adapter implementation (live connection)
- [ ] Basic schema extraction (tables, columns, keys)
- [ ] JSON output generator
- [ ] CLI framework with Typer

### Phase 2: Import Adapters (Week 3-4)
- [ ] Toad DDL parser implementation
- [ ] JSON schema importer
- [ ] Extract script generator (for customer use)
- [ ] Validation command for input files
- [ ] Handle missing FK/index data gracefully

### Phase 3: Complete Schema Extraction (Week 5-6)
- [ ] Stored procedures/functions extraction
- [ ] Trigger extraction
- [ ] View extraction with column mapping
- [ ] Index extraction (live mode)
- [ ] Source code extraction for procedures
- [ ] SQL Server adapter groundwork (V2 prep)

### Phase 4: Analysis & Documentation (Week 7-8)
- [ ] Dependency graph builder
- [ ] Audit rules engine (core rules)
- [ ] HTML documentation generator (Jinja2)
- [ ] Markdown output
- [ ] ERD visualization (Mermaid)

### Phase 5: Polish & Distribution (Week 9-10)
- [ ] Additional audit rules
- [ ] Sample value extraction (optional, live mode only)
- [ ] Performance optimization for large schemas
- [ ] Comprehensive testing
- [ ] Nuitka compilation for distribution
- [ ] License key validation

## Testing Strategy

### Unit Tests
- Each database adapter with mocked connections
- Toad DDL parser with sample exports
- JSON importer with valid/invalid schemas
- Audit rules with sample schemas
- Output generators with snapshot testing

```python
# tests/test_toad_parser.py
import pytest
from pathlib import Path
from database_insight.adapters.toad_parser import ToadDdlParser

@pytest.fixture
def sample_toad_export(tmp_path):
    """Create a minimal Toad export for testing."""
    content = '''
--
-- Create Schema Script
--   Database Version            : 19.0.0.0.0
--   Schema                      : TEST_SCHEMA
--

--
-- USERS  (Table) 
--
--   Row Count: 1500
CREATE TABLE TEST_SCHEMA.USERS
(
  USER_ID     NUMBER,
  USERNAME    VARCHAR2(50 BYTE),
  EMAIL       VARCHAR2(100 BYTE),
  CREATED_AT  DATE              DEFAULT sysdate
)
TABLESPACE USERS;

COMMENT ON TABLE TEST_SCHEMA.USERS IS 'System users';
COMMENT ON COLUMN TEST_SCHEMA.USERS.USER_ID IS 'Primary key';
'''
    file_path = tmp_path / "test_export.sql"
    file_path.write_text(content)
    return file_path

def test_parses_table_definition(sample_toad_export):
    parser = ToadDdlParser(sample_toad_export)
    result = parser.parse()
    
    assert len(result.tables) == 1
    assert result.tables[0]['name'] == 'USERS'
    assert result.tables[0]['row_count'] == 1500
    assert len(result.tables[0]['columns']) == 4

def test_parses_column_details(sample_toad_export):
    parser = ToadDdlParser(sample_toad_export)
    result = parser.parse()
    
    columns = {c['name']: c for c in result.tables[0]['columns']}
    
    assert columns['USER_ID']['data_type'] == 'NUMBER'
    assert columns['USERNAME']['data_type'] == 'VARCHAR2'
    assert columns['USERNAME']['precision'] == 50
    assert columns['CREATED_AT']['default'] is not None

def test_parses_comments(sample_toad_export):
    parser = ToadDdlParser(sample_toad_export)
    result = parser.parse()
    
    assert result.table_comments['USERS'] == 'System users'
    assert result.column_comments['USERS']['USER_ID'] == 'Primary key'

def test_converts_to_schema_model(sample_toad_export):
    parser = ToadDdlParser(sample_toad_export)
    schema = parser.to_schema_model()
    
    assert schema.metadata.database_type == 'oracle'
    assert schema.metadata.schema_name == 'TEST_SCHEMA'
    assert len(schema.tables) == 1
    assert schema.tables[0].name == 'USERS'


# tests/test_audit_rules.py
import pytest
from database_insight.audit import PrimaryKeyExistsRule
from database_insight.models import SchemaModel, Table, PrimaryKey

def test_pk_exists_rule_passes():
    schema = SchemaModel(
        tables=[
            Table(name="users", primary_key=PrimaryKey(columns=["id"]), ...)
        ],
        ...
    )
    rule = PrimaryKeyExistsRule()
    result = rule.evaluate(schema)
    assert result.passed is True
    assert result.affected_objects == []

def test_pk_exists_rule_fails():
    schema = SchemaModel(
        tables=[
            Table(name="logs", primary_key=None, ...)
        ],
        ...
    )
    rule = PrimaryKeyExistsRule()
    result = rule.evaluate(schema)
    assert result.passed is False
    assert "logs" in result.affected_objects
```

### Integration Tests
- Docker containers for live database tests
- Real Toad exports (like the IMAS.sql sample)
- Round-trip testing (extract → modify → verify)

### Test Fixtures
Use the provided IMAS.sql as a real-world test fixture:
- 179 tables, 1236 columns
- 71 views
- 33 triggers
- 18 packages

```python
# tests/test_real_toad_export.py
import pytest
from pathlib import Path

@pytest.fixture
def imas_export():
    """Real IMAS Toad export for integration testing."""
    return Path("tests/fixtures/IMAS.sql")

def test_parses_large_export(imas_export):
    parser = ToadDdlParser(imas_export)
    result = parser.parse()
    
    assert len(result.tables) >= 170  # ~179 expected
    assert len(result.views) >= 60    # ~71 expected
    assert len(result.triggers) >= 30 # ~33 expected

def test_handles_complex_column_types(imas_export):
    parser = ToadDdlParser(imas_export)
    result = parser.parse()
    
    # Find XMLTYPE column (DAT_XML_AUDIT_RESULTS.XML_DOC)
    xml_table = next(t for t in result.tables if t['name'] == 'DAT_XML_AUDIT_RESULTS')
    xml_col = next(c for c in xml_table['columns'] if c['name'] == 'XML_DOC')
    assert xml_col['data_type'] == 'XMLTYPE'
```

### Test Databases
Create Docker Compose setup for live connection testing:
- Oracle XE (for V1)
- SQL Server Developer (for V2)

```yaml
# docker-compose.test.yml
services:
  oracle:
    image: gvenzl/oracle-xe:21-slim
    environment:
      ORACLE_PASSWORD: test
    ports:
      - "1521:1521"
```

Pre-seed with representative schema including:
- Tables with various column types
- Foreign key relationships (including circular)
- Stored procedures with table references
- Triggers
- Views referencing multiple tables

## Error Handling

```python
class DatabaseInsightError(Exception):
    """Base exception for Database Insight"""
    def __init__(self, message: str, code: str, context: dict = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}

class ConnectionError(DatabaseInsightError):
    """Failed to connect to database"""
    pass

class AuthenticationError(DatabaseInsightError):
    """Authentication failed"""
    pass

class SchemaNotFoundError(DatabaseInsightError):
    """Specified schema does not exist"""
    pass

class PermissionDeniedError(DatabaseInsightError):
    """Insufficient permissions to read schema"""
    pass

# Error codes
class ErrorCode:
    CONNECTION_FAILED = 'CONNECTION_FAILED'
    AUTHENTICATION_FAILED = 'AUTH_FAILED'
    SCHEMA_NOT_FOUND = 'SCHEMA_NOT_FOUND'
    PERMISSION_DENIED = 'PERMISSION_DENIED'
    QUERY_TIMEOUT = 'QUERY_TIMEOUT'
    UNSUPPORTED_DATABASE = 'UNSUPPORTED_DB'
```

## Security Considerations

- Never log credentials
- Support environment variables for passwords
- Read-only database access only
- Option to exclude sensitive table names from output
- Option to disable sample value extraction

## Licensing & Distribution

### License Key Validation

```python
import hashlib
import json
from datetime import datetime
from pathlib import Path

class LicenseValidator:
    def __init__(self, license_file: Path):
        self.license_file = license_file
        self._license_data = None
    
    def validate(self) -> bool:
        """Validate license file and check expiry."""
        if not self.license_file.exists():
            raise LicenseError("License file not found", "LICENSE_NOT_FOUND")
        
        try:
            self._license_data = json.loads(self.license_file.read_text())
        except json.JSONDecodeError:
            raise LicenseError("Invalid license file", "LICENSE_INVALID")
        
        # Check signature
        if not self._verify_signature():
            raise LicenseError("License signature invalid", "LICENSE_TAMPERED")
        
        # Check expiry
        expiry = datetime.fromisoformat(self._license_data['expires'])
        if datetime.now() > expiry:
            raise LicenseError("License expired", "LICENSE_EXPIRED")
        
        return True
    
    def _verify_signature(self) -> bool:
        """Verify license signature against public key."""
        # Implementation using cryptographic signature
        pass
    
    @property
    def company_name(self) -> str:
        return self._license_data.get('company', 'Unknown')
    
    @property
    def licensed_databases(self) -> int:
        return self._license_data.get('databases', 1)

class LicenseError(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code
```

### Nuitka Compilation for Distribution

```bash
# Build standalone executable
pip install nuitka

# Compile with full optimization
python -m nuitka \
    --standalone \
    --onefile \
    --enable-plugin=anti-bloat \
    --include-package=database_insight \
    --include-data-dir=database_insight/templates=templates \
    --output-filename=database-insight \
    database_insight/__main__.py

# Output: database-insight (single executable, ~50-80MB)
```

### Project Structure for Distribution

```
database-insight/
├── pyproject.toml
├── README.md
├── LICENSE
│
├── database_insight/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── cli.py                # Typer CLI
│   ├── config.py             # Configuration loading
│   ├── license.py            # License validation
│   │
│   ├── models/               # Pydantic models
│   │   ├── __init__.py
│   │   ├── schema.py         # SchemaModel, Table, Column, etc.
│   │   ├── audit.py          # AuditAssessment, AuditGap, etc.
│   │   └── config.py         # Configuration models
│   │
│   ├── adapters/             # Input adapters
│   │   ├── __init__.py
│   │   ├── base.py           # DatabaseAdapter ABC
│   │   ├── oracle.py         # Live Oracle connection
│   │   ├── sqlserver.py      # Live SQL Server connection [V2]
│   │   ├── toad_parser.py    # Toad DDL file parser
│   │   └── json_importer.py  # JSON schema importer
│   │
│   ├── analysis/             # Analysis logic
│   │   ├── __init__.py
│   │   ├── audit_rules.py    # FDA 21 CFR Part 11 rules
│   │   └── dependencies.py   # Dependency graph builder
│   │
│   ├── generators/           # Output generators
│   │   ├── __init__.py
│   │   ├── json_output.py
│   │   ├── html_output.py
│   │   └── markdown_output.py
│   │
│   └── templates/            # Jinja2 templates
│       ├── index.html.j2
│       ├── table.html.j2
│       ├── table.md.j2
│       ├── audit_report.md.j2
│       └── extract_script.sql.j2  # Template for customer scripts
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_adapters/
    │   ├── test_oracle.py
    │   ├── test_toad_parser.py
    │   └── test_json_importer.py
    ├── test_analysis/
    │   ├── test_audit_rules.py
    │   └── test_dependencies.py
    └── fixtures/
        ├── IMAS.sql              # Real Toad export for testing
        ├── sample_schema.json    # Sample JSON schema
        └── minimal_export.sql    # Minimal Toad export
```

## Configuration File Format

```json
{
  "input": {
    "mode": "live",
    "connection": {
      "type": "oracle",
      "host": "db.example.com",
      "port": 1521,
      "database": "PROD",
      "username": "analyzer",
      "password_env_var": "DB_PASSWORD",
      "schema": "APP"
    }
  },
  "extraction": {
    "include_tables": ["*"],
    "exclude_tables": ["*_BACKUP", "*_LOG"],
    "extract_sample_values": false,
    "sample_value_limit": 5
  },
  "audit": {
    "enabled": true,
    "regulations": ["FDA_21_CFR_PART_11", "ISO_13485"]
  },
  "output": {
    "directory": "./output",
    "formats": ["json", "html", "markdown"]
  },
  "license": {
    "file": "./license.key"
  }
}
```

**Configuration for Toad import mode:**

```json
{
  "input": {
    "mode": "toad",
    "file": "./exports/IMAS.sql"
  },
  "audit": {
    "enabled": true,
    "regulations": ["FDA_21_CFR_PART_11"]
  },
  "output": {
    "directory": "./output",
    "formats": ["json", "html"]
  }
}
```

**Configuration for JSON import mode:**

```json
{
  "input": {
    "mode": "json",
    "file": "./schema.json"
  },
  "output": {
    "directory": "./output",
    "formats": ["html", "markdown"]
  }
}
```

## Integration with API Forge

The JSON output (`schema.json`) is the primary input for API Forge. Key fields API Forge will consume:

- `tables[].name` - API resource names
- `tables[].columns` - Model properties
- `tables[].primary_key` - Resource identifiers
- `tables[].foreign_keys` - Relationship endpoints
- `constraints` - Validation rules
- `audit_assessment.gaps` - Patterns to implement in API

---

**Document Version**: 1.2  
**Last Updated**: November 2024  
**Language**: Python 3.11+
**Input Modes**: Live connection, Toad DDL import, JSON import
**Status**: Ready for Development
-e 

---


# API Forge - Technical Design Document

## Overview

API Forge generates production-ready REST APIs from Database Insight schema output. It creates complete, auditable API solutions with built-in patterns for regulatory compliance.

## Purpose

- Generate REST APIs from schema definitions
- Build in audit trail patterns by default
- Create OpenAPI/Swagger documentation automatically
- Produce code that meets FDA 21 CFR Part 11 requirements
- Output feeds directly into UI Forge

## Output Targets

| Version | Output | Target Market |
|---------|--------|---------------|
| V1 | .NET Core 8 Web API | Medical devices, J&J-type enterprises |
| V2 | Java Spring Boot | Large pharma, Java shops |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Forge                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Schema     │    │   Code       │    │   Project    │      │
│  │   Parser     │───▶│   Generator  │───▶│   Builder    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Database     │    │ Controllers  │    │ .csproj      │      │
│  │ Insight JSON │    │ Models       │    │ Program.cs   │      │
│  │              │    │ Repositories │    │ appsettings  │      │
│  │              │    │ DTOs         │    │ Dockerfile   │      │
│  │              │    │ Validators   │    │ OpenAPI      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

- **Generator Runtime**: Python 3.11+
- **Output Target V1**: .NET 8.0 Web API (C#)
- **Output Target V2**: Java 17+ / Spring Boot 3.x (future)
- **ORM (V1)**: Entity Framework Core
- **Documentation**: Swashbuckle (OpenAPI 3.0)
- **Templating**: Jinja2 (for code generation)
- **Testing**: pytest for generator, xUnit for generated code

### Rationale

Python for the generator because:
- Consistent with Database Insight
- Excellent template processing with Jinja2
- Good string manipulation for code generation
- Nuitka compilation for distribution

.NET Core for V1 output because:
- Enterprise standard in medical devices
- Strong typing catches errors at compile time
- Excellent Oracle/SQL Server support
- Familiar to target customer base

## Data Models

### Input: Database Insight Schema

API Forge consumes the `SchemaModel` JSON output from Database Insight. Key elements used:

```python
from pydantic import BaseModel
from typing import Optional

# From Database Insight output (loaded from JSON)
class SchemaInput(BaseModel):
    metadata: "SchemaMetadata"
    tables: list["Table"]
    audit_assessment: "AuditAssessment"
```

### Configuration Model

```python
from pydantic import BaseModel
from typing import Literal, Optional
from pathlib import Path

class ApiForgeConfig(BaseModel):
    input: "InputConfig"
    output: "OutputConfig"
    database: "DatabaseConfig"
    api: "ApiConfig"
    generation: "GenerationConfig"
    tables: "TableConfig"

class InputConfig(BaseModel):
    schema_file: Path  # Path to Database Insight JSON

class OutputConfig(BaseModel):
    directory: Path
    project_name: str  # e.g., "Acme.Api"
    namespace: str  # e.g., "Acme.Api"

class DatabaseConfig(BaseModel):
    type: Literal['oracle', 'sqlserver']
    connection_string_name: str  # For appsettings reference

class ApiConfig(BaseModel):
    route_prefix: str = "/api/v1"
    enable_swagger: bool = True
    enable_audit_log: bool = True
    enable_soft_delete: bool = True
    authentication_scheme: Literal['jwt', 'windows', 'none'] = 'jwt'

class GenerationConfig(BaseModel):
    include_repository_pattern: bool = True
    include_dtos: bool = True  # Separate DTOs from entities
    include_validation: bool = True
    include_unit_tests: bool = True
    target_framework: Literal['dotnet', 'java'] = 'dotnet'

class TableConfig(BaseModel):
    include: list[str] = ["*"]  # Glob patterns
    exclude: list[str] = []
    overrides: list["TableOverride"] = []

class TableOverride(BaseModel):
    table_name: str
    api_resource_name: Optional[str] = None  # Override endpoint name
    read_only: bool = False  # No POST/PUT/DELETE
    exclude_columns: list[str] = []
    custom_endpoints: list["CustomEndpoint"] = []

class CustomEndpoint(BaseModel):
    name: str
    http_method: Literal['GET', 'POST']
    route: str
    description: str
    stored_procedure: Optional[str] = None  # For SP calls
```

### Generated Code Structure

```python
from dataclasses import dataclass

@dataclass
class GeneratedFile:
    path: str  # Relative path in output
    content: str  # File content
    overwrite_if_exists: bool = True

@dataclass
class GeneratedProject:
    project_file: GeneratedFile  # .csproj
    program_cs: GeneratedFile  # Program.cs
    app_settings: GeneratedFile  # appsettings.json
    dockerfile: GeneratedFile
    
    models: list[GeneratedFile]  # Entity classes
    dtos: list[GeneratedFile]  # Request/Response DTOs
    controllers: list[GeneratedFile]  # API Controllers
    repositories: list[GeneratedFile]  # Data access
    validators: list[GeneratedFile]  # FluentValidation
    
    infrastructure: "InfrastructureFiles"
    tests: list[GeneratedFile]  # Unit tests
    openapi_spec: GeneratedFile  # openapi.json

@dataclass
class InfrastructureFiles:
    db_context: GeneratedFile
    audit_interceptor: GeneratedFile
    exception_handler: GeneratedFile
    auth_handler: GeneratedFile
```

## Code Generation Templates

Using Jinja2 for template rendering. Templates generate C# code for .NET Core.

### Entity Model Template

```jinja2
{# templates/dotnet/model.cs.j2 #}
// {{ file_path }}
// Generated by API Forge - Do not edit manually
// Generated: {{ generated_at }}

using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace {{ namespace }}.Models;

/// <summary>
/// Entity representing the {{ table_name }} table
/// {% if table_comment %}
/// {{ table_comment }}
/// {% endif %}
/// </summary>
[Table("{{ table_name }}", Schema = "{{ schema_name }}")]
public class {{ entity_name }}
{
{% for column in columns %}
    {% if column.comment %}
    /// <summary>
    /// {{ column.comment }}
    /// </summary>
    {% endif %}
    {% if column.is_primary_key %}
    [Key]
    {% endif %}
    {% if column.is_required %}
    [Required]
    {% endif %}
    {% if column.max_length %}
    [MaxLength({{ column.max_length }})]
    {% endif %}
    [Column("{{ column.column_name }}")]
    public {{ column.csharp_type }}{% if column.nullable %}?{% endif %} {{ column.property_name }} { get; set; }{% if column.has_default %} = {{ column.default_value }};{% endif %}

{% endfor %}
{% for fk in foreign_keys %}
    // Navigation property for {{ fk.referenced_table }}
    [ForeignKey("{{ fk.column_name }}")]
    public virtual {{ fk.referenced_entity_name }}? {{ fk.navigation_property_name }} { get; set; }

{% endfor %}
{% for nav in reverse_navigations %}
    // Reverse navigation from {{ nav.referencing_table }}
    public virtual ICollection<{{ nav.referencing_entity_name }}> {{ nav.collection_property_name }} { get; set; } = new List<{{ nav.referencing_entity_name }}>();

{% endfor %}
}
```

### Controller Template

```jinja2
{# templates/dotnet/controller.cs.j2 #}
// {{ file_path }}
// Generated by API Forge

using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Authorization;
using {{ namespace }}.Models;
using {{ namespace }}.DTOs;
using {{ namespace }}.Repositories;

namespace {{ namespace }}.Controllers;

[ApiController]
[Route("{{ route_prefix }}/{{ route_name }}")]
[Produces("application/json")]
{% if requires_auth %}
[Authorize]
{% endif %}
public class {{ controller_name }} : ControllerBase
{
    private readonly I{{ repository_name }} _repository;
    private readonly ILogger<{{ controller_name }}> _logger;
    private readonly IAuditService _auditService;

    public {{ controller_name }}(
        I{{ repository_name }} repository,
        ILogger<{{ controller_name }}> logger,
        IAuditService auditService)
    {
        _repository = repository;
        _logger = logger;
        _auditService = auditService;
    }

    /// <summary>
    /// Get all {{ resource_name_plural }}
    /// </summary>
    [HttpGet]
    [ProducesResponseType(typeof(PagedResult<{{ dto_name }}>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PagedResult<{{ dto_name }}>>> GetAll(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        [FromQuery] string? sortBy = null,
        [FromQuery] string? filter = null)
    {
        var result = await _repository.GetPagedAsync(page, pageSize, sortBy, filter);
        return Ok(result);
    }

    /// <summary>
    /// Get {{ resource_name }} by ID
    /// </summary>
    [HttpGet("{id}")]
    [ProducesResponseType(typeof({{ dto_name }}), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<{{ dto_name }}>> GetById({{ primary_key_type }} id)
    {
        var entity = await _repository.GetByIdAsync(id);
        if (entity == null)
        {
            return NotFound();
        }
        return Ok(entity.ToDto());
    }

{% if not read_only %}
    /// <summary>
    /// Create new {{ resource_name }}
    /// </summary>
    [HttpPost]
    [ProducesResponseType(typeof({{ dto_name }}), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<{{ dto_name }}>> Create([FromBody] Create{{ dto_name }}Request request)
    {
        var entity = request.ToEntity();
        
        // Audit trail
        await _auditService.LogCreateAsync(User, "{{ table_name }}", entity);
        
        var created = await _repository.CreateAsync(entity);
        return CreatedAtAction(nameof(GetById), new { id = created.{{ primary_key_property }} }, created.ToDto());
    }

    /// <summary>
    /// Update {{ resource_name }}
    /// </summary>
    [HttpPut("{id}")]
    [ProducesResponseType(typeof({{ dto_name }}), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<{{ dto_name }}>> Update({{ primary_key_type }} id, [FromBody] Update{{ dto_name }}Request request)
    {
        var existing = await _repository.GetByIdAsync(id);
        if (existing == null)
        {
            return NotFound();
        }

        var previousValues = existing.Clone();
        request.ApplyTo(existing);
        
        // Audit trail with before/after
        await _auditService.LogUpdateAsync(User, "{{ table_name }}", id, previousValues, existing);
        
        var updated = await _repository.UpdateAsync(existing);
        return Ok(updated.ToDto());
    }

    /// <summary>
    /// Delete {{ resource_name }}
    /// </summary>
    [HttpDelete("{id}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Delete({{ primary_key_type }} id)
    {
        var existing = await _repository.GetByIdAsync(id);
        if (existing == null)
        {
            return NotFound();
        }

        // Audit trail
        await _auditService.LogDeleteAsync(User, "{{ table_name }}", id, existing);
        
        {% if soft_delete %}
        await _repository.SoftDeleteAsync(id);
        {% else %}
        await _repository.DeleteAsync(id);
        {% endif %}
        
        return NoContent();
    }
{% endif %}

    /// <summary>
    /// Get audit history for {{ resource_name }}
    /// </summary>
    [HttpGet("{id}/history")]
    [ProducesResponseType(typeof(IEnumerable<AuditLogEntry>), StatusCodes.Status200OK)]
    public async Task<ActionResult<IEnumerable<AuditLogEntry>>> GetHistory({{ primary_key_type }} id)
    {
        var history = await _auditService.GetHistoryAsync("{{ table_name }}", id.ToString());
        return Ok(history);
    }
}
```

### Audit Service Template

```jinja2
{# templates/dotnet/audit_service.cs.j2 #}
// Infrastructure/AuditService.cs
// Generated by API Forge

using System.Security.Claims;
using System.Text.Json;

namespace {{ namespace }}.Infrastructure;

public interface IAuditService
{
    Task LogCreateAsync<T>(ClaimsPrincipal user, string tableName, T entity);
    Task LogUpdateAsync<T>(ClaimsPrincipal user, string tableName, object id, T before, T after);
    Task LogDeleteAsync<T>(ClaimsPrincipal user, string tableName, object id, T entity);
    Task<IEnumerable<AuditLogEntry>> GetHistoryAsync(string tableName, string entityId);
}

public class AuditService : IAuditService
{
    private readonly {{ db_context_name }} _context;
    private readonly ILogger<AuditService> _logger;

    public AuditService({{ db_context_name }} context, ILogger<AuditService> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task LogCreateAsync<T>(ClaimsPrincipal user, string tableName, T entity)
    {
        var entry = new AuditLog
        {
            Id = Guid.NewGuid(),
            TableName = tableName,
            Operation = "CREATE",
            UserId = GetUserId(user),
            UserName = GetUserName(user),
            Timestamp = DateTime.UtcNow,
            NewValues = JsonSerializer.Serialize(entity),
            IpAddress = GetIpAddress(),
            ApplicationName = "{{ project_name }}"
        };

        _context.AuditLogs.Add(entry);
        await _context.SaveChangesAsync();
        
        _logger.LogInformation(
            "Audit: {Operation} on {Table} by {User}", 
            entry.Operation, tableName, entry.UserName);
    }

    // ... (rest of implementation same as before)
}
```

## Type Mapping

```typescript
interface TypeMapping {
  // Oracle to C#
  oracle: {
    'NUMBER': 'decimal',
    'NUMBER(1)': 'bool',
    'NUMBER(10)': 'int',
    'NUMBER(19)': 'long',
    'VARCHAR2': 'string',
    'NVARCHAR2': 'string',
    'CHAR': 'string',
    'DATE': 'DateTime',
    'TIMESTAMP': 'DateTime',
    'CLOB': 'string',
    'BLOB': 'byte[]',
    'RAW': 'byte[]',
  },
  
  // SQL Server to C#
  sqlserver: {
    'int': 'int',
    'bigint': 'long',
    'smallint': 'short',
    'tinyint': 'byte',
    'bit': 'bool',
    'decimal': 'decimal',
    'numeric': 'decimal',
    'money': 'decimal',
    'float': 'double',
    'real': 'float',
    'varchar': 'string',
    'nvarchar': 'string',
    'char': 'string',
    'text': 'string',
    'datetime': 'DateTime',
    'datetime2': 'DateTime',
    'date': 'DateOnly',
    'time': 'TimeOnly',
    'uniqueidentifier': 'Guid',
    'varbinary': 'byte[]',
    'image': 'byte[]',
  }
}
```

## CLI Interface

Using Typer for a clean CLI:

```python
import typer
from pathlib import Path
from typing import Optional
from enum import Enum

app = typer.Typer(help="Generate REST APIs from database schema")

class TargetFramework(str, Enum):
    dotnet = "dotnet"
    java = "java"  # V2

@app.command()
def generate(
    schema: Path = typer.Option(..., "--schema", "-s", help="Database Insight JSON file"),
    output: Path = typer.Option(..., "--output", "-o", help="Output directory"),
    project_name: str = typer.Option(..., "--project", "-p", help="Project name"),
    target: TargetFramework = typer.Option(TargetFramework.dotnet, "--target", "-t"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file"),
):
    """
    Generate REST API from Database Insight schema.
    """
    # ...

@app.command()
def validate(
    schema: Path = typer.Option(..., "--schema", "-s", help="Schema file to validate"),
):
    """
    Validate schema file compatibility.
    """
    # ...

@app.command()
def openapi(
    schema: Path = typer.Option(..., "--schema", "-s", help="Database Insight JSON"),
    output: Path = typer.Option(..., "--output", "-o", help="Output file"),
):
    """
    Generate OpenAPI spec only (no code).
    """
    # ...

if __name__ == "__main__":
    app()
```

**Usage examples:**

```bash
# Basic usage
api-forge generate \
  --schema ./database-insight-output/schema.json \
  --output ./generated-api \
  --project "Acme.Manufacturing.Api"

# With configuration file
api-forge generate --config ./api-forge.json

# Validation only (no generation)
api-forge validate --schema ./schema.json

# Generate OpenAPI spec only
api-forge openapi \
  --schema ./schema.json \
  --output ./openapi.json
```

## Generated Project Structure

```
Acme.Manufacturing.Api/
├── Acme.Manufacturing.Api.csproj
├── Program.cs
├── appsettings.json
├── appsettings.Development.json
├── Dockerfile
├── .dockerignore
│
├── Models/
│   ├── Product.cs
│   ├── Order.cs
│   ├── Customer.cs
│   └── AuditLog.cs
│
├── DTOs/
│   ├── ProductDto.cs
│   ├── CreateProductRequest.cs
│   ├── UpdateProductRequest.cs
│   └── ...
│
├── Controllers/
│   ├── ProductsController.cs
│   ├── OrdersController.cs
│   ├── CustomersController.cs
│   └── AuditController.cs
│
├── Repositories/
│   ├── IProductRepository.cs
│   ├── ProductRepository.cs
│   └── ...
│
├── Validators/
│   ├── CreateProductValidator.cs
│   └── ...
│
├── Infrastructure/
│   ├── AppDbContext.cs
│   ├── AuditService.cs
│   ├── GlobalExceptionHandler.cs
│   └── Extensions/
│       ├── ServiceCollectionExtensions.cs
│       └── MappingExtensions.cs
│
├── Migrations/
│   └── (EF migrations if needed)
│
└── Tests/
    ├── Acme.Manufacturing.Api.Tests.csproj
    └── Controllers/
        └── ProductsControllerTests.cs
```

## Development Phases

### Phase 1: Core Generation (Week 1-2)
- [ ] Project scaffolding (Python, Poetry, pytest)
- [ ] Schema parser (Database Insight JSON via Pydantic)
- [ ] Type mapping engine (Oracle → C#, SQL Server → C#)
- [ ] Entity model generator
- [ ] Basic DbContext generator
- [ ] Project file (.csproj) generator

### Phase 2: API Layer (Week 3-4)
- [ ] DTO generators (Request/Response)
- [ ] Controller generator with CRUD
- [ ] Repository pattern implementation
- [ ] Swagger/OpenAPI integration
- [ ] Validation generator (FluentValidation)

### Phase 3: Audit & Compliance (Week 5-6)
- [ ] Audit service generator
- [ ] Audit log entity and migrations
- [ ] History endpoints
- [ ] Soft delete support
- [ ] Before/after value capture

### Phase 4: Polish & Testing (Week 7-8)
- [ ] Authentication scaffolding (JWT/Windows)
- [ ] Unit test generators
- [ ] Dockerfile generation
- [ ] Configuration management
- [ ] Oracle-specific optimizations
- [ ] Nuitka compilation for distribution

## Testing Strategy

### Generator Tests
- Template rendering tests
- Type mapping tests
- Full generation tests with snapshot comparison

```python
# tests/test_generation.py
import pytest
from pathlib import Path
from api_forge.generator import generate_project
from api_forge.models import ApiForgeConfig

def test_generates_valid_csproj(sample_schema, tmp_path):
    config = ApiForgeConfig(
        input={"schema_file": sample_schema},
        output={"directory": tmp_path, "project_name": "Test.Api"},
        ...
    )
    project = generate_project(config)
    
    assert (tmp_path / "Test.Api.csproj").exists()
    # Verify XML is valid
    # ...

def test_controller_has_audit_endpoints(sample_schema, tmp_path):
    # ...
```

### Generated Code Tests
- Build verification (generated code compiles)
- Swagger spec validation
- Runtime tests with in-memory database

### Integration Tests
- Generate from known schema
- Build generated project (`dotnet build`)
- Run generated tests (`dotnet test`)
- Verify API endpoints work

## Error Handling

```python
class ApiForgeError(Exception):
    """Base exception for API Forge"""
    def __init__(self, message: str, code: str, context: dict = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}

class SchemaValidationError(ApiForgeError):
    """Schema file is invalid or incompatible"""
    pass

class TemplateError(ApiForgeError):
    """Error rendering code template"""
    pass

class TypeMappingError(ApiForgeError):
    """Unable to map database type to target language"""
    pass

# Error codes
class ErrorCode:
    SCHEMA_INVALID = 'SCHEMA_INVALID'
    SCHEMA_NOT_FOUND = 'SCHEMA_NOT_FOUND'
    TYPE_MAPPING_FAILED = 'TYPE_MAP_FAILED'
    TEMPLATE_ERROR = 'TEMPLATE_ERROR'
    OUTPUT_WRITE_FAILED = 'OUTPUT_WRITE_FAILED'
    UNSUPPORTED_DATABASE = 'UNSUPPORTED_DB'
```

## Integration with UI Forge

API Forge outputs:
1. Generated API project
2. `openapi.json` - OpenAPI 3.0 specification

UI Forge consumes:
- `openapi.json` for endpoint discovery
- Schema information embedded in OpenAPI spec
- Validation rules from OpenAPI spec

Key OpenAPI extensions for UI Forge:

```json
{
  "paths": {
    "/api/v1/products": {
      "get": {
        "x-ui-forge": {
          "displayName": "Products",
          "icon": "package",
          "listView": {
            "columns": ["name", "sku", "price", "status"],
            "defaultSort": "name",
            "searchFields": ["name", "sku"]
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "Product": {
        "x-ui-forge": {
          "formLayout": "two-column",
          "fieldGroups": [
            { "name": "Basic Info", "fields": ["name", "sku", "description"] },
            { "name": "Pricing", "fields": ["price", "cost", "margin"] }
          ]
        }
      }
    }
  }
}
```

---

**Document Version**: 1.1  
**Last Updated**: November 2024  
**Generator Language**: Python 3.11+
**Output Targets**: .NET 8 (V1), Java Spring Boot (V2)
**Status**: Ready for Development
-e 

---


# UI Forge - Technical Design Document

## Overview

UI Forge generates functional React applications from OpenAPI specifications produced by API Forge. It creates working CRUD interfaces that can serve as production admin tools or starting points for custom development.

## Purpose

- Generate complete React applications from OpenAPI specs
- Create functional CRUD interfaces out of the box
- Produce clean, customizable code (not a runtime framework)
- Enable immediate retirement of legacy UI screens
- Provide foundation for further development

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          UI Forge                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   OpenAPI    │    │   Component  │    │   Project    │      │
│  │   Parser     │───▶│   Generator  │───▶│   Builder    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Endpoints    │    │ List Views   │    │ package.json │      │
│  │ Schemas      │    │ Detail Views │    │ vite.config  │      │
│  │ Validation   │    │ Forms        │    │ tailwind     │      │
│  │ x-ui-forge   │    │ Navigation   │    │ tsconfig     │      │
│  │ extensions   │    │ API Client   │    │ Components   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

- **Generator Runtime**: Node.js 20+ (TypeScript)
- **Output Target**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **State Management**: TanStack Query (React Query)
- **Forms**: React Hook Form + Zod
- **Tables**: TanStack Table
- **Routing**: React Router v6
- **Icons**: Lucide React
- **Templating**: Handlebars (for code generation)

### Rationale

React + TypeScript because:
- Industry standard, widely understood
- Strong typing matches API contracts
- Large ecosystem of components
- Easy to customize generated code

Tailwind CSS because:
- Utility-first enables quick customization
- No CSS file management
- Consistent design system
- Works well with code generation

TanStack Query because:
- Handles caching, refetching, optimistic updates
- Reduces boilerplate for API calls
- Works seamlessly with REST APIs

## Data Models

### Input: OpenAPI Specification

```typescript
interface OpenAPIInput {
  openapi: string;              // "3.0.0"
  info: {
    title: string;
    version: string;
  };
  paths: Record<string, PathItem>;
  components: {
    schemas: Record<string, SchemaObject>;
    securitySchemes?: Record<string, SecurityScheme>;
  };
}

// UI Forge extensions in OpenAPI
interface UIForgeExtensions {
  'x-ui-forge'?: {
    // Endpoint level
    displayName?: string;
    icon?: string;
    hidden?: boolean;           // Don't generate UI for this endpoint
    
    // List view config
    listView?: {
      columns: string[];
      defaultSort?: string;
      searchFields?: string[];
      filters?: FilterConfig[];
    };
    
    // Form config
    formLayout?: 'single-column' | 'two-column';
    fieldGroups?: FieldGroup[];
  };
}

interface FilterConfig {
  field: string;
  type: 'text' | 'select' | 'date-range' | 'number-range';
  label: string;
  options?: { value: string; label: string }[];  // For select
}

interface FieldGroup {
  name: string;
  description?: string;
  fields: string[];
  collapsible?: boolean;
}
```

### Configuration Model

```typescript
interface UIForgeConfig {
  input: {
    openApiFile: string;        // Path to OpenAPI spec
  };
  output: {
    directory: string;
    projectName: string;        // e.g., "acme-admin"
  };
  api: {
    baseUrl: string;            // Runtime API base URL
    authType: 'jwt' | 'cookie' | 'none';
  };
  ui: {
    title: string;              // App title
    logo?: string;              // Path to logo file
    primaryColor: string;       // Hex color
    dateFormat: string;         // e.g., "dd/MM/yyyy"
    timezone: string;           // e.g., "Europe/Dublin"
  };
  generation: {
    includeAuth: boolean;       // Generate login page
    includeAuditViewer: boolean;
    includeDarkMode: boolean;
    generateTests: boolean;
  };
  resources: {
    include: string[];          // Endpoint paths to include
    exclude: string[];
    overrides: ResourceOverride[];
  };
}

interface ResourceOverride {
  path: string;                 // e.g., "/api/v1/products"
  displayName?: string;
  icon?: string;
  columns?: string[];
  formFields?: FormFieldOverride[];
  actions?: ActionOverride[];
}

interface FormFieldOverride {
  name: string;
  label?: string;
  type?: 'text' | 'textarea' | 'select' | 'date' | 'number' | 'checkbox' | 'hidden';
  placeholder?: string;
  helpText?: string;
  options?: { value: string; label: string }[];
  dependsOn?: string;           // Conditional visibility
}

interface ActionOverride {
  name: string;
  label: string;
  icon?: string;
  type: 'primary' | 'secondary' | 'danger';
  handler: 'delete' | 'custom';
  confirmMessage?: string;
}
```

### Resource Model (Internal)

```typescript
interface Resource {
  name: string;                 // e.g., "products"
  displayName: string;          // e.g., "Products"
  basePath: string;             // e.g., "/api/v1/products"
  icon: string;
  
  // CRUD operations available
  operations: {
    list: boolean;
    get: boolean;
    create: boolean;
    update: boolean;
    delete: boolean;
  };
  
  // Schema information
  schema: {
    properties: PropertyInfo[];
    primaryKey: string;
    required: string[];
  };
  
  // UI configuration
  listConfig: ListConfig;
  formConfig: FormConfig;
  
  // Related resources
  relationships: Relationship[];
}

interface PropertyInfo {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'date' | 'datetime' | 'array' | 'object';
  format?: string;              // From OpenAPI format
  nullable: boolean;
  description?: string;
  enum?: string[];
  minLength?: number;
  maxLength?: number;
  minimum?: number;
  maximum?: number;
  pattern?: string;
  
  // UI hints
  displayName: string;
  inputType: InputType;
  showInList: boolean;
  showInForm: boolean;
  readOnly: boolean;
}

type InputType = 
  | 'text' 
  | 'textarea' 
  | 'number' 
  | 'email' 
  | 'password'
  | 'date' 
  | 'datetime' 
  | 'select' 
  | 'multi-select'
  | 'checkbox' 
  | 'radio'
  | 'file'
  | 'hidden';

interface Relationship {
  type: 'belongsTo' | 'hasMany';
  resource: string;
  foreignKey: string;
  displayField: string;         // Field to show in dropdowns
}
```

## Code Generation Templates

### API Client Template

```handlebars
// src/api/client.ts
// Generated by UI Forge

import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '{{apiBaseUrl}}',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
api.interceptors.request.use((config) => {
  {{#if useJwt}}
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  {{/if}}
  return config;
});

// Response interceptor for errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      {{#if useJwt}}
      localStorage.removeItem('token');
      window.location.href = '/login';
      {{/if}}
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Resource API Template

```handlebars
// src/api/{{resourceName}}.ts
// Generated by UI Forge

import api from './client';
import type { {{typeName}}, Create{{typeName}}Request, Update{{typeName}}Request, PagedResult } from '../types/{{resourceName}}';

export interface {{typeName}}QueryParams {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  search?: string;
  {{#each filters}}
  {{name}}?: {{type}};
  {{/each}}
}

export const {{resourceName}}Api = {
  {{#if operations.list}}
  async list(params: {{typeName}}QueryParams = {}): Promise<PagedResult<{{typeName}}>> {
    const { data } = await api.get('{{basePath}}', { params });
    return data;
  },
  {{/if}}

  {{#if operations.get}}
  async get(id: {{primaryKeyType}}): Promise<{{typeName}}> {
    const { data } = await api.get(`{{basePath}}/${id}`);
    return data;
  },
  {{/if}}

  {{#if operations.create}}
  async create(payload: Create{{typeName}}Request): Promise<{{typeName}}> {
    const { data } = await api.post('{{basePath}}', payload);
    return data;
  },
  {{/if}}

  {{#if operations.update}}
  async update(id: {{primaryKeyType}}, payload: Update{{typeName}}Request): Promise<{{typeName}}> {
    const { data } = await api.put(`{{basePath}}/${id}`, payload);
    return data;
  },
  {{/if}}

  {{#if operations.delete}}
  async delete(id: {{primaryKeyType}}): Promise<void> {
    await api.delete(`{{basePath}}/${id}`);
  },
  {{/if}}

  async getHistory(id: {{primaryKeyType}}): Promise<AuditLogEntry[]> {
    const { data } = await api.get(`{{basePath}}/${id}/history`);
    return data;
  },
};
```

### List View Component Template

```handlebars
// src/pages/{{resourceName}}/{{typeName}}List.tsx
// Generated by UI Forge

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { {{resourceName}}Api, type {{typeName}}QueryParams } from '../../api/{{resourceName}}';
import { DataTable } from '../../components/DataTable';
import { Button } from '../../components/Button';
import { SearchInput } from '../../components/SearchInput';
import { Pagination } from '../../components/Pagination';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { {{icon}} } from 'lucide-react';
import type { {{typeName}} } from '../../types/{{resourceName}}';

const columns = [
  {{#each listColumns}}
  {
    key: '{{name}}',
    header: '{{displayName}}',
    {{#if sortable}}
    sortable: true,
    {{/if}}
    {{#if formatter}}
    render: (value: {{type}}) => {{formatter}},
    {{/if}}
  },
  {{/each}}
];

export function {{typeName}}List() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [params, setParams] = useState<{{typeName}}QueryParams>({
    page: 1,
    pageSize: 20,
  });
  const [deleteId, setDeleteId] = useState<{{primaryKeyType}} | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['{{resourceName}}', params],
    queryFn: () => {{resourceName}}Api.list(params),
  });

  {{#if operations.delete}}
  const deleteMutation = useMutation({
    mutationFn: {{resourceName}}Api.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['{{resourceName}}'] });
      setDeleteId(null);
    },
  });
  {{/if}}

  const handleSearch = (search: string) => {
    setParams((prev) => ({ ...prev, search, page: 1 }));
  };

  const handleSort = (sortBy: string, sortOrder: 'asc' | 'desc') => {
    setParams((prev) => ({ ...prev, sortBy, sortOrder }));
  };

  const handlePageChange = (page: number) => {
    setParams((prev) => ({ ...prev, page }));
  };

  if (error) {
    return <div className="text-red-600">Error loading {{displayName}}</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <{{icon}} className="h-8 w-8 text-gray-400" />
          <h1 className="text-2xl font-semibold text-gray-900">{{displayName}}</h1>
        </div>
        {{#if operations.create}}
        <Link to="/{{resourceName}}/new">
          <Button>Add {{singularDisplayName}}</Button>
        </Link>
        {{/if}}
      </div>

      <div className="flex items-center gap-4">
        <SearchInput
          placeholder="Search {{displayName}}..."
          onSearch={handleSearch}
        />
        {{#each filters}}
        {/* Filter: {{label}} */}
        {{/each}}
      </div>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        isLoading={isLoading}
        sortBy={params.sortBy}
        sortOrder={params.sortOrder}
        onSort={handleSort}
        onRowClick={(row) => navigate(`/{{resourceName}}/${row.{{primaryKey}}}`)}
        actions={(row) => (
          <div className="flex gap-2">
            {{#if operations.update}}
            <Link to={`/{{resourceName}}/${row.{{primaryKey}}}/edit`}>
              <Button variant="secondary" size="sm">Edit</Button>
            </Link>
            {{/if}}
            {{#if operations.delete}}
            <Button
              variant="danger"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setDeleteId(row.{{primaryKey}});
              }}
            >
              Delete
            </Button>
            {{/if}}
          </div>
        )}
      />

      {data && (
        <Pagination
          currentPage={data.page}
          totalPages={data.totalPages}
          totalItems={data.totalItems}
          onPageChange={handlePageChange}
        />
      )}

      {{#if operations.delete}}
      <ConfirmDialog
        isOpen={deleteId !== null}
        title="Delete {{singularDisplayName}}"
        message="Are you sure you want to delete this {{singularDisplayName}}? This action cannot be undone."
        confirmLabel="Delete"
        onConfirm={() => deleteId && deleteMutation.mutate(deleteId)}
        onCancel={() => setDeleteId(null)}
        isLoading={deleteMutation.isPending}
      />
      {{/if}}
    </div>
  );
}
```

### Form Component Template

```handlebars
// src/pages/{{resourceName}}/{{typeName}}Form.tsx
// Generated by UI Forge

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { z } from 'zod';
import { {{resourceName}}Api } from '../../api/{{resourceName}}';
import { Button } from '../../components/Button';
import { FormField } from '../../components/FormField';
import { Card } from '../../components/Card';
import type { Create{{typeName}}Request, Update{{typeName}}Request } from '../../types/{{resourceName}}';

const schema = z.object({
  {{#each formFields}}
  {{name}}: z.{{zodType}}({{zodArgs}}){{#if optional}}.optional(){{/if}}{{#if nullable}}.nullable(){{/if}},
  {{/each}}
});

type FormData = z.infer<typeof schema>;

interface {{typeName}}FormProps {
  mode: 'create' | 'edit';
}

export function {{typeName}}Form({ mode }: {{typeName}}FormProps) {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: existing, isLoading: isLoadingExisting } = useQuery({
    queryKey: ['{{resourceName}}', id],
    queryFn: () => {{resourceName}}Api.get({{primaryKeyCast}}id!),
    enabled: mode === 'edit' && !!id,
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  useEffect(() => {
    if (existing) {
      reset(existing);
    }
  }, [existing, reset]);

  const createMutation = useMutation({
    mutationFn: {{resourceName}}Api.create,
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ['{{resourceName}}'] });
      navigate(`/{{resourceName}}/${created.{{primaryKey}}}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: {{primaryKeyType}}; data: Update{{typeName}}Request }) =>
      {{resourceName}}Api.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['{{resourceName}}'] });
      navigate(`/{{resourceName}}/${id}`);
    },
  });

  const onSubmit = (data: FormData) => {
    if (mode === 'create') {
      createMutation.mutate(data as Create{{typeName}}Request);
    } else {
      updateMutation.mutate({ id: {{primaryKeyCast}}id!, data: data as Update{{typeName}}Request });
    }
  };

  if (mode === 'edit' && isLoadingExisting) {
    return <div>Loading...</div>;
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">
          {mode === 'create' ? 'New {{singularDisplayName}}' : 'Edit {{singularDisplayName}}'}
        </h1>
      </div>

      {{#each fieldGroups}}
      <Card>
        <Card.Header>
          <Card.Title>{{name}}</Card.Title>
          {{#if description}}
          <Card.Description>{{description}}</Card.Description>
          {{/if}}
        </Card.Header>
        <Card.Content className="{{#if twoColumn}}grid grid-cols-2 gap-4{{else}}space-y-4{{/if}}">
          {{#each fields}}
          <FormField
            label="{{label}}"
            error={errors.{{name}}?.message}
            {{#if helpText}}
            helpText="{{helpText}}"
            {{/if}}
          >
            {{#if (eq inputType 'textarea')}}
            <textarea
              {...register('{{name}}')}
              className="input"
              rows={4}
              {{#if placeholder}}placeholder="{{placeholder}}"{{/if}}
            />
            {{else if (eq inputType 'select')}}
            <select {...register('{{name}}')} className="input">
              <option value="">Select {{label}}</option>
              {{#each options}}
              <option value="{{value}}">{{label}}</option>
              {{/each}}
            </select>
            {{else if (eq inputType 'checkbox')}}
            <input
              type="checkbox"
              {...register('{{name}}')}
              className="checkbox"
            />
            {{else if (eq inputType 'date')}}
            <input
              type="date"
              {...register('{{name}}')}
              className="input"
            />
            {{else if (eq inputType 'number')}}
            <input
              type="number"
              {...register('{{name}}', { valueAsNumber: true })}
              className="input"
              {{#if placeholder}}placeholder="{{placeholder}}"{{/if}}
            />
            {{else}}
            <input
              type="{{inputType}}"
              {...register('{{name}}')}
              className="input"
              {{#if placeholder}}placeholder="{{placeholder}}"{{/if}}
            />
            {{/if}}
          </FormField>
          {{/each}}
        </Card.Content>
      </Card>
      {{/each}}

      <div className="flex justify-end gap-4">
        <Button
          type="button"
          variant="secondary"
          onClick={() => navigate(-1)}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Saving...' : 'Save {{singularDisplayName}}'}
        </Button>
      </div>
    </form>
  );
}
```

## Component Library

UI Forge generates a set of reusable components:

```
src/components/
├── Button.tsx           # Primary, secondary, danger variants
├── Card.tsx             # Card with header, content, footer
├── DataTable.tsx        # Sortable, clickable table
├── ConfirmDialog.tsx    # Modal confirmation dialog
├── FormField.tsx        # Label, input, error wrapper
├── SearchInput.tsx      # Debounced search input
├── Pagination.tsx       # Page navigation
├── Sidebar.tsx          # Navigation sidebar
├── TopBar.tsx           # Header with user menu
├── LoadingSpinner.tsx   # Loading indicator
├── EmptyState.tsx       # No data message
├── Badge.tsx            # Status badges
├── Tabs.tsx             # Tab navigation
├── AuditHistory.tsx     # Audit log viewer
└── DateDisplay.tsx      # Formatted date/time
```

## Generated Project Structure

```
acme-admin/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
├── index.html
├── .env.example
│
├── public/
│   └── logo.svg
│
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── routes.tsx
│   │
│   ├── api/
│   │   ├── client.ts
│   │   ├── products.ts
│   │   ├── orders.ts
│   │   └── customers.ts
│   │
│   ├── types/
│   │   ├── products.ts
│   │   ├── orders.ts
│   │   └── customers.ts
│   │
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Login.tsx
│   │   ├── products/
│   │   │   ├── ProductList.tsx
│   │   │   ├── ProductDetail.tsx
│   │   │   └── ProductForm.tsx
│   │   ├── orders/
│   │   │   └── ...
│   │   └── customers/
│   │       └── ...
│   │
│   ├── components/
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── DataTable.tsx
│   │   └── ...
│   │
│   ├── layouts/
│   │   ├── MainLayout.tsx
│   │   └── AuthLayout.tsx
│   │
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   └── useDebounce.ts
│   │
│   └── utils/
│       ├── formatters.ts
│       └── validators.ts
│
└── tests/
    └── ...
```

## CLI Interface

```bash
# Basic usage
ui-forge generate \
  --openapi ./api-forge-output/openapi.json \
  --output ./generated-ui \
  --project-name "acme-admin"

# With configuration file
ui-forge generate --config ./ui-forge.json

# Preview mode (generates to temp directory, starts dev server)
ui-forge preview --openapi ./openapi.json

# Validate OpenAPI spec compatibility
ui-forge validate --openapi ./openapi.json
```

## Development Phases

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Project scaffolding
- [ ] OpenAPI parser
- [ ] Resource discovery from OpenAPI
- [ ] Type generation from schemas
- [ ] Project file generators (package.json, vite.config, etc.)
- [ ] Component library implementation

### Phase 2: CRUD Generation (Week 3-4)
- [ ] List view generator
- [ ] Detail view generator
- [ ] Form generator (create/edit)
- [ ] API client generator
- [ ] Routing setup
- [ ] Navigation/sidebar

### Phase 3: Polish & Features (Week 5-6)
- [ ] Validation from OpenAPI schema
- [ ] Relationship handling (dropdowns for foreign keys)
- [ ] Search and filtering
- [ ] Sorting and pagination
- [ ] Audit history viewer
- [ ] Dark mode support

### Phase 4: Authentication & Testing (Week 7-8)
- [ ] JWT authentication flow
- [ ] Login page
- [ ] Protected routes
- [ ] Test generation
- [ ] Build optimization
- [ ] Documentation

## Testing Strategy

### Generator Tests
- OpenAPI parsing tests
- Template rendering tests
- Full generation with snapshot comparison

### Generated Code Tests
- Build verification
- Component unit tests (generated)
- E2E tests with mock API

## Error Handling

```typescript
class UIForgeError extends Error {
  constructor(
    message: string,
    public code: string,
    public context?: Record<string, unknown>
  ) {
    super(message);
  }
}

const ErrorCodes = {
  OPENAPI_INVALID: 'OPENAPI_INVALID',
  OPENAPI_NOT_FOUND: 'OPENAPI_NOT_FOUND',
  NO_RESOURCES_FOUND: 'NO_RESOURCES',
  TEMPLATE_ERROR: 'TEMPLATE_ERROR',
  OUTPUT_WRITE_FAILED: 'OUTPUT_WRITE_FAILED',
};
```

---

**Document Version**: 1.0  
**Last Updated**: November 2024  
**Status**: Ready for Development
-e 

---


# Logic Mapper - Technical Design Document

## Overview

Logic Mapper analyzes legacy codebases to extract, document, and categorize business logic. It identifies where logic currently resides, recommends optimal placement in a modern architecture, and generates migration scaffolding.

## Purpose

- Parse and analyze legacy code (ASP, VBScript, .NET, PL/SQL, T-SQL)
- Extract business rules from procedural code
- Map dependencies between logic and data
- Recommend above-API vs below-API placement
- Generate migration scaffolding and test cases
- Preserve institutional knowledge during modernization

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Logic Mapper                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Code       │    │   Logic      │    │   Output     │      │
│  │   Parsers    │───▶│   Analyzer   │───▶│   Generator  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ ASP/VBScript │    │ Rule         │    │ Inventory    │      │
│  │ .NET         │    │ Extractor    │    │ Report       │      │
│  │ PL/SQL       │    │              │    │              │      │
│  │ T-SQL        │    │ Dependency   │    │ Migration    │      │
│  │              │    │ Mapper       │    │ Scaffolding  │      │
│  │              │    │              │    │              │      │
│  │              │    │ Placement    │    │ Test Cases   │      │
│  │              │    │ Recommender  │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    AI Assistant Layer                        ││
│  │         (Claude API for complex pattern recognition)         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

- **Runtime**: Node.js 20+ (TypeScript)
- **Parsing**: 
  - Custom parsers for ASP/VBScript (no good existing tools)
  - Tree-sitter for .NET/C#
  - ANTLR grammars for PL/SQL and T-SQL
- **AI Integration**: Anthropic Claude API (for pattern recognition)
- **Output**: JSON, Markdown, Generated code
- **Testing**: Vitest

### Rationale

This is the most challenging tool because:
- VBScript/Classic ASP have no modern parsing tools
- Business logic is often implicit, not explicit
- Understanding intent requires more than syntax analysis
- AI assistance valuable for pattern recognition

## Data Models

### Input: Codebase Configuration

```typescript
interface LogicMapperConfig {
  input: {
    directories: DirectoryConfig[];
    schemaFile?: string;          // Database Insight output for correlation
  };
  output: {
    directory: string;
    formats: ('json' | 'markdown' | 'html')[];
  };
  analysis: {
    includePatterns: string[];    // Glob patterns
    excludePatterns: string[];
    maxFileSize: number;          // Skip very large files
  };
  ai: {
    enabled: boolean;
    apiKey?: string;              // Or use env var
    maxTokensPerFile: number;     // Cost control
  };
  migration: {
    targetPlatform: 'dotnet' | 'node';
    generateScaffolding: boolean;
    generateTests: boolean;
  };
}

interface DirectoryConfig {
  path: string;
  type: 'asp' | 'dotnet' | 'plsql' | 'tsql';
  description?: string;
}
```

### Core Logic Model

```typescript
interface LogicInventory {
  metadata: {
    analyzedAt: string;
    toolVersion: string;
    filesAnalyzed: number;
    totalLinesOfCode: number;
  };
  files: AnalyzedFile[];
  businessRules: BusinessRule[];
  dataAccess: DataAccessPattern[];
  dependencies: DependencyGraph;
  recommendations: PlacementRecommendation[];
}

interface AnalyzedFile {
  path: string;
  type: 'asp' | 'vbscript' | 'csharp' | 'vbnet' | 'plsql' | 'tsql';
  linesOfCode: number;
  
  // Structural elements
  classes?: ClassInfo[];
  functions: FunctionInfo[];
  procedures: ProcedureInfo[];
  
  // Extracted logic
  businessRules: BusinessRuleReference[];
  dataAccess: DataAccessReference[];
  
  // Quality metrics
  complexity: ComplexityMetrics;
  issues: CodeIssue[];
}

interface FunctionInfo {
  name: string;
  startLine: number;
  endLine: number;
  parameters: ParameterInfo[];
  returnType?: string;
  calledFunctions: string[];
  accessedTables: string[];
  complexity: number;           // Cyclomatic complexity
  
  // Raw source for AI analysis
  sourceCode: string;
}

interface BusinessRule {
  id: string;
  name: string;
  description: string;
  category: RuleCategory;
  
  // Source location
  sourceFile: string;
  sourceFunction: string;
  startLine: number;
  endLine: number;
  sourceCode: string;
  
  // Rule characteristics
  type: RuleType;
  dataEntities: string[];       // Tables involved
  conditions: Condition[];
  actions: Action[];
  
  // Classification
  confidence: number;           // 0-1, how confident we are in extraction
  extractionMethod: 'pattern' | 'ai' | 'manual';
  
  // Migration planning
  suggestedPlacement: 'above-api' | 'below-api' | 'both';
  placementRationale: string;
  migrationPriority: 'critical' | 'high' | 'medium' | 'low';
  migrationComplexity: 'trivial' | 'simple' | 'moderate' | 'complex';
  dependencies: string[];       // Other rule IDs
}

type RuleCategory =
  | 'validation'              // Input validation rules
  | 'calculation'             // Business calculations
  | 'workflow'                // Process/state transitions
  | 'authorization'           // Access control
  | 'data-transformation'     // Data mapping/conversion
  | 'integration'             // External system interaction
  | 'audit'                   // Logging/audit trail
  | 'notification'            // Alerts, emails
  | 'scheduling'              // Time-based rules
  | 'other';

type RuleType =
  | 'constraint'              // Must be true
  | 'derivation'              // Calculated value
  | 'reaction'                // Triggered action
  | 'inference';              // Deduced fact

interface Condition {
  description: string;
  expression: string;
  entities: string[];
  fields: string[];
}

interface Action {
  description: string;
  type: 'update' | 'insert' | 'delete' | 'calculate' | 'notify' | 'call';
  target?: string;
  details: string;
}

interface DataAccessPattern {
  id: string;
  type: 'read' | 'write' | 'read-write';
  
  // Source
  sourceFile: string;
  sourceFunction: string;
  startLine: number;
  
  // Target
  tables: string[];
  columns: string[];
  
  // Pattern details
  accessMethod: 'inline-sql' | 'stored-proc' | 'orm' | 'recordset';
  sqlStatement?: string;
  storedProcedure?: string;
  
  // Risk assessment
  hasParameterizedQueries: boolean;
  potentialInjectionRisk: boolean;
}

interface PlacementRecommendation {
  ruleId: string;
  ruleName: string;
  
  currentLocation: 'ui' | 'middleware' | 'stored-proc' | 'trigger' | 'mixed';
  recommendedPlacement: 'above-api' | 'below-api';
  
  rationale: string[];
  benefits: string[];
  risks: string[];
  
  migrationSteps: MigrationStep[];
  estimatedEffort: 'hours' | 'days' | 'weeks';
}

interface MigrationStep {
  order: number;
  description: string;
  type: 'extract' | 'transform' | 'implement' | 'test' | 'deprecate';
  details: string;
}
```

## Code Parsers

### ASP/VBScript Parser

Since no good parsing tools exist for Classic ASP/VBScript, we build a custom parser:

```typescript
interface ASPParser {
  parse(source: string, filePath: string): ASPParseResult;
}

interface ASPParseResult {
  includes: string[];           // <!-- #include --> files
  functions: VBScriptFunction[];
  subs: VBScriptSub[];
  globalVariables: Variable[];
  sqlStatements: SQLStatement[];
  adoOperations: ADOOperation[];
  errors: ParseError[];
}

interface VBScriptFunction {
  name: string;
  startLine: number;
  endLine: number;
  parameters: string[];
  localVariables: Variable[];
  calledFunctions: string[];
  sqlStatements: SQLStatement[];
  responseWrites: ResponseWrite[];
  sourceCode: string;
}

interface SQLStatement {
  line: number;
  type: 'select' | 'insert' | 'update' | 'delete' | 'exec';
  rawSql: string;
  tables: string[];             // Extracted table names
  isParameterized: boolean;
  variables: string[];          // VBScript variables used
}

interface ADOOperation {
  line: number;
  type: 'connection' | 'recordset' | 'command';
  operation: string;            // Open, Execute, MoveNext, etc.
  connectionString?: string;
}
```

### Parser Implementation Strategy

```typescript
// Simplified ASP/VBScript tokenizer
class VBScriptTokenizer {
  private source: string;
  private pos: number = 0;
  private line: number = 1;
  
  tokenize(): Token[] {
    const tokens: Token[] = [];
    
    while (this.pos < this.source.length) {
      // Skip whitespace (track newlines)
      this.skipWhitespace();
      
      // Check for ASP delimiters
      if (this.match('<%')) {
        tokens.push({ type: 'ASP_START', line: this.line });
        continue;
      }
      if (this.match('%>')) {
        tokens.push({ type: 'ASP_END', line: this.line });
        continue;
      }
      
      // Keywords
      if (this.matchKeyword('Function')) {
        tokens.push({ type: 'FUNCTION', line: this.line });
        continue;
      }
      if (this.matchKeyword('End Function')) {
        tokens.push({ type: 'END_FUNCTION', line: this.line });
        continue;
      }
      if (this.matchKeyword('Sub')) {
        tokens.push({ type: 'SUB', line: this.line });
        continue;
      }
      // ... etc for other keywords
      
      // SQL detection (look for patterns)
      if (this.lookAheadSQL()) {
        const sql = this.extractSQLStatement();
        tokens.push({ type: 'SQL', value: sql, line: this.line });
        continue;
      }
      
      // Identifiers and other tokens
      // ...
    }
    
    return tokens;
  }
  
  private lookAheadSQL(): boolean {
    const patterns = [
      /^\s*"SELECT\s/i,
      /^\s*"INSERT\s/i,
      /^\s*"UPDATE\s/i,
      /^\s*"DELETE\s/i,
      /^\s*"EXEC\s/i,
    ];
    const remaining = this.source.substring(this.pos);
    return patterns.some(p => p.test(remaining));
  }
}

// Function extractor
class VBScriptFunctionExtractor {
  extract(tokens: Token[]): VBScriptFunction[] {
    const functions: VBScriptFunction[] = [];
    let currentFunction: Partial<VBScriptFunction> | null = null;
    let braceDepth = 0;
    
    for (let i = 0; i < tokens.length; i++) {
      const token = tokens[i];
      
      if (token.type === 'FUNCTION') {
        currentFunction = {
          name: tokens[i + 1]?.value || 'unknown',
          startLine: token.line,
          parameters: [],
          calledFunctions: [],
          sqlStatements: [],
        };
      }
      
      if (token.type === 'END_FUNCTION' && currentFunction) {
        currentFunction.endLine = token.line;
        functions.push(currentFunction as VBScriptFunction);
        currentFunction = null;
      }
      
      if (currentFunction && token.type === 'SQL') {
        currentFunction.sqlStatements!.push(this.parseSQLStatement(token));
      }
      
      if (currentFunction && token.type === 'IDENTIFIER') {
        // Track function calls
        if (tokens[i + 1]?.type === 'LPAREN') {
          currentFunction.calledFunctions!.push(token.value);
        }
      }
    }
    
    return functions;
  }
}
```

### SQL Statement Analyzer

```typescript
class SQLAnalyzer {
  analyze(sql: string): SQLAnalysis {
    const normalized = this.normalize(sql);
    
    return {
      type: this.detectType(normalized),
      tables: this.extractTables(normalized),
      columns: this.extractColumns(normalized),
      conditions: this.extractConditions(normalized),
      isParameterized: this.checkParameterization(sql),
      complexity: this.assessComplexity(normalized),
    };
  }
  
  private extractTables(sql: string): string[] {
    const tables: string[] = [];
    
    // FROM clause
    const fromMatch = sql.match(/FROM\s+([^\s,]+(?:\s*,\s*[^\s,]+)*)/i);
    if (fromMatch) {
      tables.push(...fromMatch[1].split(',').map(t => t.trim()));
    }
    
    // JOIN clauses
    const joinMatches = sql.matchAll(/JOIN\s+([^\s]+)/gi);
    for (const match of joinMatches) {
      tables.push(match[1]);
    }
    
    // INSERT INTO
    const insertMatch = sql.match(/INSERT\s+INTO\s+([^\s(]+)/i);
    if (insertMatch) {
      tables.push(insertMatch[1]);
    }
    
    // UPDATE
    const updateMatch = sql.match(/UPDATE\s+([^\s]+)/i);
    if (updateMatch) {
      tables.push(updateMatch[1]);
    }
    
    return [...new Set(tables)];
  }
  
  private checkParameterization(sql: string): boolean {
    // Look for string concatenation patterns indicating non-parameterized
    const dangerPatterns = [
      /"\s*&\s*\w+\s*&\s*"/,      // " & variable & "
      /'\s*\+\s*\w+\s*\+\s*'/,    // ' + variable + '
      /"\s*\|\|\s*\w+/,           // " || variable (Oracle)
    ];
    
    return !dangerPatterns.some(p => p.test(sql));
  }
}
```

## AI Integration

For complex pattern recognition, we integrate Claude:

```typescript
interface AIAnalyzer {
  analyzeFunction(
    sourceCode: string,
    context: AnalysisContext
  ): Promise<AIAnalysisResult>;
}

interface AnalysisContext {
  fileName: string;
  functionName: string;
  language: string;
  relatedTables: string[];      // From Database Insight
  calledFunctions: string[];
  existingRules: BusinessRule[];  // Already extracted rules
}

interface AIAnalysisResult {
  businessRules: ExtractedRule[];
  dataFlows: DataFlow[];
  suggestions: string[];
  confidence: number;
}

interface ExtractedRule {
  name: string;
  description: string;
  category: RuleCategory;
  conditions: string[];
  actions: string[];
  entities: string[];
  placement: 'above-api' | 'below-api';
  rationale: string;
}

// Implementation
class ClaudeAnalyzer implements AIAnalyzer {
  private client: Anthropic;
  
  async analyzeFunction(
    sourceCode: string,
    context: AnalysisContext
  ): Promise<AIAnalysisResult> {
    const prompt = this.buildPrompt(sourceCode, context);
    
    const response = await this.client.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 4000,
      messages: [{ role: 'user', content: prompt }],
    });
    
    return this.parseResponse(response);
  }
  
  private buildPrompt(sourceCode: string, context: AnalysisContext): string {
    return `
Analyze this ${context.language} function and extract business rules.

## Context
- File: ${context.fileName}
- Function: ${context.functionName}
- Related database tables: ${context.relatedTables.join(', ')}
- Called functions: ${context.calledFunctions.join(', ')}

## Source Code
\`\`\`${context.language}
${sourceCode}
\`\`\`

## Task
1. Identify all business rules in this code
2. For each rule, provide:
   - A clear name
   - A business-level description (not technical)
   - Category (validation, calculation, workflow, authorization, data-transformation, integration, audit, notification)
   - Conditions that trigger the rule
   - Actions the rule performs
   - Database entities involved
   - Recommended placement (above-api or below-api)
   - Rationale for placement

3. Identify data flows (what data goes where)

4. Note any concerns or suggestions

## Output Format
Return a JSON object with this structure:
{
  "businessRules": [...],
  "dataFlows": [...],
  "suggestions": [...],
  "confidence": 0.0-1.0
}
`;
  }
}
```

## Placement Recommendation Engine

```typescript
class PlacementEngine {
  recommend(rule: BusinessRule, context: PlacementContext): PlacementRecommendation {
    const scores = {
      aboveApi: 0,
      belowApi: 0,
    };
    
    // Factor 1: Rule type
    if (rule.category === 'validation') {
      // Validation should be in both places, but primarily below
      scores.belowApi += 3;
      scores.aboveApi += 1;
    }
    if (rule.category === 'calculation') {
      // Simple calculations: above API
      // Complex calculations touching lots of data: below API
      if (rule.dataEntities.length > 3) {
        scores.belowApi += 3;
      } else {
        scores.aboveApi += 2;
      }
    }
    if (rule.category === 'workflow') {
      // Orchestration: above API
      scores.aboveApi += 3;
    }
    if (rule.category === 'audit') {
      // Audit at source: below API
      scores.belowApi += 4;
    }
    if (rule.category === 'integration') {
      // External systems: above API
      scores.aboveApi += 3;
    }
    
    // Factor 2: Data integrity requirements
    if (this.requiresTransactionalIntegrity(rule)) {
      scores.belowApi += 2;
    }
    
    // Factor 3: Change frequency
    if (context.changeFrequency === 'high') {
      // Frequently changing rules: above API (easier deployment)
      scores.aboveApi += 2;
    }
    
    // Factor 4: Bypass risk
    if (this.cannotAllowBypass(rule)) {
      // Rules that must never be bypassed: below API
      scores.belowApi += 3;
    }
    
    // Factor 5: Performance
    if (rule.dataEntities.length > 5) {
      // Complex data access: below API (avoid round trips)
      scores.belowApi += 2;
    }
    
    const placement = scores.belowApi > scores.aboveApi ? 'below-api' : 'above-api';
    
    return {
      ruleId: rule.id,
      ruleName: rule.name,
      currentLocation: this.determineCurrentLocation(rule),
      recommendedPlacement: placement,
      rationale: this.generateRationale(rule, scores),
      benefits: this.identifyBenefits(rule, placement),
      risks: this.identifyRisks(rule, placement),
      migrationSteps: this.generateMigrationSteps(rule, placement),
      estimatedEffort: this.estimateEffort(rule),
    };
  }
  
  private cannotAllowBypass(rule: BusinessRule): boolean {
    // Rules that enforce data integrity or audit requirements
    const criticalCategories: RuleCategory[] = ['validation', 'audit', 'authorization'];
    return criticalCategories.includes(rule.category);
  }
  
  private requiresTransactionalIntegrity(rule: BusinessRule): boolean {
    // Rules that modify multiple tables atomically
    const writeActions = rule.actions.filter(a => 
      ['update', 'insert', 'delete'].includes(a.type)
    );
    const tablesModified = new Set(writeActions.map(a => a.target));
    return tablesModified.size > 1;
  }
}
```

## Migration Scaffolding Generator

```typescript
class MigrationScaffoldGenerator {
  generate(
    rule: BusinessRule,
    recommendation: PlacementRecommendation,
    targetPlatform: 'dotnet' | 'node'
  ): GeneratedScaffold {
    if (recommendation.recommendedPlacement === 'below-api') {
      return this.generateDatabaseLogic(rule, targetPlatform);
    } else {
      return this.generateApplicationLogic(rule, targetPlatform);
    }
  }
  
  private generateDatabaseLogic(
    rule: BusinessRule,
    targetPlatform: string
  ): GeneratedScaffold {
    // Generate stored procedure or trigger
    const plsql = this.generatePLSQL(rule);
    
    return {
      files: [
        {
          path: `migrations/${rule.id}_${this.slugify(rule.name)}.sql`,
          content: plsql,
          type: 'migration',
        },
        {
          path: `docs/rules/${rule.id}.md`,
          content: this.generateRuleDocumentation(rule),
          type: 'documentation',
        },
      ],
      tests: this.generateDatabaseTests(rule),
    };
  }
  
  private generateApplicationLogic(
    rule: BusinessRule,
    targetPlatform: string
  ): GeneratedScaffold {
    if (targetPlatform === 'dotnet') {
      return this.generateDotNetService(rule);
    } else {
      return this.generateNodeService(rule);
    }
  }
  
  private generateDotNetService(rule: BusinessRule): GeneratedScaffold {
    const className = this.pascalCase(rule.name) + 'Rule';
    
    const serviceCode = `
// Generated by Logic Mapper
// Rule: ${rule.name}
// Original location: ${rule.sourceFile}:${rule.startLine}

using System;
using System.Threading.Tasks;

namespace Application.BusinessRules;

/// <summary>
/// ${rule.description}
/// </summary>
/// <remarks>
/// Category: ${rule.category}
/// Migration priority: ${rule.migrationPriority}
/// </remarks>
public class ${className} : IBusinessRule
{
    private readonly ILogger<${className}> _logger;
    ${rule.dataEntities.map(e => `private readonly I${this.pascalCase(e)}Repository _${this.camelCase(e)}Repository;`).join('\n    ')}

    public ${className}(
        ILogger<${className}> logger${rule.dataEntities.map(e => `,\n        I${this.pascalCase(e)}Repository ${this.camelCase(e)}Repository`).join('')})
    {
        _logger = logger;
        ${rule.dataEntities.map(e => `_${this.camelCase(e)}Repository = ${this.camelCase(e)}Repository;`).join('\n        ')}
    }

    public async Task<RuleResult> ExecuteAsync(RuleContext context)
    {
        // TODO: Implement business rule logic
        // Original source:
        /*
${rule.sourceCode.split('\n').map(l => '        ' + l).join('\n')}
        */
        
        // Conditions to check:
${rule.conditions.map(c => `        // - ${c.description}`).join('\n')}
        
        // Actions to perform:
${rule.actions.map(a => `        // - ${a.description}`).join('\n')}
        
        throw new NotImplementedException("Migrate logic from original source");
    }
}
`;
    
    return {
      files: [
        {
          path: `Application/BusinessRules/${className}.cs`,
          content: serviceCode,
          type: 'implementation',
        },
        {
          path: `docs/rules/${rule.id}.md`,
          content: this.generateRuleDocumentation(rule),
          type: 'documentation',
        },
      ],
      tests: this.generateDotNetTests(rule, className),
    };
  }
}
```

## CLI Interface

```bash
# Analyze codebase
logic-mapper analyze \
  --input ./legacy-code \
  --type asp \
  --schema ./database-insight-output/schema.json \
  --output ./logic-mapper-output

# With multiple directories
logic-mapper analyze \
  --config ./logic-mapper.json

# Generate migration scaffolding
logic-mapper scaffold \
  --inventory ./logic-mapper-output/inventory.json \
  --target dotnet \
  --output ./migration-scaffold

# AI-enhanced analysis
logic-mapper analyze \
  --input ./legacy-code \
  --ai-enhanced \
  --output ./logic-mapper-output
```

## Development Phases

### Phase 1: Core Parsing (Week 1-3)
- [ ] Project scaffolding
- [ ] VBScript/ASP tokenizer
- [ ] VBScript function extractor
- [ ] SQL statement extractor
- [ ] Basic inventory output

### Phase 2: Analysis Engine (Week 4-5)
- [ ] SQL analyzer (table/column extraction)
- [ ] Dependency graph builder
- [ ] Call graph analysis
- [ ] Data flow tracing
- [ ] Complexity metrics

### Phase 3: AI Integration (Week 6-7)
- [ ] Claude API integration
- [ ] Business rule extraction prompts
- [ ] Pattern recognition for common rules
- [ ] Confidence scoring
- [ ] Cost management (token limits)

### Phase 4: Output & Scaffolding (Week 8-10)
- [ ] Placement recommendation engine
- [ ] Migration scaffolding generator (.NET)
- [ ] Test case generator
- [ ] HTML report generator
- [ ] Integration with Database Insight

### Phase 5: Additional Languages (Week 11-12)
- [ ] PL/SQL parser
- [ ] T-SQL parser
- [ ] .NET/C# analysis (using Tree-sitter)
- [ ] Cross-language dependency tracking

## Testing Strategy

### Parser Tests
- Unit tests with known VBScript samples
- Edge case handling (malformed code)
- SQL extraction accuracy tests

### Analysis Tests
- Known business rules → expected extraction
- Placement recommendation validation
- Dependency graph correctness

### Integration Tests
- Full pipeline with sample legacy applications
- Correlation with Database Insight output

## Error Handling

```typescript
class LogicMapperError extends Error {
  constructor(
    message: string,
    public code: string,
    public context?: Record<string, unknown>
  ) {
    super(message);
  }
}

const ErrorCodes = {
  PARSE_ERROR: 'PARSE_ERROR',
  FILE_NOT_FOUND: 'FILE_NOT_FOUND',
  UNSUPPORTED_LANGUAGE: 'UNSUPPORTED_LANG',
  AI_API_ERROR: 'AI_API_ERROR',
  AI_QUOTA_EXCEEDED: 'AI_QUOTA_EXCEEDED',
  SCHEMA_CORRELATION_FAILED: 'SCHEMA_CORRELATION',
};
```

## Security Considerations

- Never send credentials or connection strings to AI
- Sanitize source code before AI analysis (remove hardcoded passwords)
- Support air-gapped mode (no AI, pattern-only analysis)
- Audit logging of all AI interactions

---

**Document Version**: 1.0  
**Last Updated**: November 2024  
**Status**: Ready for Development
