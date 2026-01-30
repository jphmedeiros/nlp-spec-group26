"""
Módulo de Filtragem e Preparação de Dados (ETL).

Este script é responsável por carregar os dados brutos de proposições e autores,
aplicar regras de negócio para filtragem (tipo, data) e enriquecer os dados
das proposições com as informações de autoria.

Pipeline (Fluxo):
1. Carregamento dos arquivos JSON brutos.
2. Mapeamento de autores para suas respectivas proposições.
3. União (Merge) das proposições com seus autores.
4. Filtragem por tipo (PL, PEC, PLP) e intervalo de datas.
5. Limpeza de campos desnecessários para reduzir o tamanho do arquivo.
6. Salvamento do conjunto de dados intermediário.
"""

import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional

try:
    import config
except ImportError:
    from src import config

# --- 1. CONFIGURAÇÕES E CONSTANTES ---

# Caminhos definidos no arquivo de configuração
PROPOSICOES_FILE = config.PROPOSICOES_FILE
AUTORES_FILE = config.AUTORES_FILE
OUTPUT_FILE = config.FILTERED_FILE

# Regras de Negócio
# Tipos de proposição relevantes para a análise de NLP
TIPOS_VALIDOS = {'PL', 'PEC', 'PLP'}

# Recorte temporal: 1º Semestre Legislativo de 2025 (Fevereiro a Julho)
START_DATE = date(2025, 2, 2)
END_DATE = date(2025, 7, 17)

# Campos que serão removidos da proposição para economizar espaço e reduzir ruído
PROPOSICAO_KEYS_TO_REMOVE = [
    'ultimoStatus',
    'uriOrgaoNumerador',
    'uriPropAnterior',
    'uriPropPrincipal',
    'uriPropPosterior'
]

# Campos do objeto 'Autor' que serão mantidos
AUTOR_KEYS_TO_KEEP = [
    "idDeputadoAutor",
    "nomeAutor",
    "siglaPartidoAutor",
    "siglaUFAutor"
]

# --- 2. FUNÇÕES AUXILIARES ---

def load_json_data(filename: str) -> Optional[List[Dict[str, Any]]]:
    """
    Carrega dados de um arquivo JSON.
    
    Espera que o JSON tenha uma chave raiz 'dados' contendo a lista de registros,
    conforme o padrão da API de Dados Abertos da Câmara dos Deputados.

    Args:
        filename: Caminho completo para o arquivo JSON.

    Retorna:
        Uma lista de dicionários contendo os dados, ou None em caso de erro.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # A API retorna os dados dentro da chave 'dados'
            return data.get('dados', [])
    except FileNotFoundError:
        print(f"[ERRO] Arquivo não encontrado: {filename}")
        return None
    except json.JSONDecodeError:
        print(f"[ERRO] O arquivo '{filename}' não é um JSON válido.")
        return None
    except Exception as e:
        print(f"[ERRO] Falha inesperada ao ler {filename}: {e}")
        return None

def process_autores_map(autores_list: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """
    Cria um índice (dicionário) de autores agrupados pelo ID da proposição.

    Isso otimiza a busca de autores durante a união dos dados, evitando 
    uma complexidade alta de processamento (O(n^2)).

    Args:
        autores_list: Lista bruta de registros de autores.

    Retorna:
        Dicionário onde a chave é o 'idProposicao' e o valor é uma lista de autores limpos.
    """
    autores_map = {}
    for autor in autores_list:
        prop_id = autor.get('idProposicao')
        if not prop_id:
            continue
        
        # Cria um novo dicionário mantendo apenas os campos selecionados
        cleaned_autor = {key: autor.get(key) for key in AUTOR_KEYS_TO_KEEP}
        
        # Adiciona o autor à lista correspondente àquela proposição
        autores_map.setdefault(prop_id, []).append(cleaned_autor)
    return autores_map

def save_json_data(data_list: List[Dict[str, Any]], filename: str) -> None:
    """
    Salva a lista processada em um arquivo JSON.

    Args:
        data_list: Lista de proposições já processadas.
        filename: Caminho onde o arquivo será salvo.
    """
    try:
        output_data = {'dados': data_list}
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n[SUCESSO] Arquivo final salvo em: {filename}")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar o arquivo final: {e}")

# --- 3. PIPELINE PRINCIPAL ---

def main_pipeline():
    """Executa o fluxo completo de filtragem, união e limpeza dos dados."""
    print(">>> Iniciando pipeline de processamento de proposições...")
    
    # 1. Leitura dos Arquivos Fonte
    props_list = load_json_data(PROPOSICOES_FILE)
    autores_list = load_json_data(AUTORES_FILE)
    
    if props_list is None or autores_list is None:
        print("Processo interrompido devido a erro na leitura dos arquivos.")
        return

    print(f"   Proposições carregadas: {len(props_list)}")
    print(f"   Registros de autoria carregados: {len(autores_list)}")
    
    # 2. Processamento dos Autores (Indexação)
    autores_map = process_autores_map(autores_list)
    print(f"   Mapa de autores criado.")

    # 3. União (Merge) - Adiciona autores às proposições
    merged_list = []
    for prop in props_list:
        prop_id = prop.get('id')
        # Busca a lista de autores no mapa; retorna lista vazia se não houver
        prop['autores'] = autores_map.get(prop_id, [])
        merged_list.append(prop)
    
    print(f"   União de dados concluída.")

    # 4. Filtragem (Regras de Negócio)
    filtered_list = []
    # Contadores para relatório de exclusão
    removed_counts = {"tipo": 0, "data": 0, "vazia": 0}

    for prop in merged_list:
        # Filtra por Tipo de Proposição
        sigla_tipo = prop.get('siglaTipo')
        if sigla_tipo not in TIPOS_VALIDOS:
            removed_counts["tipo"] += 1
            continue
            
        # Filtra por Data de Apresentação
        data_str = prop.get('dataApresentacao')
        if not data_str:
            removed_counts["vazia"] += 1
            continue
            
        try:
            # Converte string ISO para objeto de data para comparação
            data_ap = datetime.fromisoformat(data_str.split('T')[0]).date()
            
            if not (START_DATE <= data_ap <= END_DATE):
                removed_counts["data"] += 1
                continue
        except ValueError:
            removed_counts["vazia"] += 1
            continue
            
        # Se passou em todos os filtros, adiciona à lista final
        filtered_list.append(prop)
        
    print(f"   Filtragem concluída. Registros removidos:")
    print(f"     - Por Tipo invalido ({TIPOS_VALIDOS}): {removed_counts['tipo']}")
    print(f"     - Fora do intervalo de data ({START_DATE} a {END_DATE}): {removed_counts['data']}")
    print(f"     - Data inválida ou vazia: {removed_counts['vazia']}")

    # 5. Limpeza Final de Campos
    final_list = []
    for prop in filtered_list:
        # Remove chaves desnecessárias para o NLP
        for key in PROPOSICAO_KEYS_TO_REMOVE:
            prop.pop(key, None) # .pop() remove a chave se existir
        
        final_list.append(prop)
        
    print(f"   Limpeza de campos desnecessários concluída.")
    print(f">>> Total de registros prontos para extração de texto: {len(final_list)}")

    # 6. Salvar Resultado
    save_json_data(final_list, OUTPUT_FILE)

# --- Execução do Script ---
if __name__ == "__main__":
    main_pipeline()