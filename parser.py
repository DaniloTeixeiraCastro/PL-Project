import ply.yacc as yacc
from lexer import tokens, lexer

# Dictionary to store tables in memory
tables = {}

# Dictionary to store procedures
procedures = {}

# Operator precedence to resolve conflicts
precedence = (
    ('left', 'AND'),
)

def p_program(p):
    '''program : statement_list'''
    """Parse a program as a list of statements."""
    p[0] = p[1]

def p_statement_list(p):
    '''statement_list : statement
                     | statement_list statement'''
    """Parse a list of statements, separated by semicolons."""
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_statement(p):
    '''statement : import_statement
                | export_statement
                | discard_statement
                | rename_statement
                | print_statement
                | select_statement
                | create_table_statement
                | procedure_statement
                | call_statement
                | update_statement'''
    """Parse a single statement (e.g., IMPORT, SELECT, etc.)."""
    p[0] = p[1]

def p_import_statement(p):
    '''import_statement : IMPORT TABLE ID FROM STRING SEMICOLON'''
    """Parse IMPORT TABLE table_name FROM "filename";"""
    p[0] = ('IMPORT', p[3], p[5])

def p_export_statement(p):
    '''export_statement : EXPORT TABLE ID AS STRING SEMICOLON
                       | EXPORT AVG LPAREN ID RPAREN FROM ID AS STRING SEMICOLON'''
    """Parse EXPORT TABLE table_name AS "filename"; or EXPORT AVG(column) FROM table AS "filename";"""
    if len(p) == 7:
        p[0] = ('EXPORT', p[3], p[5])
    else:
        p[0] = ('EXPORT_AVG', p[4], p[7], p[9])

def p_discard_statement(p):
    '''discard_statement : DISCARD TABLE ID SEMICOLON'''
    """Parse DISCARD TABLE table_name;"""
    p[0] = ('DISCARD', p[3])

def p_rename_statement(p):
    '''rename_statement : RENAME TABLE ID ID SEMICOLON'''
    """Parse RENAME TABLE old_name new_name;"""
    p[0] = ('RENAME', p[3], p[4])

def p_print_statement(p):
    '''print_statement : PRINT TABLE ID SEMICOLON
                      | PRINT TABLE ID AS STRING SEMICOLON
                      | PRINT AVG LPAREN ID RPAREN FROM ID SEMICOLON
                      | PRINT STRING SEMICOLON'''
    if len(p) == 5:
        p[0] = ('PRINT', p[3])
    elif len(p) == 6:
        p[0] = ('PRINT', p[3], p[5])
    elif len(p) == 9:
        p[0] = ('PRINT_AVG', p[4], p[7])
    elif len(p) == 4:
        p[0] = ('PRINT_STRING', p[2])

def p_select_statement(p):
    '''select_statement : SELECT select_list FROM ID where_clause limit_clause SEMICOLON
                       | SELECT select_list FROM ID where_clause SEMICOLON
                       | SELECT select_list FROM ID limit_clause SEMICOLON
                       | SELECT select_list FROM ID SEMICOLON'''
    """Parse SELECT queries with optional WHERE and LIMIT clauses."""
    if len(p) == 8:
        p[0] = ('SELECT', p[2], p[4], p[5], p[6])
    elif len(p) == 7:
        if isinstance(p[5], tuple) and p[5][0] == 'WHERE':
            p[0] = ('SELECT', p[2], p[4], p[5], None)
        else:
            p[0] = ('SELECT', p[2], p[4], None, p[5])
    else:
        p[0] = ('SELECT', p[2], p[4], None, None)

def p_select_list(p):
    '''select_list : STAR
                  | column_list'''
    """Parse select list (* or list of columns)."""
    p[0] = '*' if p[1] == '*' else p[1]

def p_column_list(p):
    '''column_list : ID
                  | column_list COMMA ID'''
    """Parse a list of column names (e.g., col1, col2)."""
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_where_clause(p):
    '''where_clause : WHERE condition
                   | empty'''
    """Parse WHERE clause or empty."""
    p[0] = None if len(p) == 2 else ('WHERE', p[2])

def p_condition(p):
    '''condition : ID comparison_operator value
                | condition AND condition'''
    """Parse a condition (e.g., col = value or cond AND cond)."""
    if len(p) == 4:
        if p[2] == 'AND':
            p[0] = ('AND', p[1], p[3])
        else:
            p[0] = (p[2], p[1], p[3])

def p_comparison_operator(p):
    '''comparison_operator : EQUALS
                          | NOTEQUALS
                          | LT
                          | GT
                          | LTE
                          | GTE'''
    """Parse comparison operators (=, <>, <, >, <=, >=)."""
    p[0] = p[1]

def p_value(p):
    '''value : NUMBER
            | STRING
            | ID'''
    """Parse a value (number, string, or identifier)."""
    p[0] = p[1]

def p_limit_clause(p):
    '''limit_clause : LIMIT NUMBER
                   | empty'''
    """Parse LIMIT clause or empty."""
    p[0] = None if len(p) == 2 else p[2]

def p_create_table_statement(p):
    '''create_table_statement : CREATE TABLE ID select_statement
                             | CREATE TABLE ID FROM ID JOIN ID USING LPAREN ID RPAREN SEMICOLON'''
    """Parse CREATE TABLE from SELECT or JOIN."""
    if len(p) == 5:
        p[0] = ('CREATE_FROM_SELECT', p[3], p[4])
    else:
        p[0] = ('CREATE_FROM_JOIN', p[3], p[5], p[7], p[10])

def p_procedure_statement(p):
    '''procedure_statement : PROCEDURE ID DO statement_list END SEMICOLON'''
    """Parse PROCEDURE definition."""
    procedures[p[2]] = p[4]
    p[0] = ('PROCEDURE', p[2], p[4])

def p_call_statement(p):
    '''call_statement : CALL ID SEMICOLON'''
    """Parse CALL procedure_name;"""
    p[0] = ('CALL', p[2])

def p_update_statement(p):
    '''update_statement : UPDATE ID SET ID EQUALS STRING WHERE ID EQUALS STRING SEMICOLON'''
    # Só aceita UPDATE observacoes SET DataHoraObservacao = ... WHERE Id = ...;
    p[0] = ('UPDATE_DATAHORA', p[2], p[4], p[6], p[8], p[10])

def p_empty(p):
    '''empty :'''
    """Parse an empty production."""
    pass

def p_error(p):
    """Handle syntax errors."""
    if p:
        print(f"Syntax error at token {p.type} (value: {p.value}) at line {p.lineno}, position {p.lexpos}")
    else:
        print("Syntax error at EOF")

# Build the parser
parser = yacc.yacc()