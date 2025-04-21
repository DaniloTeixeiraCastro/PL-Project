import ply.yacc as yacc
from lexer import tokens, lexer

# Dictionary to store tables in memory
tables = {}

# Dictionary to store procedures
procedures = {}

def p_program(p):
    '''program : statement_list'''
    p[0] = p[1]

def p_statement_list(p):
    '''statement_list : statement
                     | statement_list statement'''
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
                | call_statement'''
    p[0] = p[1]

def p_import_statement(p):
    'import_statement : IMPORT TABLE ID FROM STRING SEMICOLON'
    table_name = p[3]
    file_name = p[5]
    # TODO: Implement CSV file import
    p[0] = ('IMPORT', table_name, file_name)

def p_export_statement(p):
    'export_statement : EXPORT TABLE ID AS STRING SEMICOLON'
    table_name = p[3]
    file_name = p[5]
    # TODO: Implement CSV file export
    p[0] = ('EXPORT', table_name, file_name)

def p_discard_statement(p):
    'discard_statement : DISCARD TABLE ID SEMICOLON'
    table_name = p[3]
    # TODO: Implement table discard
    p[0] = ('DISCARD', table_name)

def p_rename_statement(p):
    'rename_statement : RENAME TABLE ID ID SEMICOLON'
    old_name = p[3]
    new_name = p[4]
    # TODO: Implement table rename
    p[0] = ('RENAME', old_name, new_name)

def p_print_statement(p):
    'print_statement : PRINT TABLE ID SEMICOLON'
    table_name = p[3]
    # TODO: Implement table print
    p[0] = ('PRINT', table_name)

def p_select_statement(p):
    '''select_statement : SELECT select_list FROM ID where_clause limit_clause SEMICOLON
                       | SELECT select_list FROM ID where_clause SEMICOLON
                       | SELECT select_list FROM ID limit_clause SEMICOLON
                       | SELECT select_list FROM ID SEMICOLON'''
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
    if p[1] == '*':
        p[0] = '*'
    else:
        p[0] = p[1]

def p_column_list(p):
    '''column_list : ID
                  | column_list COMMA ID'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_where_clause(p):
    '''where_clause : WHERE condition
                   | empty'''
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ('WHERE', p[2])

def p_condition(p):
    '''condition : ID comparison_operator value
                | condition AND condition'''
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
    p[0] = p[1]

def p_value(p):
    '''value : NUMBER
            | STRING
            | ID'''
    p[0] = p[1]

def p_limit_clause(p):
    '''limit_clause : LIMIT NUMBER
                   | empty'''
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = p[2]

def p_create_table_statement(p):
    '''create_table_statement : CREATE TABLE ID select_statement
                             | CREATE TABLE ID FROM ID JOIN ID USING ID SEMICOLON'''
    if len(p) == 5:
        p[0] = ('CREATE_FROM_SELECT', p[3], p[4])
    else:
        p[0] = ('CREATE_FROM_JOIN', p[3], p[5], p[7], p[9])

def p_procedure_statement(p):
    'procedure_statement : PROCEDURE ID DO statement_list END SEMICOLON'
    procedure_name = p[2]
    statements = p[4]
    procedures[procedure_name] = statements
    p[0] = ('PROCEDURE', procedure_name, statements)

def p_call_statement(p):
    'call_statement : CALL ID SEMICOLON'
    procedure_name = p[2]
    p[0] = ('CALL', procedure_name)

def p_empty(p):
    'empty :'
    pass

# Error rule for syntax errors
def p_error(p):
    if p:
        print(f"Syntax error at token {p.type} (value: {p.value}) at line {p.lineno}")
    else:
        print("Syntax error at EOF")

# Build the parser
parser = yacc.yacc() 