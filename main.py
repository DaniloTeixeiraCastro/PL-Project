import sys
import csv
from lexer import lexer
from parser import parser, tables, procedures

def evaluate_condition(row, condition):
    """Evaluate a condition on a row"""
    if condition is None:
        return True
    
    if isinstance(condition, tuple):
        if condition[0] == 'AND':
            return evaluate_condition(row, condition[1]) and evaluate_condition(row, condition[2])
        
        if len(condition) == 3:
            op, column, value = condition
            row_value = row.get(column)
            
            if row_value is None:
                return False
            
            try:
                row_value = float(row_value)
                value = float(value)
            except (ValueError, TypeError):
                pass
            
            if op == '=':
                return row_value == value
            elif op == '<>':
                return row_value != value
            elif op == '<':
                return row_value < value
            elif op == '>':
                return row_value > value
            elif op == '<=':
                return row_value <= value
            elif op == '>=':
                return row_value >= value
    
    return False

def select_rows(table_name, select_list, where_clause=None, limit=None):
    """Select rows from a table based on conditions"""
    if table_name not in tables:
        return None
    
    table = tables[table_name]
    if not table:
        return []
    
    # Filter rows based on where clause
    filtered_rows = [row for row in table if evaluate_condition(row, where_clause)]
    
    # Apply limit if specified
    if limit is not None:
        filtered_rows = filtered_rows[:int(limit)]
    
    # Select specific columns if not '*'
    if select_list != '*':
        result = []
        for row in filtered_rows:
            new_row = {}
            for col in select_list:
                if col in row:
                    new_row[col] = row[col]
            result.append(new_row)
        return result
    
    return filtered_rows

def import_csv(file_name):
    """Import a CSV file and return its contents as a list of dictionaries"""
    try:
        print(f"Trying to import file: {file_name}")
        with open(file_name, 'r', encoding='utf-8') as file:
            # Skip comment lines
            lines = [line for line in file if not line.strip().startswith('#')]
            
            # Read the header
            header = lines[0].strip().split(',')
            
            # Process each line
            data = []
            for line in lines[1:]:
                # Split by comma, but respect quotes
                values = []
                current = ''
                in_quotes = False
                for char in line:
                    if char == '"':
                        in_quotes = not in_quotes
                    elif char == ',' and not in_quotes:
                        values.append(current.strip())
                        current = ''
                    else:
                        current += char
                values.append(current.strip())
                
                # Create dictionary with header keys
                row = {}
                for i, key in enumerate(header):
                    if i < len(values):
                        row[key] = values[i]
                data.append(row)
            
            print(f"Successfully imported {len(data)} rows from {file_name}")
            return data
    except FileNotFoundError:
        print(f"Error: File {file_name} not found")
        return None
    except Exception as e:
        print(f"Error reading file {file_name}: {str(e)}")
        return None

def export_csv(table_name, file_name):
    """Export a table to a CSV file"""
    if table_name not in tables:
        print(f"Error: Table {table_name} does not exist")
        return False
    
    try:
        with open(file_name, 'w', encoding='utf-8') as file:
            if not tables[table_name]:
                return True
            
            writer = csv.DictWriter(file, fieldnames=tables[table_name][0].keys())
            writer.writeheader()
            writer.writerows(tables[table_name])
            print(f"Successfully exported {len(tables[table_name])} rows to {file_name}")
        return True
    except Exception as e:
        print(f"Error writing to file {file_name}: {str(e)}")
        return False

def join_tables(table1_name, table2_name, join_column):
    """Join two tables on a common column"""
    if table1_name not in tables or table2_name not in tables:
        print(f"Error: Tables {table1_name} or {table2_name} do not exist")
        return None
    
    table1 = tables[table1_name]
    table2 = tables[table2_name]
    
    if not table1 or not table2:
        return []
    
    # Create a dictionary for faster lookups
    table2_dict = {}
    for row in table2:
        key = row.get(join_column)
        if key is not None:
            if key not in table2_dict:
                table2_dict[key] = []
            table2_dict[key].append(row)
    
    # Perform the join
    result = []
    for row1 in table1:
        key = row1.get(join_column)
        if key in table2_dict:
            for row2 in table2_dict[key]:
                # Merge rows, preferring values from table2 for common columns
                merged_row = row1.copy()
                merged_row.update(row2)
                result.append(merged_row)
    
    print(f"Joined {len(result)} rows from {table1_name} and {table2_name}")
    return result

