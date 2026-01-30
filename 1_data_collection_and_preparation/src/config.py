import os
from pathlib import Path

# A raiz do projeto está um nível acima deste arquivo (src/config.py -> src/ -> raiz)
ROOT_DIR = Path(__file__).resolve().parent.parent

# Definição dos diretórios de dados
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Definição dos caminhos dos arquivos de dados
# Arquivos Brutos (Raw) - Devem ser baixados dos Dados Abertos da Câmara
PROPOSICOES_FILE = RAW_DATA_DIR / 'proposicoes-2025.json'
AUTORES_FILE = RAW_DATA_DIR / 'proposicoesAutores-2025.json'

# Arquivo Intermediário (Interim) - Gerado pelo script filtrar_dados.py
FILTERED_FILE = INTERIM_DATA_DIR / 'proposicoes-final-completo.json'

# Arquivo Final (Processed) - Gerado pelo script extrair_texto.py
FINAL_FILE = PROCESSED_DATA_DIR / 'proposicoes-com-texto-limpo.json'