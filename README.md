# Projeto de Análise de Proposições Legislativas (NLP) - Grupo 26

Este projeto foi desenvolvido para coletar, processar e analisar proposições legislativas da Câmara dos Deputados do Brasil. Ele utiliza técnicas de Processamento de Linguagem Natural (NLP) e modelos de linguagem de grande escala (LLMs) para extrair insights automáticos de textos legislativos.

## 🏗️ Estrutura do Projeto

O repositório está organizado em três módulos principais:

### 1. Coleta e Preparação de Dados (`1_data_collection_and_preparation/`)
Pipeline ETL em Python responsável por preparar o dataset inicial.
*   **Função:** Filtra dados brutos (JSON) da API de Dados Abertos, baixa os PDFs do inteiro teor das proposições e extrai o texto limpo.
*   **Tecnologias:** Python, Requests, PyMuPDF (fitz).

### 2. Backend e Processamento NLP (`2_backend/`)
Aplicação Python que realiza a análise inteligente dos dados.
*   **Função:** Ingestão de dados no PostgreSQL, geração de nuvens de palavras e integração com OpenAI para:
    *   Sumarização de textos.
    *   Análise de sentimento e ideologia.
    *   Extração de Entidades Nomeadas (NER).
    *   Classificação temática automática.
*   **Tecnologias:** Python, PostgreSQL, OpenAI API, Docling, Pydantic.

### 3. Frontend (`3_frontend/`)
Painel de visualização de dados.
*   **Arquivo:** `nlp-spec-group26.pbix`
*   **Função:** Dashboard em Power BI para visualização dos resultados analíticos gerados pelo backend.

---

## 🚀 Como Executar

### Pré-requisitos
*   Python 3.12 ou superior.
*   PostgreSQL instalado e em execução.
*   Chave de API da OpenAI.

### Passo 1: Preparação dos Dados
1.  Acesse a pasta: `cd 1_data_collection_and_preparation`
2.  Instale as dependências: `pip install -r requirements.txt`
3.  Execute os scripts de filtragem e extração:
    ```bash
    python src/filtrar_dados.py
    python src/extrair_texto.py
    ```

### Passo 2: Backend e Análise
1.  Acesse a pasta: `cd 2_backend`
2.  Instale as dependências: `pip install -r requirements.txt`
3.  Configure as variáveis de ambiente:
    *   Renomeie `.env.example` para `.env`.
    *   Preencha as credenciais do banco de dados e sua `OPENAI_API_KEY`.
4.  Crie as tabelas no banco de dados:
    ```bash
    python -m data_extractor.migrations
    ```
5.  Inicie o pipeline de processamento:
    ```bash
    python main.py
    ```

### Passo 3: Visualização
1.  Abra o arquivo `nlp-spec-group26.pbix` no **Power BI Desktop**.
2.  Atualize as fontes de dados para apontar para o seu banco de dados PostgreSQL.

---

## 🛠️ Convenções de Desenvolvimento

*   **Ambientes Virtuais:** Recomenda-se criar um `venv` independente para cada pasta de código (`1_` e `2_`).
*   **Configurações:**
    *   Parâmetros de limpeza de texto e datas estão em `1_data_collection_and_preparation/src/config.py`.
    *   Configurações de infraestrutura e IA estão no `.env` do backend.
