import sys
import csv
from lexer import lexer
from parser import parser, tables, procedures

def evaluate_condition(row, condition):
    """Avalia uma condição em uma linha de dados.
    
    Args:
        row (dict): Linha de dados como um dicionário.
        condition (tuple): Tupla com a condição do parser (ex.: ('=', 'coluna', valor)).
    
    Returns:
        bool: True se a condição for satisfeita, False caso contrário.
    """
    # Se não houver condição, retorna True (sem filtro)
    if condition is None:
        return True
    
    # Verifica se a condição é uma tupla (formato do parser)
    if isinstance(condition, tuple):
        # Trata cláusula WHERE, avaliando a subcondição
        if condition[0] == 'WHERE':
            return evaluate_condition(row, condition[1])
        # Trata operador AND, combinando duas condições
        if condition[0] == 'AND':
            return evaluate_condition(row, condition[1]) and evaluate_condition(row, condition[2])
        
        # Trata comparações simples (ex.: coluna = valor)
        op, column, target_value = condition
        row_value = row.get(column)
        
        # Se a coluna não existe na linha, retorna False
        if row_value is None:
            return False

        # Tenta converter valores para números, se aplicável
        try:
            # Verifica se o valor alvo é numérico
            if isinstance(target_value, (int, float)) or (isinstance(target_value, str) and target_value.replace('.', '', 1).isdigit()):
                # Converte o valor da linha para float, se possível
                row_value = float(row_value) if isinstance(row_value, (str, int, float)) else row_value
                target_value = float(target_value)
        except (ValueError, TypeError):
            # Ignora erros de conversão (mantém como string)
            pass

        # Realiza a comparação com base no operador
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
    
    # Retorna False se a condição não for válida
    return False

def select_rows(table_name, select_list, where_clause=None, limit=None):
    """Seleciona linhas de uma tabela com base em condições.
    
    Args:
        table_name (str): Nome da tabela.
        select_list (str ou list): '*' para todas as colunas ou lista de nomes de colunas.
        where_clause (tuple): Tupla com a condição WHERE ou None.
        limit (str ou int): Número de linhas a limitar ou None.
    
    Returns:
        list: Lista de dicionários com as linhas selecionadas ou None se a tabela não existir.
    """
    # Verifica se a tabela existe
    if table_name not in tables:
        print(f"Erro: Tabela {table_name} não existe")
        return None
    
    table = tables[table_name]
    # Se a tabela estiver vazia, retorna uma lista vazia
    if not table:
        return []
    
    # Filtra linhas com base na cláusula WHERE
    filtered_rows = []
    seen_rows = set()  # Evita duplicatas
    for row in table:
        if evaluate_condition(row, where_clause):
            row_key = tuple(sorted(row.items()))  # Cria uma chave única para a linha
            if row_key not in seen_rows:
                seen_rows.add(row_key)
                filtered_rows.append(row)
    
    # Valida e aplica o limite de linhas
    if limit is not None:
        try:
            limit = int(limit)
            if limit < 0:
                raise ValueError("LIMIT deve ser não-negativo")
            filtered_rows = filtered_rows[:limit]  # Limita o número de linhas
        except (ValueError, TypeError):
            print(f"Erro: Valor inválido para LIMIT {limit}")
            return []
    
    # Seleciona colunas específicas, se não for '*'
    if select_list != '*':
        result = []
        for row in filtered_rows:
            new_row = {col: row[col] for col in select_list if col in row}  # Inclui apenas colunas solicitadas
            result.append(new_row)
        return result
    
    return filtered_rows

def parse_csv_line(line, line_number):
    """Analisa uma linha de um arquivo CSV, respeitando aspas.
    
    Args:
        line (str): Linha do CSV a ser analisada.
        line_number (int): Número da linha para relatar erros.
    
    Returns:
        list: Lista de valores extraídos.
    
    Raises:
        ValueError: Se houver aspas não fechadas.
    """
    values = []
    current = ''
    in_quotes = False  # Indica se está dentro de aspas
    i = 0
    
    while i < len(line):
        char = line[i]
        if char == '"':
            if not in_quotes:
                in_quotes = True  # Inicia uma string entre aspas
            elif i + 1 < len(line) and line[i + 1] == '"':
                current += '"'  # Trata aspas escapadas
                i += 1
            else:
                in_quotes = False  # Finaliza a string entre aspas
        elif char == ',' and not in_quotes:
            values.append(current.strip())  # Adiciona o valor à lista
            current = ''  # Reinicia para o próximo valor
        else:
            current += char  # Adiciona caractere ao valor atual
        i += 1
    
    values.append(current.strip())  # Adiciona o último valor
    if in_quotes:
        raise ValueError(f"Aspas não fechadas na linha {line_number + 1}")
    return values

