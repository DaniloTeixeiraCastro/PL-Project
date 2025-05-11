import sys
import csv
from lexer import lexer
from parser import parser, tables, procedures

def evaluate_condition(row, condition):
    """Evaluate a condition on a row.
    
    Args:
        row (dict): Row data as a dictionary.
        condition (tuple): Condition tuple from parser (e.g., ('=', 'col', value)).
    
    Returns:
        bool: True if the condition is satisfied, False otherwise.
    """
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

        # Convert for numeric comparisons if possible
        try:
            if isinstance(target_value, (int, float)) or (isinstance(target_value, str) and target_value.replace('.', '', 1).isdigit()):
                row_value = float(row_value) if isinstance(row_value, (str, int, float)) else row_value
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
    """Select rows from a table based on conditions.
    
    Args:
        table_name (str): Name of the table.
        select_list (str or list): '*' or list of column names.
        where_clause (tuple): WHERE condition tuple or None.
        limit (str or int): Number of rows to limit or None.
    
    Returns:
        list: List of dictionaries representing selected rows, or None if table doesn't exist.
    """
    if table_name not in tables:
        print(f"Error: Table {table_name} does not exist")
        return None
    
    table = tables[table_name]
    if not table:
        return []
    
    # Filter rows based on where clause
    filtered_rows = []
    seen_rows = set()
    for row in table:
        if evaluate_condition(row, where_clause):
            row_key = tuple(sorted(row.items()))
            if row_key not in seen_rows:
                seen_rows.add(row_key)
                filtered_rows.append(row)
    
    # Validate and apply limit
    if limit is not None:
        try:
            limit = int(limit)
            if limit < 0:
                raise ValueError("LIMIT must be non-negative")
            filtered_rows = filtered_rows[:limit]
        except (ValueError, TypeError):
            print(f"Error: Invalid LIMIT value {limit}")
            return []
    
    # Select specific columns if not '*'
    if select_list != '*':
        result = []
        for row in filtered_rows:
            new_row = {col: row[col] for col in select_list if col in row}
            result.append(new_row)
        return result
    
    return filtered_rows

def parse_csv_line(line, line_number):
    """Parse a CSV line respecting quotes.
    
    Args:
        line (str): CSV line to parse.
        line_number (int): Line number for error reporting.
    
    Returns:
        list: List of values.
    
    Raises:
        ValueError: If quotes are unclosed.
    """
    values = []
    current = ''
    in_quotes = False
    i = 0
    
    while i < len(line):
        char = line[i]
        if char == '"':
            if not in_quotes:
                in_quotes = True
            elif i + 1 < len(line) and line[i + 1] == '"':
                current += '"'
                i += 1
            else:
                in_quotes = False
        elif char == ',' and not in_quotes:
            values.append(current.strip())
            current = ''
        else:
            current += char
        i += 1
    
    values.append(current.strip())
    if in_quotes:
        raise ValueError(f"Unclosed quotes in line {line_number + 1}")
    return values

def import_csv(file_name):
    """Import a CSV file into a list of dictionaries.
    
    Args:
        file_name (str): Path to the CSV file.
    
    Returns:
        list: List of dictionaries representing rows, or None if an error occurs.
    """
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            lines = []
            for i, line in enumerate(file):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                lines.append(line)
            
            if not lines:
                raise ValueError("File is empty or contains only comments")
            
            header = parse_csv_line(lines[0], 0)
            if not header:
                raise ValueError("Invalid header: empty or malformed")
            
            for col in header:
                if not col.strip() or ',' in col:
                    raise ValueError(f"Invalid column name: {col}")
            
            data = []
            for i, line in enumerate(lines[1:], 1):
                try:
                    values = parse_csv_line(line, i)
                    if len(values) != len(header):
                        print(f"Warning: Line {i+1} has {len(values)} values, expected {len(header)}. Skipping.")
                        continue
                    row = {col: value for col, value in zip(header, values)}
                    data.append(row)
                except Exception as e:
                    print(f"Warning: Error processing line {i+1}: {str(e)}. Skipping.")
                    continue
            
            print(f"Imported {len(data)} rows from {file_name}")
            return data
    except FileNotFoundError:
        print(f"Error: File {file_name} not found")
        return None
    except Exception as e:
        print(f"Error reading {file_name}: {str(e)}")
        return None

