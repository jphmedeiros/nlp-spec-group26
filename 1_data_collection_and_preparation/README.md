# Análise de Proposições Legislativas da Câmara dos Deputados (TCC)

Este repositório contém o código-fonte e o pipeline de processamento de dados para a análise de proposições legislativas da Câmara dos Deputados do Brasil. Este projeto faz parte de um Trabalho de Conclusão de Curso (TCC) de uma pós-graduação em Processamento de Linguagem Natural (NLP).

## 📂 Estrutura do Projeto

```text
TCC/
├── data/
│   ├── raw/            # Dados originais imutáveis (JSONs brutos)
│   ├── interim/        # Dados intermediários (filtrados e transformados)
│   └── processed/      # Conjuntos de dados finais (com texto extraído)
├── src/                # Código-fonte
│   ├── config.py       # Definições de caminhos e configurações
│   ├── filtrar_dados.py # Script ETL para filtragem e união de dados
│   └── extrair_texto.py # Script para extração e limpeza de texto de PDFs
├── requirements.txt    # Dependências do Python
└── README.md           # Documentação do projeto
```

## 🚀 Como Começar

### Pré-requisitos

*   Python 3.12 ou superior
*   Ambiente virtual (recomendado)

### Instalação

1.  Clone o repositório:
    ```bash
    git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
    cd TCC
    ```

2.  Crie e ative um ambiente virtual:
    ```bash
    python -m venv venv
    # Windows:
    .\venv\Scripts\activate
    # Linux/Mac:
    source venv/bin/activate
    ```

3.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

## 🛠️ Uso

O pipeline consiste em dois scripts principais localizados no diretório `src`.

### 1. Filtragem e União de Dados
Filtra as proposições brutas por tipo (PL, PEC, PLP) e data, e mescla as informações dos autores.

```bash
python src/filtrar_dados.py
```
*   **Entrada:** `data/raw/proposicoes-2025.json`, `data/raw/proposicoesAutores-2025.json`
*   **Saída:** `data/interim/proposicoes-final-completo.json`

### 2. Extração e Limpeza de Texto
Baixa o PDF do inteiro teor de cada proposição, extrai o texto e realiza a limpeza (remoção de cabeçalhos, rodapés, carimbos, etc.).

```bash
python src/extrair_texto.py
```
*   **Entrada:** `data/interim/proposicoes-final-completo.json`
*   **Saída:** `data/processed/proposicoes-com-texto-limpo.json`

## ⚙️ Configuração

Você pode modificar as regras de filtragem (datas, tipos) e os limiares de limpeza diretamente nos scripts ou editando o arquivo `src/config.py` (para caminhos de arquivos).

*   **`src/filtrar_dados.py`**: Edite `START_DATE`, `END_DATE`, `TIPOS_VALIDOS`.
*   **`src/extrair_texto.py`**: Edite `TOP_FRAC`, `REPEAT_THRESHOLD` para ajustar a sensibilidade da limpeza de PDFs.

## 📊 Fonte de Dados

Os arquivos de dados brutos utilizados neste projeto são obtidos através do portal de **Dados Abertos da Câmara dos Deputados**.

Os arquivos `proposicoes-2025.json` e `proposicoesAutores-2025.json` devem ser baixados na seção de arquivos estáticos:
*   **URL:** [Dados Abertos - Arquivos Estáticos](https://dadosabertos.camara.leg.br/swagger/api.html?tab=staticfile)

## 📊 Fluxo de Dados

1.  **Dados Brutos**: `data/raw/` deve conter os datasets JSON iniciais baixados da fonte acima.
2.  **ETL**: `filtrar_dados.py` limpa os metadados e une os autores.
3.  **Intermediário**: A lista filtrada é salva em `data/interim/`.
4.  **Extração**: `extrair_texto.py` baixa os PDFs e extrai o texto.
5.  **Processado**: O JSON final com o texto limpo é salvo em `data/processed/`.

## 📝 Licença

[Especificar Licença, ex: MIT]