def import_csv(file_name):
    """Importa um arquivo CSV para uma lista de dicionários.
    
    Args:
        file_name (str): Caminho para o arquivo CSV.
    
    Returns:
        list: Lista de dicionários representando as linhas ou None em caso de erro.
    """
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            lines = []
            # Lê o arquivo linha por linha
            for i, line in enumerate(file):
                line = line.strip()
                # Ignora linhas vazias ou comentários
                if not line or line.startswith('#'):
                    continue
                lines.append(line)
            
            # Verifica se o arquivo está vazio
            if not lines:
                raise ValueError("Arquivo vazio ou contém apenas comentários")
            
            # Extrai o cabeçalho (primeira linha)
            header = parse_csv_line(lines[0], 0)
            if not header:
                raise ValueError("Cabeçalho inválido: vazio ou malformado")
            
            # Valida os nomes das colunas
            for col in header:
                if not col.strip() or ',' in col:
                    raise ValueError(f"Nome de coluna inválido: {col}")
            
            data = []
            # Processa as linhas de dados
            for i, line in enumerate(lines[1:], 1):
                try:
                    values = parse_csv_line(line, i)
                    # Verifica se o número de valores corresponde ao cabeçalho
                    if len(values) != len(header):
                        print(f"Aviso: Linha {i+1} tem {len(values)} valores, esperado {len(header)}. Ignorando.")
                        continue
                    # Cria um dicionário para a linha
                    row = {col: value for col, value in zip(header, values)}
                    data.append(row)
                except Exception as e:
                    print(f"Aviso: Erro ao processar linha {i+1}: {str(e)}. Ignorando.")
                    continue
            
            print(f"Importadas {len(data)} linhas de {file_name}")
            return data
    except FileNotFoundError:
        print(f"Erro: Arquivo {file_name} não encontrado")
        return None
    except Exception as e:
        print(f"Erro ao ler {file_name}: {str(e)}")
        return None

def export_csv(table_name, file_name):
    """Exporta uma tabela para um arquivo CSV.
    
    Args:
        table_name (str): Nome da tabela.
        file_name (str): Caminho do arquivo CSV de saída.
    
    Returns:
        bool: True se bem-sucedido, False caso contrário.
    """
    # Verifica se a tabela existe
    if table_name not in tables:
        print(f"Erro: Tabela {table_name} não existe")
        return False
    
    try:
        with open(file_name, 'w', encoding='utf-8') as file:
            # Se a tabela estiver vazia, retorna True
            if not tables[table_name]:
                return True
            # Usa DictWriter para escrever o CSV
            writer = csv.DictWriter(file, fieldnames=tables[table_name][0].keys())
            writer.writeheader()  # Escreve o cabeçalho
            writer.writerows(tables[table_name])  # Escreve as linhas
            print(f"Exportadas {len(tables[table_name])} linhas para {file_name}")
        return True
    except Exception as e:
        print(f"Erro ao escrever em {file_name}: {str(e)}")
        return False

def join_tables(table1_name, table2_name, join_column):
    """Junta duas tabelas com base em uma coluna comum.
    
    Args:
        table1_name (str): Nome da primeira tabela.
        table2_name (str): Nome da segunda tabela.
        join_column (str): Coluna usada para a junção.
    
    Returns:
        list: Lista de linhas mescladas ou None se as tabelas não existirem.
    """
    # Verifica se ambas as tabelas existem
    if table1_name not in tables or table2_name not in tables:
        print(f"Erro: Tabela {table1_name} ou {table2_name} não existe")
        return None
    
    table1 = tables[table1_name]
    table2 = tables[table2_name]
    
    # Se uma das tabelas estiver vazia, retorna lista vazia
    if not table1 or not table2:
        return []
    
    # Cria um dicionário para a segunda tabela, usando a coluna de junção como chave
    table2_dict = {}
    for row in table2:
        key = row.get(join_column)
        if key is not None:
            table2_dict[key] = row
    
    result = []
    seen_rows = set()  # Evita duplicatas
    for row1 in table1:
        key = row1.get(join_column)
        # Se a chave existe na segunda tabela, mescla as linhas
        if key in table2_dict:
            merged_row = row1.copy()
            merged_row.update(table2_dict[key])  # Combina os dados
            row_key = tuple(sorted(merged_row.items()))  # Cria chave única
            if row_key not in seen_rows:
                seen_rows.add(row_key)
                result.append(merged_row)
    
    print(f"Juntadas {len(result)} linhas de {table1_name} e {table2_name}")
    return result

