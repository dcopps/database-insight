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
