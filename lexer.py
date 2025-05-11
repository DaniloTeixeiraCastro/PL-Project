import ply.lex as lex

# List of token names
tokens = (
    # Keywords
    'IMPORT', 'EXPORT', 'TABLE', 'FROM', 'AS', 'DISCARD', 'RENAME',
    'PRINT', 'SELECT', 'WHERE', 'CREATE', 'JOIN', 'USING', 'PROCEDURE',
    'DO', 'END', 'CALL', 'LIMIT',
    
    # Operators
    'EQUALS', 'NOTEQUALS', 'LT', 'GT', 'LTE', 'GTE', 'AND',
    
    # Literals
    'ID', 'NUMBER', 'STRING',
    
    # Punctuation
    'COMMA', 'SEMICOLON', 'LPAREN', 'RPAREN', 'STAR',
    
    # Comments
    'COMMENT', 'MULTILINE_COMMENT'
)

# Regular expression rules for simple tokens
t_EQUALS = r'='
t_NOTEQUALS = r'<>'
t_LT = r'<'
t_GT = r'>'
t_LTE = r'<='
t_GTE = r'>='
t_AND = r'AND'
t_COMMA = r','
t_SEMICOLON = r';'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_STAR = r'\*'

# Keywords
def t_IMPORT(t):
    r'IMPORT'
    return t

def t_EXPORT(t):
    r'EXPORT'
    return t

def t_TABLE(t):
    r'TABLE'
    return t

def t_FROM(t):
    r'FROM'
    return t

def t_AS(t):
    r'AS'
    return t

def t_DISCARD(t):
    r'DISCARD'
    return t

def t_RENAME(t):
    r'RENAME'
    return t

def t_PRINT(t):
    r'PRINT'
    return t

def t_SELECT(t):
    r'SELECT'
    return t

def t_WHERE(t):
    r'WHERE'
    return t

def t_CREATE(t):
    r'CREATE'
    return t

def t_JOIN(t):
    r'JOIN'
    return t

def t_USING(t):
    r'USING'
    return t

def t_PROCEDURE(t):
    r'PROCEDURE'
    return t

def t_DO(t):
    r'DO'
    return t

def t_END(t):
    r'END'
    return t

def t_CALL(t):
    r'CALL'
    return t

def t_LIMIT(t):
    r'LIMIT'
    return t

# Regular expression rules for complex tokens
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    # Identifiers: starts with letter or underscore, followed by letters, digits, or underscores
    return t

def t_NUMBER(t):
    r'-?\d*\.?\d+'
    # Numbers: optional minus sign, optional integer part, optional decimal point, at least one digit
    t.value = float(t.value)
    return t

def t_STRING(t):
    r'\"[^\"]*\"'
    # Strings: text enclosed in double quotes, allowing commas and other characters
    t.value = t.value[1:-1]  # Remove quotes
    return t

def t_COMMENT(t):
    r'--.*'
    # Single-line comments: ignored
    pass

def t_MULTILINE_COMMENT(t):
    r'\{-.*?-\}'
    # Multi-line comments: ignored, non-greedy match
    pass

# Define a rule to track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# A string containing ignored characters (spaces and tabs)
t_ignore = ' \t'

# Error handling rule
def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lineno}, position {t.lexpos}")
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

# Example test function (uncomment to use)
"""
def test_lexer(input_string):
    lexer.input(input_string)
    for token in lexer:
        print(f"Token: {token.type}, Value: {token.value}, Line: {token.lineno}")

# Test cases
test_input = '''
IMPORT TABLE estacoes FROM "estacoes.csv";
SELECT * FROM observacoes WHERE Temperatura > 22;
SELECT DataHoraObservacao, Id FROM observacoes WHERE Temperatura < -10.5;
-- This is a comment
{- This is a
   multiline comment -}
CREATE TABLE mais_quentes SELECT * FROM observacoes WHERE Temperatura > 22;
'''
test_lexer(test_input)
"""