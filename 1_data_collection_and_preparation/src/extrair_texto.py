# -*- coding: utf-8 -*-
"""
Módulo de Extração e Limpeza de Texto (NLP).

Este script realiza o download dos documentos PDF (Inteiro Teor) das proposições,
extrai o conteúdo textual e aplica heurísticas avançadas de limpeza para
remover ruídos comuns em documentos legislativos.

Funcionalidades Principais:
1. Download de PDF via URL.
2. Extração de blocos de texto preservando layout básico.
3. Detecção e remoção de Cabeçalhos e Rodapés baseada em repetição visual.
4. Remoção de numeração de páginas e carimbos institucionais.
5. Identificação e corte (opcional) de seções de ANEXOS.

Saída:
    Gera um novo JSON enriquecido com o campo 'textoInteiroTeorLimpo'.
"""

import json
import re
import requests
import fitz  # PyMuPDF
from collections import Counter
from typing import Optional, List, Tuple, Set

try:
    import config
except ImportError:
    from src import config

# ------------------------------- 
# CONSTANTES E CONFIGURAÇÕES
# ------------------------------- 

INPUT_FILE  = config.FILTERED_FILE
OUTPUT_FILE = config.FINAL_FILE
# Cabeçalho HTTP para simular um navegador e evitar bloqueios
HEADERS = {"User-Agent": "Mozilla/5.0"}

# --- Parâmetros da Heurística de Limpeza ---

# Define se devemos cortar o texto quando encontrar um ANEXO
REMOVE_FROM_ANEXO = False

# Áreas da página para análise de cabeçalho (topo) e rodapé (base)
# Ex: 0.15 significa os 15% superiores/inferiores da altura da página
TOP_FRAC = 0.15
BOTTOM_FRAC = 0.15

# Limiar de repetição: Se um texto aparece na mesma posição em X% das páginas,
# ele é considerado cabeçalho/rodapé e removido. (0.40 = 40%)
REPEAT_THRESHOLD = 0.40

# Configurações específicas para detecção de Anexos
TOP_FRAC_ANNEX = 0.30          # Título do anexo deve estar no terço superior
STRICT_UPPERCASE_ANNEX = True  # Título deve estar estritamente em CAIXA ALTA

# Ativa logs detalhados para depuração
DEBUG_LOG = False

# Lista de termos "boilerplate" (institucionais) que devem ser removidos
# independentemente de sua posição na página (busca insensível a maiúsculas/minúsculas).
BANNED_SUBSTRS = [
    "câmara dos deputados",
    "gabinete do deputado",
    "gabinete do deputado federal",
    "assinado eletronicamente",
    "para verificar a assinatura",
    "@camara.leg.br",
    "praça dos três poderes",
    "cep 70160",
    "mesa",
    "deputado federal",
    "projeto de lei n",
    "projeto de lei nº",
    "gabinete",
]


# ------------------------
# UTILITÁRIOS DE TEXTO
# ------------------------

def normalize_line(s: str) -> str:
    """
    Remove ruídos visuais como linhas pontilhadas longas e normaliza espaços.
    Exemplo: "......." é transformado em " ".
    """
    # Remove sequências de 3 ou mais caracteres de pontuação/marcadores
    s = re.sub(r'[_\'\.\·•●◦▪▫⋅∙…]{3,}', ' ', s)
    # Colapsa múltiplos espaços em um único
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def is_page_number(line: str) -> bool:
    """
    Verifica se a linha é apenas uma numeração de página.
    Suporta formatos como: "3", "Página 3", "3/25", "Página 3 de 10".
    """
    t = line.strip()
    # Apenas números (ex: "3")
    if re.fullmatch(r'\d{1,4}', t):
        return True
    # Formato "Página X" ou "Página X de Y"
    if re.fullmatch(r'(?i)p[áa]gina\s+\d{1,4}(\s+de\s+\d{1,4})?', t):
        return True
    # Formato "X/Y"
    if re.fullmatch(r'\d{1,4}\s*/\s*\d{1,4}', t):
        return True
    return False

