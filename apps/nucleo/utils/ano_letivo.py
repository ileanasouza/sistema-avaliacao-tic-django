from __future__ import annotations
from datetime import date

def ano_letivo_atual(today: date | None = None) -> tuple[int, int]:
    """
    Regra Portugal: ano letivo inicia em setembro.
    - Se mês >= 9: ano_inicio = ano corrente
    - Caso contrário: ano_inicio = ano corrente - 1
    """
    today = today or date.today()
    if today.month >= 9:
        start = today.year
    else:
        start = today.year - 1
    return start, start + 1


def choices_anos_letivos(qtd_futuros: int = 3):
    """
    Retorna choices no formato:
    [('2025/2026','2025/2026'), ('2026/2027','2026/2027'), ...]
    Inclui o atual + qtd_futuros.
    """
    start, _ = ano_letivo_atual()
    choices = []
    for i in range(0, qtd_futuros + 1):  # 0 = atual, +3 futuros
        a = start + i
        b = a + 1
        s = f"{a:04d}/{b:04d}"
        choices.append((s, s))
    return choices


