import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table as RichTable

from .adapters.toad_parser import ToadDdlParser

app = typer.Typer(help="Database schema analysis tool")
console = Console()

@app.command()
def analyze(
    input_file: Path = typer.Argument(..., help="Toad DDL export file (.sql)"),
    output: Path = typer.Option(None, "--output", "-o", help="Output JSON file"),
):
    """Analyze a Toad DDL export file."""
    
    if not input_file.exists():
        console.print(f"[red]Error: File not found: {input_file}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[blue]Parsing {input_file.name}...[/blue]")
    
    parser = ToadDdlParser(input_file)
    schema = parser.parse()
    
    # Summary
    console.print(f"\n[green]Schema: {schema.schema_name}[/green]")
    console.print(f"Database: Oracle {schema.database_version or 'unknown'}")
    console.print(f"Tables: {len(schema.tables)}")
    console.print(f"Views: {len(schema.views)}")
    console.print(f"Procedures: {len(schema.procedures)}")

    total_columns = sum(len(t.columns) for t in schema.tables)
    console.print(f"Columns: {total_columns}")

    # Count constraints
    tables_with_pk = sum(1 for t in schema.tables if t.primary_key)
    total_fks = sum(len(t.foreign_keys) for t in schema.tables)
    console.print(f"Primary Keys: {tables_with_pk}")
    console.print(f"Foreign Keys: {total_fks}")

    # Count procedures with REF CURSOR OUT parameters
    refcursor_procs = sum(1 for p in schema.procedures if p.has_refcursor_out)
    console.print(f"Procedures with REF CURSOR OUT: {refcursor_procs}")
    
    # Top 10 tables by row count
    console.print("\n[bold]Top 10 Tables by Row Count:[/bold]")
    table = RichTable()
    table.add_column("Table")
    table.add_column("Rows", justify="right")
    table.add_column("Columns", justify="right")
    
    sorted_tables = sorted(schema.tables, key=lambda t: t.row_count, reverse=True)[:10]
    for t in sorted_tables:
        table.add_row(t.name, f"{t.row_count:,}", str(len(t.columns)))
    
    console.print(table)
    
    # Output JSON if requested
    if output:
        output.write_text(schema.model_dump_json(indent=2))
        console.print(f"\n[green]Schema written to {output}[/green]")

@app.command()
def tables(
    input_file: Path = typer.Argument(..., help="Toad DDL export file"),
):
    """List all tables in the schema."""
    parser = ToadDdlParser(input_file)
    schema = parser.parse()
    
    for t in sorted(schema.tables, key=lambda x: x.name):
        console.print(f"{t.name} ({len(t.columns)} cols, {t.row_count:,} rows)")

@app.command()
def describe(
    input_file: Path = typer.Argument(..., help="Toad DDL export file"),
    table_name: str = typer.Argument(..., help="Table name"),
):
    """Describe a specific table."""
    parser = ToadDdlParser(input_file)
    schema = parser.parse()

    table = next((t for t in schema.tables if t.name.upper() == table_name.upper()), None)
    if not table:
        console.print(f"[red]Table not found: {table_name}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]{table.schema_name}.{table.name}[/bold]")
    if table.comment:
        console.print(f"[dim]{table.comment}[/dim]")
    console.print(f"Rows: {table.row_count:,}")

    # Show primary key
    if table.primary_key:
        pk_cols = ", ".join(table.primary_key.columns)
        console.print(f"[green]Primary Key:[/green] {pk_cols}")

    # Show foreign keys
    if table.foreign_keys:
        console.print(f"[blue]Foreign Keys:[/blue] {len(table.foreign_keys)}")
        for fk in table.foreign_keys:
            fk_cols = ", ".join(fk.columns)
            ref_cols = ", ".join(fk.referenced_columns)
            console.print(f"  {fk_cols} → {fk.referenced_table}({ref_cols})")

    console.print()

    rtable = RichTable()
    rtable.add_column("Column")
    rtable.add_column("Type")
    rtable.add_column("Nullable")
    rtable.add_column("Default")
    rtable.add_column("Key")

    # Get primary key columns for marking
    pk_columns = set(table.primary_key.columns) if table.primary_key else set()

    for col in table.columns:
        type_str = col.data_type
        if col.max_length:
            type_str += f"({col.max_length})"
        elif col.precision:
            type_str += f"({col.precision}"
            if col.scale:
                type_str += f",{col.scale}"
            type_str += ")"

        # Mark if primary key
        key_marker = "PK" if col.name in pk_columns else ""

        rtable.add_row(
            col.name,
            type_str,
            "Y" if col.nullable else "N",
            col.default_value or "",
            key_marker
        )

    console.print(rtable)

@app.command()
def views(
    input_file: Path = typer.Argument(..., help="Toad DDL export file"),
):
    """List all views in the schema."""
    parser = ToadDdlParser(input_file)
    schema = parser.parse()

    for v in sorted(schema.views, key=lambda x: x.name):
        console.print(f"{v.name} ({len(v.columns)} cols)")

@app.command()
def procedures(
    input_file: Path = typer.Argument(..., help="Toad DDL export file"),
    refcursor_only: bool = typer.Option(False, "--refcursor", "-r", help="Show only procedures with REF CURSOR OUT"),
):
    """List all procedures in the schema."""
    parser = ToadDdlParser(input_file)
    schema = parser.parse()

    procs = schema.procedures
    if refcursor_only:
        procs = [p for p in procs if p.has_refcursor_out]

    for p in sorted(procs, key=lambda x: (x.package_name, x.name)):
        cursor_marker = " [RC]" if p.has_refcursor_out else ""
        console.print(f"{p.package_name}.{p.name}{cursor_marker} ({len(p.parameters)} params)")

@app.command()
def describe_view(
    input_file: Path = typer.Argument(..., help="Toad DDL export file"),
    view_name: str = typer.Argument(..., help="View name"),
):
    """Describe a specific view."""
    parser = ToadDdlParser(input_file)
    schema = parser.parse()

    view = next((v for v in schema.views if v.name.upper() == view_name.upper()), None)
    if not view:
        console.print(f"[red]View not found: {view_name}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]{view.schema_name}.{view.name}[/bold]")
    console.print(f"\n[dim]Columns:[/dim] {', '.join(view.columns)}")
    console.print(f"\n[dim]SELECT Statement:[/dim]")
    console.print(view.select_statement)

@app.command()
def describe_procedure(
    input_file: Path = typer.Argument(..., help="Toad DDL export file"),
    procedure_name: str = typer.Argument(..., help="Procedure name (Package.Procedure)"),
):
    """Describe a specific procedure."""
    parser = ToadDdlParser(input_file)
    schema = parser.parse()

    # Parse package.procedure format
    if '.' in procedure_name:
        pkg_name, proc_name = procedure_name.upper().split('.', 1)
        proc = next((p for p in schema.procedures
                    if p.package_name.upper() == pkg_name and p.name.upper() == proc_name), None)
    else:
        proc = next((p for p in schema.procedures if p.name.upper() == procedure_name.upper()), None)

    if not proc:
        console.print(f"[red]Procedure not found: {procedure_name}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]{proc.package_name}.{proc.name}[/bold]")
    if proc.has_refcursor_out:
        console.print("[green]Has REF CURSOR OUT parameter[/green]")

    console.print("\n[dim]Parameters:[/dim]")
    rtable = RichTable()
    rtable.add_column("Name")
    rtable.add_column("Direction")
    rtable.add_column("Type")

    for param in proc.parameters:
        rtable.add_row(param.name, param.direction, param.data_type)

    console.print(rtable)

def main():
    app()

if __name__ == "__main__":
    main()