def should_remove_global(line: str) -> bool:
    """
    Decide se uma linha deve ser removida baseada em seu conteúdo (Lista Negra).
    Remove assinaturas digitais, endereços, carimbos de protocolo e identificadores de PL.
    """
    if not line:
        return False
    l = line.casefold()

    # Verifica se contém algum termo banido
    if any(b in l for b in BANNED_SUBSTRS):
        return True

    # Remove códigos de protocolo internos (estilo "*CD257150518000*")
    if re.search(r'(\*|^)\s*cd\d{6,}\s*(\*|$)', l):
        return True

    # Remove identificação curta do PL (ex: "PL 1234/2025") quando aparece solta no texto
    if re.fullmatch(r'(?i)pl\s*n?`\.IBLE?s*\d{1,6}[/-]\d{2,4}', line.strip()):
        return True

    return False


# ------------------------
# EXTRAÇÃO E ANÁLISE ESPACIAL
# ------------------------

def extract_blocks(page: fitz.Page) -> List[Tuple[Tuple[float, float, float, float], str]]:
    """
    Extrai blocos de texto e suas coordenadas (Bounding Box) de uma página.
    
    Retorna:
        Lista de tuplas no formato ((x0, y0, x1, y1), texto_normalizado)
    """
    blocks = page.get_text("blocks")
    out = []
    for (x0, y0, x1, y1, text, *_rest) in blocks:
        for line in text.splitlines():
            ln = normalize_line(line)
            if ln:
                out.append(((x0, y0, x1, y1), ln))
    return out

def detect_headers_footers(pages_lines: List[List], heights: List[float]) -> Tuple[Set[str], Set[str]]:
    """
    Identifica cabeçalhos e rodapés baseando-se na repetição de texto entre páginas.
    
    Lógica: Se um texto aparece no topo (ou base) de muitas páginas (definido por REPEAT_THRESHOLD),
    ele é classificado como cabeçalho (ou rodapé) e será removido de todas as páginas.
    """
    top_c = Counter()
    bot_c = Counter()
    n = len(pages_lines)

    for i, lines in enumerate(pages_lines):
        h = heights[i]
        top_y = h * TOP_FRAC
        bot_y = h * (1 - BOTTOM_FRAC)
        st = set()
        sb = set()
        for (bbox, line) in lines:
            y0 = bbox[1]
            # Coleta candidatos no topo (exceto números de página que variam a cada página)
            if y0 <= top_y and not is_page_number(line):
                st.add(line)
            # Coleta candidatos no rodapé
            if y0 >= bot_y:
                sb.add(line)
        top_c.update(st)
        bot_c.update(sb)

    # Filtra apenas os textos que aparecem em X% das páginas (limiar definido)
    top_rep = {l for l, c in top_c.items() if c >= REPEAT_THRESHOLD * n}
    bot_rep = {l for l, c in bot_c.items() if c >= REPEAT_THRESHOLD * n}
    return top_rep, bot_rep


# ------------------------
# DETECÇÃO DE ANEXOS
# ------------------------

def looks_like_annex_title(line: str) -> bool:
    """
    Verifica se uma linha parece ser o título de um Anexo Legislativo.
    Critérios: Começar com 'ANEXO', ser curto, e estar majoritariamente em maiúsculas.
    """
    s = line.strip()

    # Regex para identificar "ANEXO I", "ANEXO ÚNICO", etc.
    if not re.match(r'^ANEXO(\s+[IVXLCDM0-9]+)?(\s*[-–—:].*)?$', s):
        return False

    # Evita falsos positivos (frases longas ou terminadas em ponto final)
    if s.endswith('.') or len(s.split()) > 10:
        return False

    # Verifica a proporção de letras maiúsculas
    letters = [c for c in s if c.isalpha()]
    if letters:
        upper_ratio = sum(c.isupper() for c in letters) / len(letters)
        if upper_ratio < 0.90:
            return False

    # Verifica se deve ser estritamente maiúsculo
    if STRICT_UPPERCASE_ANNEX and s != s.upper():
        return False

    return True