def execute_statement(statement):
    """Execute a parsed statement"""
    if not statement:
        return
    
    stmt_type = statement[0]
    print(f"Executing statement: {statement}")
    
    if stmt_type == 'IMPORT':
        _, table_name, file_name = statement
        data = import_csv(file_name)
        if data is not None:
            tables[table_name] = data
            print(f"Table {table_name} imported successfully")
    
    elif stmt_type == 'EXPORT':
        _, table_name, file_name = statement
        if export_csv(table_name, file_name):
            print(f"Table {table_name} exported to {file_name}")
    
    elif stmt_type == 'DISCARD':
        _, table_name = statement
        if table_name in tables:
            del tables[table_name]
            print(f"Table {table_name} discarded")
        else:
            print(f"Error: Table {table_name} does not exist")
    
    elif stmt_type == 'RENAME':
        _, old_name, new_name = statement
        if old_name in tables:
            tables[new_name] = tables.pop(old_name)
            print(f"Table {old_name} renamed to {new_name}")
        else:
            print(f"Error: Table {old_name} does not exist")
    
    elif stmt_type == 'PRINT':
        _, table_name = statement
        if table_name in tables:
            print(f"\nTable: {table_name}")
            for row in tables[table_name]:
                print(row)
        else:
            print(f"Error: Table {table_name} does not exist")
    
    elif stmt_type == 'SELECT':
        _, select_list, table_name, where_clause, limit = statement
        if table_name not in tables:
            print(f"Error: Table {table_name} does not exist")
            return
        
        result = select_rows(table_name, select_list, where_clause, limit)
        if result is not None:
            print("\nQuery Result:")
            for row in result:
                print(row)
    
    elif stmt_type == 'CREATE_FROM_SELECT':
        _, new_table, select_stmt = statement
        if select_stmt[1] == '*':
            # Create table from another table
            source_table = select_stmt[2]
            if source_table not in tables:
                print(f"Error: Source table {source_table} does not exist")
                return
            
            tables[new_table] = select_rows(source_table, '*', select_stmt[3], select_stmt[4])
            print(f"Table {new_table} created from SELECT statement")
        else:
            # Create table from query result
            result = select_rows(select_stmt[2], select_stmt[1], select_stmt[3], select_stmt[4])
            if result is not None:
                tables[new_table] = result
                print(f"Table {new_table} created from SELECT statement")
    
    elif stmt_type == 'CREATE_FROM_JOIN':
        _, new_table, table1, table2, join_column = statement
        # Remove parentheses from join column name
        if join_column.startswith('(') and join_column.endswith(')'):
            join_column = join_column[1:-1]
        result = join_tables(table1, table2, join_column)
        if result is not None:
            tables[new_table] = result
            print(f"Table {new_table} created from JOIN operation")
    
    elif stmt_type == 'PROCEDURE':
        _, proc_name, statements = statement
        procedures[proc_name] = statements
        print(f"Procedure {proc_name} defined")
    
    elif stmt_type == 'CALL':
        _, proc_name = statement
        if proc_name in procedures:
            for stmt in procedures[proc_name]:
                execute_statement(stmt)
        else:
            print(f"Error: Procedure {proc_name} does not exist")

def main():
    if len(sys.argv) > 1:
        # Read from file
        try:
            print(f"Reading from file: {sys.argv[1]}")
            with open(sys.argv[1], 'r') as file:
                input_text = file.read()
                print("File contents:")
                print(input_text)
        except FileNotFoundError:
            print(f"Error: File {sys.argv[1]} not found")
            return
    else:
        # Interactive mode
        print("CQL Interpreter (Type 'exit' to quit)")
        while True:
            try:
                input_text = input("CQL> ")
                if input_text.lower() == 'exit':
                    break
            except EOFError:
                break
    
    # Parse and execute the input
    try:
        print("Parsing input...")
        result = parser.parse(input_text, lexer=lexer)
        print(f"Parse result: {result}")
        if result:
            for statement in result:
                execute_statement(statement)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 