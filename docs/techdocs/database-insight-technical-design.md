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
