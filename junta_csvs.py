# Script para juntar os CSVs exportados em um único arquivo
import csv

arquivos = [
    'temps_altas.csv',
    'dados_completos.csv',
    'temperaturas_altas.csv'
]

with open('dados_completos_multi.csv', 'w', encoding='utf-8', newline='') as fout:
    for idx, arquivo in enumerate(arquivos):
        with open(arquivo, 'r', encoding='utf-8') as fin:
            if idx > 0:
                fout.write('\n')  # separador entre tabelas
            fout.write(f'==== {arquivo} ====' + '\n')
            for line in fin:
                fout.write(line)
print('Arquivo dados_completos_multi.csv gerado com sucesso.')
