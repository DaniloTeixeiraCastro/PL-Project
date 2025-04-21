# CQL Interpreter

A CQL (Comma Query Language) interpreter implemented in Python using PLY. This interpreter can process CSV files and execute SQL-like queries.

## Features

- Import and export CSV files
- Execute SQL-like queries on CSV data
- Create new tables from queries
- Support for procedures
- Comments support (single and multi-line)

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the interpreter:
```bash
python main.py [input_file.fca]
```

If no input file is provided, the interpreter will read commands from the terminal.

## Supported Commands

- `IMPORT TABLE table_name FROM "file.csv";`
- `EXPORT TABLE table_name AS "file.csv";`
- `DISCARD TABLE table_name;`
- `RENAME TABLE old_name new_name;`
- `PRINT TABLE table_name;`
- `SELECT * FROM table_name;`
- `SELECT column1, column2 FROM table_name WHERE condition;`
- `CREATE TABLE new_table SELECT * FROM table_name WHERE condition;`
- `CREATE TABLE new_table FROM table1 JOIN table2 USING(column);`
- `PROCEDURE procedure_name DO ... END`
- `CALL procedure_name;`

## Comments

- Single line comments: `-- comment`
- Multi-line comments: `{- comment -}` 