def export_csv(table_name, file_name):
    """Export a table to a CSV file.
    
    Args:
        table_name (str): Name of the table.
        file_name (str): Output CSV file path.
    
    Returns:
        bool: True if successful, False otherwise.
    """
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
            print(f"Exported {len(tables[table_name])} rows to {file_name}")
        return True
    except Exception as e:
        print(f"Error writing to {file_name}: {str(e)}")
        return False

def join_tables(table1_name, table2_name, join_column):
    """Join two tables on a common column.
    
    Args:
        table1_name (str): First table name.
        table2_name (str): Second table name.
        join_column (str): Column to join on.
    
    Returns:
        list: List of merged rows, or None if tables don't exist.
    """
    if table1_name not in tables or table2_name not in tables:
        print(f"Error: Table {table1_name} or {table2_name} does not exist")
        return None
    
    table1 = tables[table1_name]
    table2 = tables[table2_name]
    
    if not table1 or not table2:
        return []
    
    table2_dict = {}
    for row in table2:
        key = row.get(join_column)
        if key is not None:
            table2_dict[key] = row
    
    result = []
    seen_rows = set()
    for row1 in table1:
        key = row1.get(join_column)
        if key in table2_dict:
            merged_row = row1.copy()
            merged_row.update(table2_dict[key])
            row_key = tuple(sorted(merged_row.items()))
            if row_key not in seen_rows:
                seen_rows.add(row_key)
                result.append(merged_row)
    
    print(f"Joined {len(result)} rows from {table1_name} and {table2_name}")
    return result

def execute_statement(statement):
    """Execute a parsed CQL statement.
    
    Args:
        statement (tuple): Parsed statement tuple from parser.
    """
    if not statement:
        return
    
    stmt_type = statement[0]
    try:
        if stmt_type == 'IMPORT':
            _, table_name, file_name = statement
            data = import_csv(file_name)
            if data is not None:
                tables[table_name] = data
        
        elif stmt_type == 'EXPORT':
            _, table_name, file_name = statement
            export_csv(table_name, file_name)
        
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
            result = select_rows(table_name, select_list, where_clause, limit)
            if result is not None:
                print("\nQuery Result:")
                for row in result:
                    print(row)
        
        elif stmt_type == 'CREATE_FROM_SELECT':
            _, new_table, select_stmt = statement
            result = select_rows(select_stmt[2], select_stmt[1], select_stmt[3], select_stmt[4])
            if result is not None:
                tables[new_table] = result
                print(f"Table {new_table} created from SELECT")
        
        elif stmt_type == 'CREATE_FROM_JOIN':
            _, new_table, table1, table2, join_column = statement
            result = join_tables(table1, table2, join_column)
            if result is not None:
                tables[new_table] = result
                print(f"Table {new_table} created from JOIN")
        
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
    
    except Exception as e:
        print(f"Error executing statement {stmt_type}: {str(e)}")

def main():
    """Main function to run the CQL interpreter."""
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], 'r', encoding='utf-8') as file:
                input_text = file.read()
        except FileNotFoundError:
            print(f"Error: File {sys.argv[1]} not found")
            return
    else:
        print("CQL Interpreter (Type 'exit' to quit)")
        input_text = ""
        while True:
            try:
                line = input("CQL> ")
                if line.lower() == 'exit':
                    break
                input_text += line + "\n"
            except EOFError:
                break
    
    try:
        result = parser.parse(input_text, lexer=lexer)
        if result:
            for statement in result:
                execute_statement(statement)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()