def execute_statement(statement):
    """Executa um comando CQL analisado.
    
    Args:
        statement (tuple): Tupla com o comando analisado pelo parser.
    """
    # Se o comando for vazio, retorna
    if not statement:
        return
    
    stmt_type = statement[0]  # Tipo do comando (ex.: 'SELECT', 'IMPORT')
    try:
        if stmt_type == 'IMPORT':
            _, table_name, file_name = statement
            data = import_csv(file_name)
            if data is not None:
                tables[table_name] = data  # Armazena a tabela em memória
        
        elif stmt_type == 'EXPORT':
            _, table_name, file_name = statement
            export_csv(table_name, file_name)  # Exporta a tabela
        
        elif stmt_type == 'DISCARD':
            _, table_name = statement
            if table_name in tables:
                del tables[table_name]  # Remove a tabela
                print(f"Tabela {table_name} descartada")
            else:
                print(f"Erro: Tabela {table_name} não existe")
        
        elif stmt_type == 'RENAME':
            _, old_name, new_name = statement
            if old_name in tables:
                tables[new_name] = tables.pop(old_name)  # Renomeia a tabela
                print(f"Tabela {old_name} renomeada para {new_name}")
            else:
                print(f"Erro: Tabela {old_name} não existe")
        
        elif stmt_type == 'PRINT':
            _, table_name = statement
            if table_name in tables:
                print(f"\nTabela: {table_name}")
                for row in tables[table_name]:
                    print(row)  # Exibe todas as linhas da tabela
            else:
                print(f"Erro: Tabela {table_name} não existe")
        
        elif stmt_type == 'SELECT':
            _, select_list, table_name, where_clause, limit = statement
            result = select_rows(table_name, select_list, where_clause, limit)
            if result is not None:
                print("\nResultado da Consulta:")
                for row in result:
                    print(row)  # Exibe os resultados da consulta
        
        elif stmt_type == 'CREATE_FROM_SELECT':
            _, new_table, select_stmt = statement
            result = select_rows(select_stmt[2], select_stmt[1], select_stmt[3], select_stmt[4])
            if result is not None:
                tables[new_table] = result  # Cria nova tabela com resultado de SELECT
                print(f"Tabela {new_table} criada a partir de SELECT")
        
        elif stmt_type == 'CREATE_FROM_JOIN':
            _, new_table, table1, table2, join_column = statement
            result = join_tables(table1, table2, join_column)
            if result is not None:
                tables[new_table] = result  # Cria nova tabela com resultado de JOIN
                print(f"Tabela {new_table} criada a partir de JOIN")
        
        elif stmt_type == 'PROCEDURE':
            _, proc_name, statements = statement
            procedures[proc_name] = statements  # Armazena o procedimento
            print(f"Procedimento {proc_name} definido")
        
        elif stmt_type == 'CALL':
            _, proc_name = statement
            if proc_name in procedures:
                for stmt in procedures[proc_name]:
                    execute_statement(stmt)  # Executa cada comando do procedimento
            else:
                print(f"Erro: Procedimento {proc_name} não existe")
    
    except Exception as e:
        print(f"Erro ao executar comando {stmt_type}: {str(e)}")

def main():
    """Função principal para executar o interpretador CQL."""
    # Verifica se há argumento de linha de comando (arquivo .fca)
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], 'r', encoding='utf-8') as file:
                input_text = file.read()  # Lê o arquivo
        except FileNotFoundError:
            print(f"Erro: Arquivo {sys.argv[1]} não encontrado")
            return
    else:
        # Modo interativo
        print("Interpretador CQL (Digite 'exit' para sair)")
        input_text = ""
        while True:
            try:
                line = input("CQL> ")
                if line.lower() == 'exit':
                    break
                input_text += line + "\n"  # Acumula comandos
            except EOFError:
                break
    
    try:
        # Analisa a entrada com o lexer e parser
        result = parser.parse(input_text, lexer=lexer)
        if result:
            # Executa cada comando analisado
            for statement in result:
                execute_statement(statement)
    except Exception as e:
        print(f"Erro: {str(e)}")

if __name__ == "__main__":
    main()