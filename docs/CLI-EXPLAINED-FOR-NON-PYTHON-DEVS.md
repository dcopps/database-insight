# Understanding cli.py: A Guide for Non-Python Developers

This document explains how the `database_insight/cli.py` file works, assuming you're an experienced software engineer but new to Python.

## Table of Contents
1. [Python Basics You Need to Know](#python-basics-you-need-to-know)
2. [Import System](#import-system)
3. [The Typer Framework](#the-typer-framework)
4. [How Commands Work](#how-commands-work)
5. [Type Hints and Function Signatures](#type-hints-and-function-signatures)
6. [Python-Specific Syntax](#python-specific-syntax)
7. [Command-by-Command Walkthrough](#command-by-command-walkthrough)

---

## Python Basics You Need to Know

### 1. No Semicolons, Indentation Matters
Python uses indentation (4 spaces) to define code blocks instead of curly braces:

```python
# Instead of C#/Java style:
# if (condition) {
#     doSomething();
# }

# Python style:
if condition:
    do_something()
```

### 2. Everything is an Object
Functions are first-class objects. You can pass them around, decorate them, and assign them to variables.

### 3. Dynamic Typing with Optional Type Hints
Python is dynamically typed, but modern Python uses type hints for better tooling:

```python
# Type hints are optional but recommended
def greet(name: str) -> str:
    return f"Hello, {name}"
```

### 4. No `new` Keyword
Create objects by calling the class directly:

```python
# Instead of: Parser parser = new Parser();
parser = ToadDdlParser(input_file)
```

### 5. String Formatting
Python has multiple ways to format strings:

```python
# f-strings (modern, preferred)
console.print(f"Tables: {len(schema.tables)}")

# Equivalent to C#'s string interpolation:
# Console.WriteLine($"Tables: {schema.Tables.Count}");
```

---

## Import System

At the top of `cli.py`, we import dependencies:

```python
import typer                          # Third-party CLI framework
from pathlib import Path              # Standard library for file paths
from rich.console import Console      # Third-party for colored terminal output
from rich.table import Table as RichTable  # Import with alias to avoid naming conflict

from .adapters.toad_parser import ToadDdlParser  # Relative import from our package
```

### Import Syntax Explained

| Syntax | Meaning | Equivalent to |
|--------|---------|---------------|
| `import typer` | Import entire module | `using Typer;` (C#) |
| `from pathlib import Path` | Import specific class | `using Path = System.IO.Path;` |
| `from rich.table import Table as RichTable` | Import with alias | `using RichTable = Rich.Table;` |
| `from .adapters.toad_parser import ...` | Relative import (`.` = current package) | Internal project reference |

---

## The Typer Framework

Typer is a CLI framework that uses Python decorators to convert functions into CLI commands.

### Setup (Lines 8-9)

```python
app = typer.Typer(help="Database schema analysis tool")
console = Console()
```

- `app` is the CLI application instance
- `console` is a Rich console for formatted output
- These are **module-level variables** (like static fields in C#/Java)

### How Decorators Work

In Python, decorators modify or enhance functions. The `@app.command()` decorator registers a function as a CLI command:

```python
@app.command()
def analyze(input_file: Path, output: Path = None):
    """Analyze a Toad DDL export file."""
    # Function body
```

**What this does:**
1. The `@app.command()` decorator tells Typer: "This function is a CLI command"
2. Typer automatically parses command-line arguments based on the function signature
3. When you run `dbi analyze file.sql`, Typer calls this function with `input_file=Path("file.sql")`

**Equivalent in other languages:**
- In C#, this is like using attributes: `[Command("analyze")]`
- In Java, similar to annotations: `@Command("analyze")`

---

## Type Hints and Function Signatures

### Understanding Function Parameters

```python
def analyze(
    input_file: Path = typer.Argument(..., help="Toad DDL export file (.sql)"),
    output: Path = typer.Option(None, "--output", "-o", help="Output JSON file"),
):
```

Let's break this down:

| Component | Meaning |
|-----------|---------|
| `input_file: Path` | Parameter named `input_file` with type hint `Path` |
| `= typer.Argument(...)` | Default value that tells Typer this is a **required positional argument** |
| `...` (Ellipsis) | Python's way of saying "required, no default value" |
| `output: Path` | Parameter named `output` with type hint `Path` |
| `= typer.Option(None, ...)` | This is an **optional flag** (`--output` or `-o`) |
| `None` | Default value if not provided |

**Command-line mapping:**
```bash
dbi analyze IMAS.sql --output schema.json
#           ↑               ↑
#      input_file        output
```

### Argument vs Option

| Type | Syntax | Required? | Example |
|------|--------|-----------|---------|
| `typer.Argument()` | Positional | Yes (if `...`) | `dbi analyze IMAS.sql` |
| `typer.Option()` | Named flag | No (if default provided) | `--output schema.json` |

---

## Python-Specific Syntax

### 1. List Comprehensions

Python has concise syntax for creating/filtering lists:

```python
# Line 34: Count all columns across all tables
total_columns = sum(len(t.columns) for t in schema.tables)
```

**Equivalent pseudo-code:**
```java
// Java-style equivalent
int totalColumns = schema.tables.stream()
    .mapToInt(t -> t.columns.size())
    .sum();
```

### 2. Generator Expressions with `sum()`

```python
# Line 38: Count tables that have primary keys
tables_with_pk = sum(1 for t in schema.tables if t.primary_key)
```

**Equivalent pseudo-code:**
```csharp
// C#-style equivalent
int tablesWithPk = schema.Tables.Count(t => t.PrimaryKey != null);
```

### 3. Lambda Functions

```python
# Line 54: Sort tables by row_count in descending order, take first 10
sorted_tables = sorted(schema.tables, key=lambda t: t.row_count, reverse=True)[:10]
```

| Component | Meaning |
|-----------|---------|
| `sorted(...)` | Built-in function to sort a list |
| `key=lambda t: t.row_count` | Sort by the `row_count` property |
| `lambda t: t.row_count` | Anonymous function (like `t => t.RowCount` in C#) |
| `reverse=True` | Sort descending |
| `[:10]` | Slice notation: take first 10 elements |

### 4. The `next()` Function

```python
# Line 85: Find first table matching the name (case-insensitive)
table = next((t for t in schema.tables if t.name.upper() == table_name.upper()), None)
```

**Breakdown:**
- `next(iterator, default)` returns the first item from an iterator, or `default` if empty
- `(t for t in schema.tables if ...)` is a generator expression (lazy evaluation)
- If no match found, returns `None`

**Equivalent to:**
```csharp
// C# LINQ equivalent
var table = schema.Tables.FirstOrDefault(t =>
    t.Name.ToUpper() == tableName.ToUpper());
```

### 5. String Formatting with f-strings

```python
# Line 56: Format number with thousands separator
table.add_row(t.name, f"{t.row_count:,}", str(len(t.columns)))
```

| Component | Meaning |
|-----------|---------|
| `f"..."` | f-string (formatted string literal) |
| `{t.row_count:,}` | Insert value with comma thousands separator (1000000 → 1,000,000) |
| `{t.name}` | Insert value as-is |

### 6. Conditional Expressions (Ternary Operator)

```python
# Line 131: Set key_marker to "PK" if in pk_columns, else ""
key_marker = "PK" if col.name in pk_columns else ""
```

**Equivalent to:**
```java
// Java-style ternary
String keyMarker = pkColumns.contains(col.name) ? "PK" : "";
```

### 7. The `or` Operator for Default Values

```python
# Line 137: Use default_value if not null/empty, otherwise use ""
col.default_value or ""
```

In Python, `or` returns the first truthy value:
- If `col.default_value` is `None` or `""` (falsy), return `""`
- Otherwise, return `col.default_value`

### 8. String Joining

```python
# Line 97: Join list of strings with ", "
pk_cols = ", ".join(table.primary_key.columns)
```

**Equivalent to:**
```csharp
// C# equivalent
string pkCols = string.Join(", ", table.PrimaryKey.Columns);
```

### 9. The `in` Operator

```python
# Line 200: Check if string contains character
if '.' in procedure_name:
```

**Equivalent to:**
```java
// Java equivalent
if (procedureName.contains(".")) {
```

### 10. Tuple Unpacking

```python
# Line 201: Split string and assign to two variables
pkg_name, proc_name = procedure_name.upper().split('.', 1)
```

**Breakdown:**
- `split('.', 1)` splits string on first occurrence of `.`, returns list with 2 elements
- `pkg_name, proc_name = [...]` unpacks list into two variables

---

## Command-by-Command Walkthrough

### Command 1: `analyze` (Lines 11-63)

**Purpose:** Parse SQL file, display summary, optionally export JSON

**Execution flow:**

1. **Validate input file exists** (Lines 18-20)
   ```python
   if not input_file.exists():
       console.print(f"[red]Error: File not found: {input_file}[/red]")
       raise typer.Exit(1)
   ```
   - `input_file.exists()` checks file existence (Path method)
   - `raise typer.Exit(1)` exits with error code 1 (like `System.exit(1)` in Java)

2. **Parse the SQL file** (Lines 24-25)
   ```python
   parser = ToadDdlParser(input_file)
   schema = parser.parse()
   ```

3. **Display summary statistics** (Lines 27-45)
   ```python
   console.print(f"\n[green]Schema: {schema.schema_name}[/green]")
   ```
   - `[green]...[/green]` is Rich markup for colored output
   - `\n` adds a newline

4. **Create and display table** (Lines 47-58)
   ```python
   table = RichTable()
   table.add_column("Table")
   table.add_column("Rows", justify="right")

   sorted_tables = sorted(schema.tables, key=lambda t: t.row_count, reverse=True)[:10]
   for t in sorted_tables:
       table.add_row(t.name, f"{t.row_count:,}", str(len(t.columns)))

   console.print(table)
   ```

5. **Optional JSON export** (Lines 60-63)
   ```python
   if output:
       output.write_text(schema.model_dump_json(indent=2))
       console.print(f"\n[green]Schema written to {output}[/green]")
   ```
   - `if output:` checks if output parameter was provided (truthy check)
   - `write_text()` is a Path method that writes string to file
   - `model_dump_json()` is a Pydantic method that serializes object to JSON

---

### Command 2: `tables` (Lines 65-74)

**Purpose:** List all tables with basic stats

```python
@app.command()
def tables(input_file: Path = typer.Argument(..., help="Toad DDL export file")):
    """List all tables in the schema."""
    parser = ToadDdlParser(input_file)
    schema = parser.parse()

    for t in sorted(schema.tables, key=lambda x: x.name):
        console.print(f"{t.name} ({len(t.columns)} cols, {t.row_count:,} rows)")
```

**Key points:**
- `sorted(schema.tables, key=lambda x: x.name)` sorts alphabetically by name
- Loop over sorted list and print each table

---

### Command 3: `describe` (Lines 76-141)

**Purpose:** Show detailed information about a specific table

**Notable sections:**

1. **Find table by name (case-insensitive)** (Line 85)
   ```python
   table = next((t for t in schema.tables if t.name.upper() == table_name.upper()), None)
   ```

2. **Handle not found** (Lines 86-88)
   ```python
   if not table:
       console.print(f"[red]Table not found: {table_name}[/red]")
       raise typer.Exit(1)
   ```

3. **Display constraints** (Lines 95-106)
   ```python
   if table.primary_key:
       pk_cols = ", ".join(table.primary_key.columns)
       console.print(f"[green]Primary Key:[/green] {pk_cols}")

   if table.foreign_keys:
       for fk in table.foreign_keys:
           fk_cols = ", ".join(fk.columns)
           ref_cols = ", ".join(fk.referenced_columns)
           console.print(f"  {fk_cols} → {fk.referenced_table}({ref_cols})")
   ```

4. **Build column table** (Lines 110-141)
   ```python
   rtable = RichTable()
   rtable.add_column("Column")
   rtable.add_column("Type")
   rtable.add_column("Nullable")
   rtable.add_column("Default")
   rtable.add_column("Key")

   pk_columns = set(table.primary_key.columns) if table.primary_key else set()

   for col in table.columns:
       # Build type string with length/precision
       type_str = col.data_type
       if col.max_length:
           type_str += f"({col.max_length})"
       elif col.precision:
           type_str += f"({col.precision}"
           if col.scale:
               type_str += f",{col.scale}"
           type_str += ")"

       key_marker = "PK" if col.name in pk_columns else ""

       rtable.add_row(
           col.name,
           type_str,
           "Y" if col.nullable else "N",
           col.default_value or "",
           key_marker
       )
   ```

**Key Python concepts:**
- `set()` creates a set for fast lookups
- `if/elif/else` chains (like switch statements)
- String concatenation with `+=`
- Conditional expression for nullable: `"Y" if col.nullable else "N"`

---

### Command 4: `views` (Lines 143-152)

Simple list of views, similar to `tables` command.

---

### Command 5: `procedures` (Lines 154-169)

**Purpose:** List procedures with optional filtering

```python
@app.command()
def procedures(
    input_file: Path = typer.Argument(..., help="Toad DDL export file"),
    refcursor_only: bool = typer.Option(False, "--refcursor", "-r", help="Show only procedures with REF CURSOR OUT"),
):
    parser = ToadDdlParser(input_file)
    schema = parser.parse()

    procs = schema.procedures
    if refcursor_only:
        procs = [p for p in procs if p.has_refcursor_out]

    for p in sorted(procs, key=lambda x: (x.package_name, x.name)):
        cursor_marker = " [RC]" if p.has_refcursor_out else ""
        console.print(f"{p.package_name}.{p.name}{cursor_marker} ({len(p.parameters)} params)")
```

**Key points:**
- `refcursor_only: bool = typer.Option(False, ...)` creates a boolean flag (default `False`)
- List comprehension for filtering: `[p for p in procs if p.has_refcursor_out]`
- Sort by tuple `(package_name, name)` for two-level sorting

---

### Command 6: `describe_view` (Lines 171-188)

Shows view details including column list and SELECT statement.

---

### Command 7: `describe_procedure` (Lines 190-224)

**Purpose:** Show procedure parameters

**Interesting logic - handling qualified names** (Lines 199-205):

```python
if '.' in procedure_name:
    pkg_name, proc_name = procedure_name.upper().split('.', 1)
    proc = next((p for p in schema.procedures
                if p.package_name.upper() == pkg_name and p.name.upper() == proc_name), None)
else:
    proc = next((p for p in schema.procedures if p.name.upper() == procedure_name.upper()), None)
```

**Explanation:**
- If user provides `PKG_NAME.PROC_NAME`, split and match both
- If user provides just `PROC_NAME`, match by name only
- `split('.', 1)` splits on first `.` only (max 2 parts)

---

### Entry Point (Lines 226-230)

```python
def main():
    app()

if __name__ == "__main__":
    main()
```

**Explanation:**
- `main()` function calls the Typer app
- `if __name__ == "__main__":` runs only if script is executed directly (not imported)
- This is the standard Python entry point pattern

**Equivalent to:**
```java
// Java equivalent
public static void main(String[] args) {
    app.run(args);
}
```

---

## How It All Connects

### When you run: `dbi analyze IMAS.sql -o schema.json`

1. **Python's entry point:** `if __name__ == "__main__":` triggers
2. **main() calls app():** This invokes the Typer application
3. **Typer parses arguments:**
   - Sees `analyze` → finds `@app.command()` decorated `analyze()` function
   - Sees `IMAS.sql` → maps to `input_file` parameter
   - Sees `-o schema.json` → maps to `output` parameter
4. **Typer calls:** `analyze(input_file=Path("IMAS.sql"), output=Path("schema.json"))`
5. **Function executes:** Parses SQL, displays output, writes JSON

### Configured in pyproject.toml

```toml
[tool.poetry.scripts]
dbi = "database_insight.cli:main"
```

This tells Poetry: "Create a `dbi` executable that calls the `main()` function in `database_insight.cli` module"

---

## Summary: Key Takeaways for Non-Python Developers

1. **Decorators** (`@app.command()`) are Python's way of adding metadata/behavior to functions
2. **Type hints** (`input_file: Path`) are optional but recommended for tooling
3. **List comprehensions** and **generator expressions** are concise ways to transform/filter collections
4. **f-strings** (`f"..."`) are the modern way to format strings
5. **Everything is an object** - no `new` keyword, no semicolons
6. **Indentation defines scope** - 4 spaces, not curly braces
7. **Truthiness** - `if output:` checks if value is truthy (not null/empty)
8. **Lambda functions** - `lambda x: x.name` is like `x => x.Name` in C#
9. **next() with generator** - efficient way to find first match
10. **Typer framework** - automatically converts function signatures into CLI interfaces

---

## Additional Resources

- [Official Python Tutorial](https://docs.python.org/3/tutorial/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Python for Java Developers](https://python-course.eu/java-python.php)
- [Python for C# Developers](https://code-maven.com/slides/python-programming/python-for-csharp-developers)