def find_annex_start_page(pages_lines, heights) -> Optional[int]:
    """
    Localiza a página onde o Anexo começa.
    Geralmente anexos aparecem apenas no final do documento.
    """
    candidates = []
    n_pages = len(pages_lines)

    for i, lines in enumerate(pages_lines):
        h = heights[i]
        top_limit = h * TOP_FRAC_ANNEX
        for (bbox, line) in lines:
            y0 = bbox[1]
            if y0 <= top_limit and looks_like_annex_title(line):
                candidates.append(i)
                break 

    if not candidates:
        return None

    # Assume que o anexo real é o último encontrado e deve estar na segunda metade do documento
    start = candidates[-1]
    if start < n_pages // 2:
        return None

    return start


# ------------------------
# EXTRAÇÃO PRINCIPAL (CORE)
# ------------------------

def get_pdf_text_clean_from_doc(doc) -> Optional[str]:
    """
    Orquestra a extração e limpeza de um documento PDF já aberto.
    """
    pages_lines, heights = [], []

    # 1. Extração bruta de blocos com coordenadas
    for p in doc:
        heights.append(p.rect.height)
        pages_lines.append(extract_blocks(p))

    # 2. Identificação de padrões repetitivos (Cabeçalhos/Rodapés)
    top_rep, bot_rep = detect_headers_footers(pages_lines, heights)

    # 3. Detecção de corte de anexo (se habilitado)
    annex_start = find_annex_start_page(pages_lines, heights) if REMOVE_FROM_ANEXO else None
    if DEBUG_LOG and annex_start is not None:
        print(f"[INFO] ANEXO detectado na página {annex_start + 1}. Cortando conteúdo posterior.")

    cleaned_pages: List[str] = []

    # 4. Filtragem linha a linha
    for i, lines in enumerate(pages_lines):

        # Se detectou início de anexo, para a extração aqui
        if annex_start is not None and i >= annex_start:
            break

        h = heights[i]
        top_y = h * TOP_FRAC
        bottom_y = h * (1 - BOTTOM_FRAC)

        keep = []
        for (bbox, line) in lines:
            y0 = bbox[1]

            # Aplica regras de exclusão
            if should_remove_global(line): continue
            if line in top_rep and y0 <= top_y: continue
            if line in bot_rep and y0 >= bottom_y: continue
            if is_page_number(line) and (y0 <= top_y or y0 >= bottom_y): continue

            keep.append(line)

        page_text = " ".join(keep).strip()
        if page_text:
            cleaned_pages.append(page_text)

    text = "\n".join(cleaned_pages).strip()
    return text or None

def extract_pdf_from_url(url: str) -> Optional[str]:
    """Baixa o PDF da URL e inicia o processamento."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=50)
        r.raise_for_status()
        doc = fitz.open(stream=r.content, filetype="pdf")
        return get_pdf_text_clean_from_doc(doc)
    except Exception as e:
        if DEBUG_LOG:
            print(f"[ERRO] Falha ao baixar/processar PDF: {e}")
        return None


# ------------------------
# EXECUÇÃO DO SCRIPT
# ------------------------
if __name__ == "__main__":
    print(f"Lendo arquivo de entrada: {INPUT_FILE}")
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[FATAL] Arquivo {INPUT_FILE} não encontrado. Execute 'filtrar_dados.py' primeiro.")
        exit(1)

    if isinstance(data, dict) and "dados" in data:
        # Suporte ao novo padrão definido no projeto
        proposicoes = data["dados"]
    elif isinstance(data, dict) and "proposicoes" in data:
        # Suporte legado para estrutura antiga
        proposicoes = data["proposicoes"]
    else:
        raise ValueError("JSON não está no formato esperado (chaves 'dados' ou 'proposicoes')")

    total = len(proposicoes)
    print(f"Total de proposições para processar: {total}")

    for idx, prop in enumerate(proposicoes, start=1):
        if not isinstance(prop, dict): continue

        url = prop.get("urlInteiroTeor")
        # Log de progresso simples
        print(f"[{idx}/{total}] Processando ID {prop.get('id')}...")

        if url:
            texto_limpo = extract_pdf_from_url(url)
            prop["textoInteiroTeorLimpo"] = texto_limpo
        else:
            prop["textoInteiroTeorLimpo"] = None

    # Salva mantendo a estrutura compatível
    out = {"dados": proposicoes}

    print(f"Salvando resultados em: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("✅ Processamento finalizado com sucesso!")
