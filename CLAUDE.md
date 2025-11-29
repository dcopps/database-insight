# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Database Insight is a Python CLI tool that parses and analyzes Oracle database schema exports from Toad. It converts Toad DDL SQL files into structured data models and provides commands to explore schema information.

## Development Commands

### Setup
```bash
# Install dependencies using Poetry
poetry install

# Activate virtual environment
poetry shell
```

### Running the CLI
```bash
# Run via Poetry
poetry run database-insight analyze IMAS.sql

# Or after activating shell
database-insight analyze IMAS.sql

# Or via Python module
python -m database_insight analyze IMAS.sql
```

### Testing
```bash
# Run tests with pytest
poetry run pytest

# Run specific test file
poetry run pytest tests/test_file.py
```

## Architecture

### Core Components

**Adapter Pattern**: The codebase uses an adapter pattern to support different database export formats. Currently implements:
- `ToadDdlParser` (adapters/toad_parser.py) - Parses Toad "Create Schema Script" exports

**Data Models** (models/schema.py):
- `SchemaModel` - Top-level container (database_type, version, schema_name, tables)
- `Table` - Represents database tables with columns and metadata
- `Column` - Column definitions with type, constraints, defaults

All models use Pydantic for validation and serialization.

### Parsing Strategy

The `ToadDdlParser` uses regex-based parsing in stages:
1. `_parse_metadata()` - Extracts header comments (version, schema name)
2. `_parse_tables()` - Matches CREATE TABLE blocks, extracts row counts from comments
3. `_parse_columns()` - Parses column definitions within each table
4. `_parse_table_comments()` / `_parse_column_comments()` - Matches COMMENT ON statements
5. Comments are then applied to their respective tables/columns

### CLI Commands

The CLI (cli.py) uses Typer and Rich for a polished terminal experience:
- `analyze` - Main command: parses file, displays summary table, optionally exports JSON
- `tables` - Lists all tables with column/row counts
- `describe <table_name>` - Shows detailed column information for a table

All commands parse the entire DDL file fresh on each invocation.

### Adding Support for New Export Formats

To add a new database export parser:
1. Create new parser class in `adapters/` directory (e.g., `mysql_parser.py`)
2. Implement `parse()` method that returns a `SchemaModel`
3. Import and use in CLI commands alongside `ToadDdlParser`
4. Consider adding a `--format` option to commands to select parser

### Key Design Notes

- Column type parsing handles Oracle-specific types (VARCHAR2, NUMBER, CLOB, SYS.XMLTYPE, etc.)
- Row counts are extracted from Toad's comment format: `-- Row Count: <number>`
- Comments use Oracle's escaped single-quote format (`''` for literal `'`)
- The parser is tolerant of missing metadata - defaults to "UNKNOWN" schema, 0 row counts

## Project Context

Database Insight is the first tool in a 4-tool Strangler Fig modernization framework:

1. **Database Insight** (this tool) → Parses schema, outputs JSON
2. **API Forge** → Consumes schema JSON, generates .NET Core REST APIs
3. **UI Forge** → Consumes OpenAPI spec, generates HTML/JS UI
4. **Logic Mapper** → Analyzes legacy code (ASP/VBScript, PL/SQL)

Target market: FDA-regulated manufacturing (pharma, medical devices).

## Output Requirements

Database Insight must output a SchemaModel JSON that API Forge can consume:
- Tables with columns, types, PKs, FKs
- Relationships for generating endpoints
- Comments for API documentation
- Row counts for pagination hints

See docs/ folder for detailed technical designs.
