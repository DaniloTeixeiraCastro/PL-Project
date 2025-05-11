import sys
import csv
from lexer import lexer
from parser import parser, tables, procedures

def evaluate_condition(row, condition):
    """Evaluate a condition on a row"""
    if condition is None:
        return True
    
    if isinstance(condition, tuple):
        if condition[0] == 'WHERE':
            return evaluate_condition(row, condition[1])
            
        if condition[0] == 'AND':
            return evaluate_condition(row, condition[1]) and evaluate_condition(row, condition[2])
        
        # Handle basic comparison
        op, column, target_value = condition
        row_value = row.get(column)
        
        if row_value is None:
            return False

        # Convert to float for numeric comparisons if possible
        try:
            if isinstance(row_value, str) and row_value.replace('.','',1).isdigit():
                row_value = float(row_value)
            elif isinstance(row_value, (int, float)):
                row_value = float(row_value)
                
            if isinstance(target_value, (int, float)):
                target_value = float(target_value)
            elif isinstance(target_value, str) and target_value.replace('.','',1).isdigit():
                target_value = float(target_value)
        except (ValueError, TypeError):
            pass

        if op == '=':
            return row_value == target_value
        elif op == '<>':
            return row_value != target_value
        elif op == '<':
            return row_value < target_value
        elif op == '>':
            return row_value > target_value
        elif op == '<=':
            return row_value <= target_value
        elif op == '>=':
            return row_value >= target_value
    
    return False

def select_rows(table_name, select_list, where_clause=None, limit=None):
    """Select rows from a table based on conditions"""
    if table_name not in tables:
        return None
    
    table = tables[table_name]
    if not table:
        return []
    
    # Filter rows based on where clause
    filtered_rows = []
    seen_rows = set()  # Track unique rows
    for row in table:
        if evaluate_condition(row, where_clause):
            # Create a tuple of values for comparison
            row_key = tuple(sorted(row.items()))
            if row_key not in seen_rows:
                seen_rows.add(row_key)
                filtered_rows.append(row)
    
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

def parse_csv_line(line, line_number):
    """Parse a CSV line respecting quotes and returning a list of values."""
    values = []
    current = ''
    in_quotes = False
    i = 0
    
    while i < len(line):
        char = line[i]
        
        # Handle quotes
        if char == '"':
            if not in_quotes:  # Start of quoted field
                in_quotes = True
            elif i + 1 < len(line) and line[i + 1] == '"':  # Escaped quote
                current += '"'
                i += 1  # Skip next quote
            else:  # End of quoted field
                in_quotes = False
        # Handle commas
        elif char == ',' and not in_quotes:
            values.append(current.strip())
            current = ''
        # Handle all other characters
        else:
            current += char
        i += 1
    
    # Add the last field
    values.append(current.strip())
    
    # Validate no unclosed quotes
    if in_quotes:
        raise ValueError(f"Unclosed quotes in line {line_number + 1}")
        
    return values

def import_csv(file_name):
    """Import a CSV file and return its contents as a list of dictionaries.
    Validates CSV structure and handles malformed lines."""
    try:
        print(f"Trying to import file: {file_name}")
        with open(file_name, 'r', encoding='utf-8') as file:
            lines = []
            line_number = 0
            
            # Read and validate each line
            for line in file:
                line_number += 1
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                    
                # Skip comment lines starting with #
                if line.startswith('#'):
                    continue
                
                lines.append(line)
            
            if not lines:
                raise ValueError("File is empty or contains only comments")
                
            # Read and validate header
            header = parse_csv_line(lines[0], 0)
            if not header:
                raise ValueError("Invalid header: empty or malformed")
                
            # Validate header names are valid identifiers
            for col in header:
                if not col.strip() or ',' in col:
                    raise ValueError(f"Invalid column name: {col}")
            
            # Process each data line
            data = []
            for i, line in enumerate(lines[1:], 1):
                try:
                    values = parse_csv_line(line, i)
                    if len(values) != len(header):
                        print(f"Warning: Line {i+1} has {len(values)} values but header has {len(header)} columns. Skipping line: {line}")
                        continue
                        
                    # Create dictionary with header keys and convert numeric values
                    row = {}
                    for col, value in zip(header, values):
                        # Try to convert numeric values
                        try:
                            if value.strip():  # Skip empty values
                                if '.' in value:
                                    row[col] = float(value)
                                elif value.isdigit():
                                    row[col] = int(value)
                                else:
                                    row[col] = value
                            else:
                                row[col] = value
                        except ValueError:
                            row[col] = value
                    data.append(row)
                except Exception as e:
                    print(f"Warning: Error processing line {i+1}: {str(e)}. Skipping line: {line}")
                    continue
                
                # Create dictionary with header keys and convert numeric values
                row = {}
                for i, key in enumerate(header):
                    if i < len(values):
                        value = values[i].strip('"')  # Remove quotes if present
                        # Try to convert numeric values
                        try:
                            if '.' in value:
                                row[key] = float(value)
                                print(f"Converted {key}={value} to float: {row[key]}")
                            elif value.isdigit():
                                row[key] = int(value)
                                print(f"Converted {key}={value} to int: {row[key]}")
                            else:
                                row[key] = value
                                print(f"Kept {key}={value} as string")
                        except ValueError:
                            row[key] = value
                            print(f"Failed to convert {key}={value}, keeping as string")
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
                table2_dict[key] = row  # Store only one row per key
    
    # Perform the join
    result = []
    seen_rows = set()  # Track unique rows
    for row1 in table1:
        key = row1.get(join_column)
        if key in table2_dict:
            row2 = table2_dict[key]
            # Merge rows, preferring values from table2 for common columns
            merged_row = row1.copy()
            merged_row.update(row2)
            
            # Create a tuple of values for comparison
            row_key = tuple(sorted(merged_row.items()))
            if row_key not in seen_rows:
                seen_rows.add(row_key)
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