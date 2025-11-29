# Database Insight - Technical Architecture

**Version:** 0.1.0
**Last Updated:** November 28, 2025

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Module Reference](#module-reference)
4. [Data Models](#data-models)
5. [Parsing Strategy](#parsing-strategy)
6. [Data Flow](#data-flow)
7. [CLI Commands](#cli-commands)
8. [Extension Points](#extension-points)

---

## Overview

Database Insight is a Python CLI tool that parses and analyzes Oracle database schema exports from Toad. It converts Toad DDL SQL files into structured data models (JSON) for consumption by downstream tools in the Strangler Fig modernization framework.

### Key Features

- **Tables**: Parse CREATE TABLE statements with columns, types, constraints, and row counts
- **Views**: Extract CREATE VIEW definitions with column lists and SELECT statements
- **Procedures**: Parse stored procedures from package specifications
- **Constraints**: Extract PRIMARY KEY and FOREIGN KEY relationships
- **Export**: JSON serialization for downstream consumption (API Forge)

### Technology Stack

- **Python 3.11+**: Modern Python with type hints
- **Pydantic 2.x**: Data validation and serialization
- **Typer**: CLI framework with type-safe argument parsing
- **Rich**: Terminal output formatting with tables and colors
- **Poetry**: Dependency management and build tool

---

## Architecture

Database Insight follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│                   CLI Layer                         │
│              (cli.py - Typer/Rich)                  │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│                 Adapter Layer                       │
│          (adapters/toad_parser.py)                  │
│         Uses Regex-based parsing                    │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│                 Data Model Layer                    │
│            (models/schema.py)                       │
│          Pydantic models with validation            │
└─────────────────────────────────────────────────────┘
```

### Design Patterns

#### Adapter Pattern
The codebase uses the **Adapter Pattern** to support different database export formats:

- **Interface**: Implicit contract via `parse() -> SchemaModel` method
- **Concrete Adapter**: `ToadDdlParser` (currently the only implementation)
- **Extensibility**: New parsers (e.g., MySQL, PostgreSQL) can be added without modifying core logic

#### Single Responsibility
Each module has a focused purpose:

- **CLI**: User interaction and output formatting
- **Parser**: DDL parsing and extraction logic
- **Models**: Data structures and validation

---

## Module Reference

### Entry Points

#### `__init__.py`
```python
__version__ = "0.1.0"
```
Defines package version for introspection.

#### `__main__.py`
```python
from .cli import main
main()
```
Enables execution via `python -m database_insight`.

#### CLI Script (pyproject.toml)
```toml
[tool.poetry.scripts]
database-insight = "database_insight.cli:main"
```
Registers the `database-insight` command-line tool.

---

### CLI Layer (`cli.py`)

**Responsibilities:**
- Command-line interface definition
- User input validation
- Output formatting (tables, summaries)
- JSON export

**Key Components:**

```python
app = typer.Typer(help="Database schema analysis tool")
console = Console()  # Rich console for formatted output
```

**Commands:**

| Command | Purpose | Signature |
|---------|---------|-----------|
| `analyze` | Main analysis with summary and JSON export | `(input_file: Path, output: Path?)` |
| `tables` | List all tables with counts | `(input_file: Path)` |
| `describe` | Detailed table view with constraints | `(input_file: Path, table_name: str)` |
| `views` | List all views | `(input_file: Path)` |
| `describe_view` | Show view columns and SELECT | `(input_file: Path, view_name: str)` |
| `procedures` | List procedures, optionally filtered | `(input_file: Path, refcursor_only: bool)` |
| `describe_procedure` | Show procedure parameters | `(input_file: Path, procedure_name: str)` |

**Output Features:**
- Color-coded messages (green=success, red=error, blue=info)
- Rich tables with alignment and formatting
- Summary statistics (table count, FK count, etc.)
- Constraint visualization in `describe` command

---

### Adapter Layer (`adapters/toad_parser.py`)

**Class:** `ToadDdlParser`

**Responsibilities:**
- Parse Toad DDL SQL files
- Extract metadata, tables, views, procedures, constraints
- Apply comments to schema objects
- Return structured `SchemaModel`

**Constructor:**
```python
def __init__(self, file_path: Path):
    self.file_path = file_path
    self.content = file_path.read_text(encoding='utf-8')
```
Loads entire file into memory for regex processing.

**Main Method:**
```python
def parse(self) -> SchemaModel
```
Orchestrates all parsing steps and assembles the final schema model.

**Private Parsing Methods:**

| Method | Returns | Purpose |
|--------|---------|---------|
| `_parse_metadata()` | `dict` | Extract database version and schema name from header |
| `_parse_tables()` | `list[Table]` | Parse CREATE TABLE statements |
| `_parse_columns()` | `list[Column]` | Parse column definitions within a table |
| `_parse_table_comments()` | `dict[str, str]` | Extract COMMENT ON TABLE statements |
| `_parse_column_comments()` | `dict[str, dict[str, str]]` | Extract COMMENT ON COLUMN statements |
| `_parse_views()` | `list[View]` | Parse CREATE OR REPLACE FORCE VIEW |
| `_parse_procedures()` | `list[Procedure]` | Extract procedures from packages |
| `_parse_procedure_parameters()` | `list[ProcedureParameter]` | Parse parameter lists |
| `_parse_primary_keys()` | `dict[str, PrimaryKey]` | Extract ALTER TABLE PRIMARY KEY |
| `_parse_foreign_keys()` | `dict[str, list[ForeignKey]]` | Extract ALTER TABLE FOREIGN KEY |

---

### Data Model Layer (`models/schema.py`)

All models extend **Pydantic's BaseModel** for validation and JSON serialization.

#### `Column`
Represents a table column.

```python
class Column(BaseModel):
    name: str
    data_type: str                    # VARCHAR2, NUMBER, DATE, etc.
    nullable: bool = True
    max_length: int | None = None     # For VARCHAR2, CHAR
    precision: int | None = None      # For NUMBER
    scale: int | None = None          # For NUMBER
    default_value: str | None = None
    comment: str | None = None
```

**Oracle Type Mapping:**
- `VARCHAR2(n)` → `data_type="VARCHAR2"`, `max_length=n`
- `NUMBER(p,s)` → `data_type="NUMBER"`, `precision=p`, `scale=s`
- `DATE` → `data_type="DATE"` (no size attributes)

#### `PrimaryKey`
Represents a primary key constraint.

```python
class PrimaryKey(BaseModel):
    constraint_name: str    # e.g., "PK_ADMCOREINFO"
    columns: list[str]      # e.g., ["COREID"]
```

#### `ForeignKey`
Represents a foreign key relationship.

```python
class ForeignKey(BaseModel):
    constraint_name: str           # e.g., "FK_ADMCOREINFO_01"
    columns: list[str]             # Local columns
    referenced_table: str          # Target table
    referenced_columns: list[str]  # Target columns
```

#### `Table`
Represents a database table.

```python
class Table(BaseModel):
    name: str
    schema_name: str
    columns: list[Column]
    row_count: int = 0
    comment: str | None = None
    primary_key: PrimaryKey | None = None
    foreign_keys: list[ForeignKey] = []
```

#### `View`
Represents a database view.

```python
class View(BaseModel):
    name: str
    schema_name: str
    columns: list[str]          # Column names only
    select_statement: str       # Full SELECT query
    comment: str | None = None
```

#### `ProcedureParameter`
Represents a procedure parameter.

```python
class ProcedureParameter(BaseModel):
    name: str
    direction: str   # "IN", "OUT", "IN OUT"
    data_type: str   # VARCHAR2, NUMBER, ref_cursor, etc.
```

#### `Procedure`
Represents a stored procedure.

```python
class Procedure(BaseModel):
    name: str
    package_name: str
    schema_name: str
    parameters: list[ProcedureParameter]
    has_refcursor_out: bool = False  # Flagged for API generation
```

**REF CURSOR Detection:**
Automatically detects OUT/IN OUT parameters containing "REF" and "CURSOR" in the type.

#### `SchemaModel`
Top-level schema container.

```python
class SchemaModel(BaseModel):
    database_type: str              # "oracle"
    database_version: str | None    # e.g., "19.0.0.0.0"
    schema_name: str
    extracted_at: datetime
    tables: list[Table]
    views: list[View] = []
    procedures: list[Procedure] = []
```

**JSON Serialization:**
```python
schema.model_dump_json(indent=2)
```
Produces clean JSON with ISO datetime formatting.

---

## Parsing Strategy

### Regex-Based Approach

The parser uses **compiled regex patterns** with the `re.DOTALL` and `re.IGNORECASE` flags for multi-line matching.

#### Why Regex?
- **Performance**: Single-pass parsing for large files (45K+ lines)
- **Simplicity**: No grammar dependencies (ANTLR, PLY, etc.)
- **Targeted**: Extracts only needed information
- **Tolerant**: Handles malformed DDL gracefully

#### Trade-offs
- **Brittleness**: Requires exact pattern matching
- **Maintenance**: Complex patterns are hard to debug
- **Edge Cases**: May miss unusual formatting

### Parsing Workflow

```
1. Load entire file into memory
2. Extract metadata (header comments)
3. Parse tables (CREATE TABLE)
   ├── Extract columns
   ├── Determine row counts
   └── Infer schema if missing
4. Parse views (CREATE VIEW)
5. Parse procedures (from packages)
6. Parse constraints (ALTER TABLE)
7. Apply comments to objects
8. Apply constraints to tables
9. Return SchemaModel
```

### Key Regex Patterns

#### Table Parsing
```python
r'CREATE TABLE\s+(?:(\w+)\.)?(\w+)\s*\(\s*\n(.*?)\n\)\s*\n(?:TABLESPACE|;)'
```
- `(?:(\w+)\.)?` - Optional schema prefix
- `(\w+)` - Table name (captured)
- `(.*?)` - Column block (captured, non-greedy)
- Stops at `TABLESPACE` or `;`

#### Column Parsing
```python
r'^\s*(\w+)\s+' +  # Column name
r'(VARCHAR2|NUMBER|DATE|...)' +  # Data type
r'(?:\((\d+)(?:\s*BYTE)?(?:,(\d+))?\))?' +  # Optional size
r'([^,\n]*)'  # Rest of definition
```

#### Primary Key Parsing
```python
r'ALTER\s+TABLE\s+(\w+)\s+ADD\s+\(\s*\n' +
r'\s*CONSTRAINT\s+(\w+)\s*\n' +
r'\s*PRIMARY\s+KEY\s*\n' +
r'\s*\((.*?)\)'
```

#### Foreign Key Parsing
```python
r'ALTER\s+TABLE\s+(\w+)\s+ADD\s+\(\s*\n' +
r'\s*CONSTRAINT\s+(\w+)\s*\n' +
r'\s*FOREIGN\s+KEY\s+\((.*?)\)\s*\n' +
r'\s*REFERENCES\s+(\w+)\s+\((.*?)\)'
```

### Row Count Extraction

Toad exports include row counts in comments:
```sql
--   Row Count: 1416
CREATE TABLE ADMCOREINFO
```

**Strategy:**
```python
start_pos = max(0, match.start() - 200)
preceding_text = self.content[start_pos:match.start()]
row_match = re.search(r'--\s+Row Count:\s*(\d+)', preceding_text)
```
Searches 200 characters before CREATE TABLE to find the row count.

### Comment Handling

Oracle uses doubled single-quotes for escaping:
```sql
COMMENT ON COLUMN IMAS.MOLDS.PART_TYPE_CD IS 'Mold''s part type';
```

**Replacement:**
```python
comment.replace("''", "'")  # Convert to: Mold's part type
```

---

## Data Flow

### Parse Flow

```
Input: IMAS.sql (Toad export)
  ↓
ToadDdlParser.__init__()
  ↓ [Load file to memory]
ToadDdlParser.parse()
  ↓
[Parallel Parsing Steps]
├── _parse_metadata()
├── _parse_tables()
│   └── _parse_columns()
├── _parse_views()
├── _parse_procedures()
│   └── _parse_procedure_parameters()
├── _parse_primary_keys()
└── _parse_foreign_keys()
  ↓
[Assembly Phase]
├── Apply comments to tables/columns
├── Apply constraints to tables
└── Build SchemaModel
  ↓
Output: SchemaModel instance
  ↓
[CLI Layer]
├── Display summary
├── Generate Rich tables
└── Export JSON (optional)
```

### JSON Export Flow

```
SchemaModel
  ↓
.model_dump_json(indent=2)
  ↓ [Pydantic serialization]
JSON String
  ↓
Path.write_text()
  ↓
schema.json (for API Forge)
```

**Example Output:**
```json
{
  "database_type": "oracle",
  "database_version": "19.0.0.0.0",
  "schema_name": "IMAS",
  "extracted_at": "2025-11-28T17:07:29.452047",
  "tables": [
    {
      "name": "ADMCOREINFO",
      "schema_name": "IMAS",
      "columns": [...],
      "row_count": 1416,
      "primary_key": {
        "constraint_name": "PK_ADMCOREINFO",
        "columns": ["COREID"]
      },
      "foreign_keys": [
        {
          "constraint_name": "FK_ADMCOREINFO_01",
          "columns": ["CORENAME_FORMAT"],
          "referenced_table": "ADMCORENAMEFORMAT",
          "referenced_columns": ["CORENAMEFORMATID"]
        }
      ]
    }
  ],
  "views": [...],
  "procedures": [...]
}
```

---

## CLI Commands

### `analyze`

**Usage:**
```bash
database-insight analyze IMAS.sql [--output schema.json]
```

**Output:**
- Schema summary (name, version, counts)
- Constraint statistics
- Top 10 tables by row count
- Optional JSON export

**Example:**
```
Schema: IMAS
Database: Oracle 19.0.0.0.0
Tables: 97
Views: 71
Procedures: 206
Columns: 780
Primary Keys: 73
Foreign Keys: 28
Procedures with REF CURSOR OUT: 69

Top 10 Tables by Row Count:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Table                    ┃       Rows ┃ Columns ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━┩
│ HISTORY_IMAS_SUB_READING │ 52,352,818 │      10 │
...
```

### `tables`

**Usage:**
```bash
database-insight tables IMAS.sql
```

**Output:**
```
ADMCOREINFO (16 cols, 1,416 rows)
ADMCORENAMEFORMAT (2 cols, 2 rows)
...
```

### `describe`

**Usage:**
```bash
database-insight describe IMAS.sql ADMCOREINFO
```

**Output:**
- Table name and schema
- Row count
- Primary key columns
- Foreign key relationships
- Column table with types, nullability, defaults, and key markers

**Example:**
```
IMAS.ADMCOREINFO
Rows: 1,416
Primary Key: COREID
Foreign Keys: 1
  CORENAME_FORMAT → ADMCORENAMEFORMAT(CORENAMEFORMATID)

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┳━━━━━┓
┃ Column             ┃ Type         ┃ Nullable ┃ Default ┃ Key ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━╇━━━━━┩
│ COREID             │ NUMBER       │ N        │         │ PK  │
│ CORENAME           │ VARCHAR2(30) │ Y        │         │     │
...
```

### `views`

**Usage:**
```bash
database-insight views IMAS.sql
```

**Output:**
```
V_AUDIT_ROUTES (10 cols)
V_BLOCK_LINKS (14 cols)
...
```

### `describe_view`

**Usage:**
```bash
database-insight describe-view IMAS.sql V_AUDIT_ROUTES
```

**Output:**
- View name
- Column list
- Full SELECT statement

### `procedures`

**Usage:**
```bash
database-insight procedures IMAS.sql [--refcursor]
```

**Options:**
- `--refcursor` / `-r`: Filter to procedures with REF CURSOR OUT parameters

**Output:**
```
PKG_BLOCKS.GET_BLOCK_LINES [RC] (1 params)
PACKAGE_IMAS.FIND_COMPLETED_LOTS_GEN_LINE (3 params)
...
```

### `describe_procedure`

**Usage:**
```bash
database-insight describe-procedure IMAS.sql PKG_BLOCKS.GET_BLOCK_LINES
```

**Output:**
- Procedure name (package.procedure)
- REF CURSOR flag (if applicable)
- Parameter table with name, direction, type

---

## Extension Points

### Adding New Database Parsers

To support exports from other tools (MySQL Workbench, pgAdmin, etc.):

1. **Create new parser class** in `adapters/`:
   ```python
   class MySqlWorkbenchParser:
       def __init__(self, file_path: Path):
           self.file_path = file_path
           self.content = file_path.read_text()

       def parse(self) -> SchemaModel:
           # Implement MySQL-specific parsing
           ...
   ```

2. **Update CLI** to accept a `--format` option:
   ```python
   @app.command()
   def analyze(
       input_file: Path,
       format: str = typer.Option("toad", help="Parser format"),
       ...
   ):
       if format == "toad":
           parser = ToadDdlParser(input_file)
       elif format == "mysql":
           parser = MySqlWorkbenchParser(input_file)
       ...
   ```

3. **Register in adapters/__init__.py**:
   ```python
   from .toad_parser import ToadDdlParser
   from .mysql_parser import MySqlWorkbenchParser
   ```

### Adding New Schema Elements

To parse triggers, sequences, or other objects:

1. **Add model** to `models/schema.py`:
   ```python
   class Trigger(BaseModel):
       name: str
       table_name: str
       timing: str  # BEFORE, AFTER
       event: str   # INSERT, UPDATE, DELETE
       body: str
   ```

2. **Update SchemaModel**:
   ```python
   class SchemaModel(BaseModel):
       ...
       triggers: list[Trigger] = []
   ```

3. **Add parser method** to `ToadDdlParser`:
   ```python
   def _parse_triggers(self) -> list[Trigger]:
       # Regex pattern for CREATE TRIGGER
       ...
   ```

4. **Call in parse()**:
   ```python
   def parse(self) -> SchemaModel:
       ...
       triggers = self._parse_triggers()
       ...
       return SchemaModel(..., triggers=triggers)
   ```

5. **Add CLI command** in `cli.py`:
   ```python
   @app.command()
   def triggers(input_file: Path):
       parser = ToadDdlParser(input_file)
       schema = parser.parse()
       for t in schema.triggers:
           console.print(f"{t.name} on {t.table_name}")
   ```

### Enhancing Constraint Parsing

Current implementation supports PK and FK. To add UNIQUE, CHECK, etc.:

```python
class UniqueConstraint(BaseModel):
    constraint_name: str
    columns: list[str]

class CheckConstraint(BaseModel):
    constraint_name: str
    condition: str

class Table(BaseModel):
    ...
    unique_constraints: list[UniqueConstraint] = []
    check_constraints: list[CheckConstraint] = []
```

### Custom Output Formats

To generate formats beyond JSON (YAML, XML, GraphQL schema):

```python
@app.command()
def export_graphql(input_file: Path, output: Path):
    parser = ToadDdlParser(input_file)
    schema = parser.parse()

    # Generate GraphQL type definitions
    graphql_schema = generate_graphql_schema(schema)
    output.write_text(graphql_schema)
```

---

## Performance Considerations

### Memory Usage
- **Current**: Loads entire file into memory (~2MB for IMAS.sql with 45K lines)
- **Trade-off**: Fast regex operations vs. memory overhead
- **Scalability**: Suitable for files up to ~100MB

### Parse Time
- **Typical**: 1-2 seconds for 45K line file
- **Bottleneck**: Regex compilation and pattern matching
- **Optimization**: Pre-compiled patterns (already implemented)

### Recommended Optimizations (Future)
1. **Streaming Parser**: Process file line-by-line for large exports
2. **Parallel Parsing**: Multi-thread table/view/procedure parsing
3. **Caching**: Store parsed results for repeated operations

---

## Dependencies

### Production
- **pydantic** (2.12.5+): Data validation, serialization
- **typer** (0.20.0+): CLI framework with type annotations
- **rich** (14.2.0+): Terminal formatting and tables

### Development
- **pytest** (9.0.1+): Unit testing framework
- **poetry**: Dependency management and packaging

### Python Version
- **Requires**: Python 3.11+
- **Reason**: Uses `X | None` type union syntax

---

## Testing Strategy

### Current Coverage
- Manual testing against IMAS.sql
- Verified parsing of 97 tables, 71 views, 206 procedures

### Recommended Tests
1. **Unit Tests**:
   - Individual parsing methods (`_parse_tables`, `_parse_columns`, etc.)
   - Edge cases (empty files, malformed DDL)
   - Comment escaping

2. **Integration Tests**:
   - Full parse flow on sample files
   - JSON serialization/deserialization
   - CLI command execution

3. **Regression Tests**:
   - Parse known schemas and compare output
   - Validate constraint counts

---

## Future Enhancements

### Planned Features
1. **Materialized Views**: Parse CREATE MATERIALIZED VIEW
2. **Triggers**: Extract CREATE TRIGGER statements
3. **Sequences**: Parse CREATE SEQUENCE
4. **Indexes**: Parse CREATE INDEX (currently inferred from constraints)
5. **Column-level Constraints**: Extract CHECK, DEFAULT constraints inline

### API Forge Integration
Output schema JSON includes:
- **Primary Keys** → Unique record endpoints (`/cores/{id}`)
- **Foreign Keys** → Relationship endpoints (`/cores/{id}/attributes`)
- **Procedures with REF CURSOR** → Query endpoints (`/queries/completed-lots`)
- **Views** → Read-only endpoints (`/views/audit-routes`)

### Performance Improvements
- Incremental parsing (only changed tables)
- Diff mode (compare two schema versions)
- Index on table names for faster lookups

---

## Troubleshooting

### Common Issues

**Problem**: Parser finds 0 tables
**Cause**: CREATE TABLE pattern doesn't match
**Solution**: Check if tables have schema prefix (`IMAS.TABLE` vs `TABLE`)

**Problem**: Row counts all show 0
**Cause**: Row count comment missing or in wrong position
**Solution**: Ensure `-- Row Count: N` appears within 200 chars before CREATE TABLE

**Problem**: Foreign keys not detected
**Cause**: ALTER TABLE format differs
**Solution**: Verify constraint uses format:
```sql
ALTER TABLE X ADD (
  CONSTRAINT FK_NAME
  FOREIGN KEY (col)
  REFERENCES Y (col)
  ENABLE VALIDATE);
```

**Problem**: Procedures missing parameters
**Cause**: Multi-line parameter format not parsed correctly
**Solution**: Check that parameters are comma-separated

---

## Conclusion

Database Insight provides a robust, extensible foundation for parsing Oracle DDL exports. Its layered architecture, Pydantic-based models, and adapter pattern make it easy to extend for new databases or schema elements.

For questions or contributions, see the project repository.
