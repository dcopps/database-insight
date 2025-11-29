# Database Insight User Guide

**Version:** 0.1.0 (MVP)  
**Purpose:** Analyse Oracle database schemas from Toad DDL exports

---

## Overview

Database Insight parses Toad "Create Schema Script" exports and extracts schema metadata for documentation and downstream tooling (API generation, migration planning).

### What it extracts

| Object | Status | Notes |
|--------|--------|-------|
| Tables | ✅ | Columns, types, defaults, nullability |
| Row counts | ✅ | From Toad comments |
| Table/column comments | ✅ | Documentation |
| Primary keys | 🔜 | From ALTER TABLE statements |
| Foreign keys | 🔜 | From ALTER TABLE statements |
| Views | 🔜 | Planned |
| Stored procedures | 🔜 | Planned |

---

## Installation

### Prerequisites

- Python 3.11 or later
- Poetry (Python package manager)

### Install Python (macOS)

```bash
brew install python@3.11
```

### Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3.11 -
```

Add to your PATH (add to `~/.zshrc`):
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Install Database Insight

```bash
cd ~/code/database-insight
poetry install
```

---

## Creating a Toad Export

In Toad for Oracle:

1. **Schema Browser** → Right-click schema → **Export** → **Create Schema Script**

2. **Include these objects:**
   - ✅ Tables
   - ✅ Primary key constraints
   - ✅ Foreign key constraints  
   - ✅ Unique constraints
   - ✅ Comments (table and column)
   - ✅ Views
   - ✅ Packages and package bodies
   - ✅ Triggers
   - ✅ Sequences

3. **Exclude:**
   - ❌ MLOG$ tables (materialized view logs)
   - ❌ RUPD$ tables (replication tables)
   - ❌ Grants/permissions
   - ❌ Storage clauses (optional - adds noise)

4. **Save as:** `SCHEMANAME.sql`

---

## Commands

### Analyze Schema

Summary of the schema with top tables by row count:

```bash
poetry run database-insight analyze IMAS.sql
```

**Output:**
```
Parsing IMAS.sql...

Schema: IMAS
Database: Oracle 19.0.0.0.0
Tables: 96
Columns: 774

Top 10 Tables by Row Count:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Table                         ┃       Rows ┃ Columns ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━┩
│ HISTORY_IMAS_SUB_READING      │ 52,352,818 │      10 │
│ IMAS_SUB_READING              │ 52,239,512 │       7 │
│ ...                           │        ... │     ... │
└───────────────────────────────┴────────────┴─────────┘
```

### Export to JSON

For use with API Forge or other downstream tools:

```bash
poetry run database-insight analyze IMAS.sql --output schema.json
```

### List All Tables

```bash
poetry run database-insight tables IMAS.sql
```

**Output:**
```
ADMCOREINFO (16 cols, 1,416 rows)
ADMCORENAMEFORMAT (2 cols, 12 rows)
MOLDS (23 cols, 67,717 rows)
...
```

### Describe a Table

Detailed column information for a specific table:

```bash
poetry run database-insight describe IMAS.sql MOLDS
```

**Output:**
```
IMAS.MOLDS
Rows: 67,717

┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┓
┃ Column           ┃ Type          ┃ Nullable ┃ Default ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━┩
│ MOLD_ID          │ NUMBER        │ Y        │         │
│ CAPTURE_DATETIME │ DATE          │ Y        │ SYSDATE │
│ MOLD_NUM         │ VARCHAR2(20)  │ Y        │         │
│ NUM_CAVITIES     │ NUMBER(2)     │ Y        │         │
│ ...              │ ...           │ ...      │ ...     │
└──────────────────┴───────────────┴──────────┴─────────┘
```

---

## JSON Output Format

The `--output` option produces a JSON file structured for API Forge:

```json
{
  "database_type": "oracle",
  "database_version": "19.0.0.0.0",
  "schema_name": "IMAS",
  "extracted_at": "2024-11-28T10:30:00",
  "tables": [
    {
      "name": "MOLDS",
      "schema_name": "IMAS",
      "row_count": 67717,
      "comment": "Master table for injection molds",
      "columns": [
        {
          "name": "MOLD_ID",
          "data_type": "NUMBER",
          "nullable": true,
          "precision": null,
          "scale": null,
          "max_length": null,
          "default_value": null,
          "comment": "Primary key"
        },
        {
          "name": "MOLD_NUM",
          "data_type": "VARCHAR2",
          "nullable": true,
          "max_length": 20,
          "comment": "Mold identifier"
        }
      ],
      "primary_key": {
        "name": "PK_MOLDS",
        "columns": ["MOLD_ID"]
      },
      "foreign_keys": [
        {
          "name": "FK_MOLDS_STATUS",
          "columns": ["STATUSID"],
          "referenced_table": "ADMSTATUS",
          "referenced_columns": ["STATUSID"]
        }
      ]
    }
  ]
}
```

---

## Downstream Usage

### API Forge

Database Insight output feeds directly into API Forge to generate REST APIs:

```bash
# Step 1: Extract schema
poetry run database-insight analyze IMAS.sql --output schema.json

# Step 2: Generate API (future)
api-forge generate schema.json --output ./api-project
```

### What API Forge generates from this:

| Schema Element | API Output |
|----------------|------------|
| Table MOLDS | `GET/POST/PUT/DELETE /api/molds` |
| Primary key MOLD_ID | `GET /api/molds/{id}` |
| Foreign key to ADMSTATUS | `GET /api/molds/{id}/status` |
| Row count 67,717 | Pagination enabled by default |
| Column comments | OpenAPI descriptions |

---

## Troubleshooting

### "Table not found" error

Table names are case-sensitive. Try uppercase:
```bash
poetry run database-insight describe IMAS.sql MOLDS
# not: molds
```

### Low table count

If you see fewer tables than expected, check for:
- MLOG$ / RUPD$ tables in Toad export (system tables, no DDL)
- Tables in different schemas not included in export

### Row counts all the same

Ensure your Toad export includes row count comments:
```sql
--   Row Count: 67717
CREATE TABLE IMAS.MOLDS
```

If missing, re-export with "Include row counts" option.

### Memory issues

If Claude Code is slow or unresponsive:
```bash
# Exit and restart
/exit
claude --resume
```

---

## Roadmap

### Current (v0.1)
- ✅ Parse tables and columns
- ✅ Extract row counts
- ✅ Extract comments
- ✅ JSON export

### Next (v0.2)
- 🔜 Primary key parsing
- 🔜 Foreign key parsing
- 🔜 View extraction

### Future (v0.3+)
- Stored procedure analysis
- Trigger documentation
- HTML report generation
- Audit gap analysis (FDA 21 CFR Part 11)

---

## Support

This tool is part of the Legacy Database Modernisation Framework for FDA-regulated manufacturing environments.

For issues or questions, contact the development team.
