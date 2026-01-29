# Spec Gate 3 - Data Extractor

Sistema de extração, processamento e classificação de proposições legislativas usando LLMs.

## 📋 Pré-requisitos

- Python 3.8+
- PostgreSQL 12+
- Chave de API OpenAI

## 🚀 Instalação

### 1. Clonar o repositório
```bash
git clone <repo-url>
cd spec_gate3
```

### 2. Criar ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente
```bash
cp .env.example .env
# Editar .env com suas credenciais
```

**Variáveis obrigatórias:**
- `DB_NAME` - Nome do banco de dados PostgreSQL
- `DB_USER` - Usuário do PostgreSQL
- `DB_PASS` - Senha do PostgreSQL
- `OPENAI_API_KEY` - Chave de API OpenAI

**Variáveis opcionais:**
- `DB_HOST` - Host do PostgreSQL (padrão: localhost)
- `DB_PORT` - Porta do PostgreSQL (padrão: 5432)
- `PROPOSITIONS_JSON` - Caminho para arquivo de proposições (padrão: ./proposicoes.json)

### 5. Criar tabelas no banco de dados
```bash
python -m data_extractor.migrations
```

## 📊 Uso

### Executar pipeline completo
```bash
python main.py
```

O pipeline executa as seguintes etapas:
1. ✅ Carrega dataset de proposições do JSON
2. ✅ Extrai e insere autores únicos
3. ✅ Extrai e insere proposições
4. ✅ Gera e insere word clouds
5. ✅ Processa proposições com OpenAI (resumo, sentimento, ideologia, NER)
6. ✅ Classifica proposições em tópicos pré-definidos

## 📁 Estrutura do Projeto

```
spec_gate3/
├── main.py                          # Ponto de entrada principal
├── migrations.py                    # Migrações de banco de dados
├── requirements.txt                 # Dependências Python
├── .env.example                     # Exemplo de configuração
├── .gitignore                       # Arquivos a ignorar no Git
├── README.md                        # Este arquivo
│
├── data_extractor/
│   ├── __init__.py
│   ├── config.py                   # Configuração e variáveis de ambiente
│   ├── db.py                       # Funções de banco de dados
│   ├── extractor.py                # Extração de dados
│   ├── openai_service.py           # Cliente OpenAI
│   ├── repository.py               # Operações de persistência
│   ├── use_cases.py                # Lógica de processamento
│   └── utils.py                    # Utilitários (word cloud, etc)
│
├── proposicoes.json                # Dataset de proposições (JSON)
```