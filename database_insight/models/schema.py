from pydantic import BaseModel
from datetime import datetime

class Column(BaseModel):
    name: str
    data_type: str
    nullable: bool = True
    max_length: int | None = None
    precision: int | None = None
    scale: int | None = None
    default_value: str | None = None
    comment: str | None = None

class PrimaryKey(BaseModel):
    constraint_name: str
    columns: list[str]

class ForeignKey(BaseModel):
    constraint_name: str
    columns: list[str]
    referenced_table: str
    referenced_columns: list[str]

class Table(BaseModel):
    name: str
    schema_name: str
    columns: list[Column]
    row_count: int = 0
    comment: str | None = None
    primary_key: PrimaryKey | None = None
    foreign_keys: list[ForeignKey] = []

class View(BaseModel):
    name: str
    schema_name: str
    columns: list[str]  # Column names from view definition
    select_statement: str  # The SELECT query
    comment: str | None = None

class ProcedureParameter(BaseModel):
    name: str
    direction: str  # IN, OUT, IN OUT
    data_type: str

class Procedure(BaseModel):
    name: str
    package_name: str
    schema_name: str
    parameters: list[ProcedureParameter]
    has_refcursor_out: bool = False  # True if has OUT parameter of type REF CURSOR

class SchemaModel(BaseModel):
    database_type: str
    database_version: str | None = None
    schema_name: str
    extracted_at: datetime
    tables: list[Table]
    views: list[View] = []
    procedures: list[Procedure] = []