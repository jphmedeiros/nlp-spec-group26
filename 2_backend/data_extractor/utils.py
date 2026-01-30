import re
import collections
from typing import List, Tuple


# Minimal NLTK stopwords lazy loader to avoid heavy imports at module import time
_stop_words = None


def _load_stopwords() -> set:
    """
    Lazily load NLTK Portuguese stopwords. Downloads the package if necessary.

    Returns:
        A set with Portuguese stopwords.
    """
    global _stop_words
    if _stop_words is None:
        try:
            from nltk.corpus import stopwords
            _stop_words = set(stopwords.words('portuguese'))
        except Exception:
            import nltk
            nltk.download('stopwords')
            from nltk.corpus import stopwords
            _stop_words = set(stopwords.words('portuguese'))
    return _stop_words


def generate_word_cloud(proposition_id: int, full_text: str) -> List[Tuple[int, str, int]]:
    """
    Generate a simple word frequency list for the provided text.

    Args:
        proposition_id: Identifier of the proposition.
        full_text: Full cleaned text of the proposition.

    Returns:
        A list of tuples (proposition_id, word, frequency).
    """
    stop_words = _load_stopwords()
    text = (full_text or "").lower()
    text = re.sub(r"[^\w\s]", "", text)
    words = text.split()
    filtered_words = [w for w in words if w not in stop_words]
    word_counts = collections.Counter(filtered_words)
    return [(int(proposition_id), word, count) for word, count in word_counts.items()]

