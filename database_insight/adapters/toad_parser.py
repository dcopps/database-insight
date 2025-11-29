import re
from pathlib import Path
from datetime import datetime
from ..models.schema import SchemaModel, Table, Column, View, Procedure, ProcedureParameter, PrimaryKey, ForeignKey

class ToadDdlParser:
    """Parses Toad 'Create Schema Script' SQL exports."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content = file_path.read_text(encoding='utf-8')
    
    def parse(self) -> SchemaModel:
        """Parse the Toad DDL file and return SchemaModel."""
        metadata = self._parse_metadata()
        tables = self._parse_tables()
        table_comments = self._parse_table_comments()
        column_comments = self._parse_column_comments()
        views = self._parse_views()
        procedures = self._parse_procedures()
        primary_keys = self._parse_primary_keys()
        foreign_keys = self._parse_foreign_keys()

        # Apply comments and constraints to tables
        for table in tables:
            table.comment = table_comments.get(table.name)
            for col in table.columns:
                col.comment = column_comments.get(table.name, {}).get(col.name)

            # Apply primary key
            if table.name in primary_keys:
                table.primary_key = primary_keys[table.name]

            # Apply foreign keys
            if table.name in foreign_keys:
                table.foreign_keys = foreign_keys[table.name]

        return SchemaModel(
            database_type='oracle',
            database_version=metadata.get('database_version'),
            schema_name=metadata.get('schema_name', 'UNKNOWN'),
            extracted_at=datetime.now(),
            tables=tables,
            views=views,
            procedures=procedures
        )
    
    def _parse_metadata(self) -> dict:
        """Extract header metadata."""
        result = {}
        
        version_match = re.search(r'Database Version\s+:\s+(.+)', self.content)
        if version_match:
            result['database_version'] = version_match.group(1).strip()
        
        schema_match = re.search(r'--\s+Schema\s+:\s+(\w+)', self.content)
        if schema_match:
            result['schema_name'] = schema_match.group(1).strip()
        
        return result
    
    def _parse_tables(self) -> list[Table]:
        """Extract table definitions."""
        tables = []

        # Pattern to match CREATE TABLE blocks (with optional schema prefix)
        pattern = re.compile(
            r'CREATE TABLE\s+(?:(\w+)\.)?(\w+)\s*\(\s*\n(.*?)\n\)\s*\n(?:TABLESPACE|;)',
            re.DOTALL | re.IGNORECASE
        )

        # Get default schema from metadata
        metadata = self._parse_metadata()
        default_schema = metadata.get('schema_name', 'UNKNOWN')

        for match in pattern.finditer(self.content):
            schema_name, table_name, columns_block = match.groups()

            # Use default schema if not specified
            if not schema_name:
                schema_name = default_schema

            # Look for row count in preceding comment (within 200 chars before CREATE TABLE)
            row_count = 0
            start_pos = max(0, match.start() - 200)
            preceding_text = self.content[start_pos:match.start()]
            row_match = re.search(r'--\s+Row Count:\s*(\d+)', preceding_text)
            if row_match:
                row_count = int(row_match.group(1))

            columns = self._parse_columns(columns_block)

            tables.append(Table(
                name=table_name,
                schema_name=schema_name,
                columns=columns,
                row_count=row_count
            ))

        return tables
    
    def _parse_columns(self, columns_block: str) -> list[Column]:
        """Parse column definitions from CREATE TABLE block."""
        columns = []
        
        # Pattern for column definitions
        col_pattern = re.compile(
            r'^\s*(\w+)\s+'
            r'(VARCHAR2|NUMBER|DATE|TIMESTAMP|CHAR|CLOB|BLOB|INTEGER|XMLTYPE|RAW|SYS\.XMLTYPE)'
            r'(?:\((\d+)(?:\s*BYTE)?(?:,(\d+))?\))?'
            r'([^,\n]*)',
            re.IGNORECASE | re.MULTILINE
        )
        
        for match in col_pattern.finditer(columns_block):
            name, data_type, size, scale, rest = match.groups()
            
            # Skip if it looks like a constraint or other non-column
            if name.upper() in ('SUPPLEMENTAL', 'CONSTRAINT', 'PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK'):
                continue
            
            nullable = 'NOT NULL' not in (rest or '').upper()
            default_match = re.search(r'DEFAULT\s+(.+?)(?:\s+NOT|\s+NULL|\s*$)', rest or '', re.IGNORECASE)
            default_value = default_match.group(1).strip() if default_match else None
            
            columns.append(Column(
                name=name,
                data_type=data_type.upper(),
                nullable=nullable,
                max_length=int(size) if size and data_type.upper() in ('VARCHAR2', 'CHAR', 'RAW') else None,
                precision=int(size) if size and data_type.upper() == 'NUMBER' else None,
                scale=int(scale) if scale else None,
                default_value=default_value
            ))
        
        return columns
    
    def _parse_table_comments(self) -> dict[str, str]:
        """Extract table-level comments."""
        comments = {}
        pattern = re.compile(
            r"COMMENT\s+ON\s+TABLE\s+\w+\.(\w+)\s+IS\s+'((?:[^']|'')*)'",
            re.IGNORECASE
        )
        for match in pattern.finditer(self.content):
            table, comment = match.groups()
            comments[table] = comment.replace("''", "'")
        return comments
    
    def _parse_column_comments(self) -> dict[str, dict[str, str]]:
        """Extract column-level comments."""
        comments = {}
        pattern = re.compile(
            r"COMMENT\s+ON\s+COLUMN\s+\w+\.(\w+)\.(\w+)\s+IS\s+'((?:[^']|'')*)'",
            re.IGNORECASE
        )
        for match in pattern.finditer(self.content):
            table, column, comment = match.groups()
            if table not in comments:
                comments[table] = {}
            comments[table][column] = comment.replace("''", "'")
        return comments

    def _parse_views(self) -> list[View]:
        """Extract view definitions."""
        views = []

        # Pattern to match CREATE OR REPLACE FORCE VIEW blocks (with optional schema prefix)
        pattern = re.compile(
            r'CREATE\s+OR\s+REPLACE\s+FORCE\s+VIEW\s+(?:(\w+)\.)?(\w+)\s*\n'
            r'\((.*?)\)\s*\n'  # Column list
            r'(?:BEQUEATH\s+DEFINER\s*\n)?'  # Optional BEQUEATH clause
            r'AS\s*\n'
            r'(.*?)'  # SELECT statement
            r'(?=\n\n--|\nGRANT|\nCREATE|\Z)',  # Stop at next section
            re.DOTALL | re.IGNORECASE
        )

        # Get default schema from metadata
        metadata = self._parse_metadata()
        default_schema = metadata.get('schema_name', 'UNKNOWN')

        for match in pattern.finditer(self.content):
            schema_name, view_name, columns_str, select_stmt = match.groups()

            # Use default schema if not specified
            if not schema_name:
                schema_name = default_schema

            # Parse column names from the column list
            columns = [col.strip() for col in columns_str.replace('\n', ' ').split(',')]

            views.append(View(
                name=view_name,
                schema_name=schema_name,
                columns=columns,
                select_statement=select_stmt.strip()
            ))

        return views

    def _parse_procedures(self) -> list[Procedure]:
        """Extract procedure definitions from package specifications."""
        procedures = []

        # Pattern to match package specifications (with optional schema prefix)
        pkg_pattern = re.compile(
            r'CREATE\s+OR\s+REPLACE\s+PACKAGE\s+(?:(\w+)\.)?(\w+)\s+(?:AS|IS)\s*\n'
            r'(.*?)'
            r'\nEND\s+\w+;',
            re.DOTALL | re.IGNORECASE
        )

        # Get default schema from metadata
        metadata = self._parse_metadata()
        default_schema = metadata.get('schema_name', 'UNKNOWN')

        for pkg_match in pkg_pattern.finditer(self.content):
            schema_name, package_name, package_body = pkg_match.groups()

            # Use default schema if not specified
            if not schema_name:
                schema_name = default_schema

            # Pattern to match procedure declarations
            proc_pattern = re.compile(
                r'PROCEDURE\s+(\w+)\s*\((.*?)\);',
                re.DOTALL | re.IGNORECASE
            )

            for proc_match in proc_pattern.finditer(package_body):
                proc_name, params_str = proc_match.groups()

                # Parse parameters
                parameters = self._parse_procedure_parameters(params_str)

                # Check if any OUT parameter is a REF CURSOR
                has_refcursor_out = any(
                    p.direction in ('OUT', 'IN OUT') and
                    ('REF' in p.data_type.upper() and 'CURSOR' in p.data_type.upper())
                    for p in parameters
                )

                procedures.append(Procedure(
                    name=proc_name,
                    package_name=package_name,
                    schema_name=schema_name,
                    parameters=parameters,
                    has_refcursor_out=has_refcursor_out
                ))

        return procedures

    def _parse_procedure_parameters(self, params_str: str) -> list[ProcedureParameter]:
        """Parse procedure parameters from parameter string."""
        parameters = []

        # Normalize whitespace and newlines
        params_str = ' '.join(params_str.split())

        # Split by comma and parse each parameter
        # Pattern: param_name [IN|OUT|IN OUT] type
        for param in params_str.split(','):
            param = param.strip()
            if not param:
                continue

            # Match: name [direction] type
            match = re.match(
                r'(\w+)\s+(IN\s+OUT|OUT|IN)\s+(.+)',
                param,
                re.IGNORECASE
            )

            if match:
                param_name = match.group(1)
                direction = match.group(2).strip().upper()
                data_type = match.group(3).strip()
            else:
                # Try without explicit direction (defaults to IN)
                match = re.match(r'(\w+)\s+(.+)', param, re.IGNORECASE)
                if match:
                    param_name = match.group(1)
                    direction = 'IN'
                    data_type = match.group(2).strip()
                else:
                    continue

            parameters.append(ProcedureParameter(
                name=param_name,
                direction=direction,
                data_type=data_type
            ))

        return parameters

    def _parse_primary_keys(self) -> dict[str, PrimaryKey]:
        """Extract primary key constraints from ALTER TABLE statements."""
        primary_keys = {}

        # Pattern to match ALTER TABLE ... ADD PRIMARY KEY
        pattern = re.compile(
            r'ALTER\s+TABLE\s+(\w+)\s+ADD\s+\(\s*\n'
            r'\s*CONSTRAINT\s+(\w+)\s*\n'
            r'\s*PRIMARY\s+KEY\s*\n'
            r'\s*\((.*?)\)',
            re.DOTALL | re.IGNORECASE
        )

        for match in pattern.finditer(self.content):
            table_name, constraint_name, columns_str = match.groups()

            # Parse column list - may be multi-line
            columns = [col.strip() for col in columns_str.replace('\n', ' ').split(',')]

            primary_keys[table_name] = PrimaryKey(
                constraint_name=constraint_name,
                columns=columns
            )

        return primary_keys

    def _parse_foreign_keys(self) -> dict[str, list[ForeignKey]]:
        """Extract foreign key constraints from ALTER TABLE statements."""
        foreign_keys = {}

        # Pattern to match ALTER TABLE ... ADD FOREIGN KEY
        pattern = re.compile(
            r'ALTER\s+TABLE\s+(\w+)\s+ADD\s+\(\s*\n'
            r'\s*CONSTRAINT\s+(\w+)\s*\n'
            r'\s*FOREIGN\s+KEY\s+\((.*?)\)\s*\n'
            r'\s*REFERENCES\s+(\w+)\s+\((.*?)\)',
            re.DOTALL | re.IGNORECASE
        )

        for match in pattern.finditer(self.content):
            table_name, constraint_name, fk_columns_str, ref_table, ref_columns_str = match.groups()

            # Parse column lists
            fk_columns = [col.strip() for col in fk_columns_str.replace('\n', ' ').split(',')]
            ref_columns = [col.strip() for col in ref_columns_str.replace('\n', ' ').split(',')]

            if table_name not in foreign_keys:
                foreign_keys[table_name] = []

            foreign_keys[table_name].append(ForeignKey(
                constraint_name=constraint_name,
                columns=fk_columns,
                referenced_table=ref_table,
                referenced_columns=ref_columns
            ))

        return foreign_keys