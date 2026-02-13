from __future__ import annotations

from decimal import Decimal


def mencao_qualitativa_tic(nota_0a100 Decimal) - str
    
    Regra (ensino basico TIC)
      50  - Insuficiente
      70  - Suficiente
      90  - Bom
      =90 - Muito Bom
    
    if nota_0a100  Decimal(50)
        return Insuficiente
    if nota_0a100  Decimal(70)
        return Suficiente
    if nota_0a100  Decimal(90)
        return Bom
    return Muito Bom


def nivel_sge_tic(nota_0a100 Decimal) - int
    
    Regra (ensino basico TIC) conforme tua planilha
      20  - 1
      50  - 2
      70  - 3
      90  - 4
      =90 - 5
    
    if nota_0a100  Decimal(20)
        return 1
    if nota_0a100  Decimal(50)
        return 2
    if nota_0a100  Decimal(70)
        return 3
    if nota_0a100  Decimal(90)
        return 4
    return 5
