from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from apps.tic.models import (
    BoletimPeriodoTIC,
    AtitudesPeriodoTIC,
    NotaAvaliacaoCognitivaTIC,
)


# -------------------------
# Tipos e helpers
# -------------------------
@dataclass(frozen=True)
class ResultadoTIC:
    media_cognitiva_100: Decimal      # 0..100 (média ponderada)
    nota_cognitiva_80: Decimal        # 0..80
    nota_atitudes_20: Decimal         # 0..20
    nota_final_100: Decimal           # 0..100
    mencao_qualitativa: str
    nivel_sge: int


def _d(x) -> Decimal:
    """Converte com segurança (None -> 0)."""
    if x is None:
        return Decimal("0")
    return Decimal(str(x))


def _round2(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _mencao_qualitativa(nota_final_0_100: Decimal) -> str:
    if nota_final_0_100 < Decimal("50"):
        return "Insuficiente"
    if nota_final_0_100 < Decimal("70"):
        return "Suficiente"
    if nota_final_0_100 < Decimal("90"):
        return "Bom"
    return "Muito Bom"


def _nivel_1a5(nota_final_0_100: Decimal) -> int:
    if nota_final_0_100 < Decimal("20"):
        return 1
    if nota_final_0_100 < Decimal("50"):
        return 2
    if nota_final_0_100 < Decimal("70"):
        return 3
    if nota_final_0_100 < Decimal("90"):
        return 4
    return 5


# -------------------------
# Cálculo do Boletim TIC
# -------------------------
def calcular_resultado_boletim(boletim: BoletimPeriodoTIC) -> ResultadoTIC:
    """
    Regras TIC (ensino básico/secundário):
      - Cognitivo: média ponderada (0..100) e depois * 0.80 => 0..80
      - Atitudes: soma de 5 dimensões, com tetos fixos, total 0..20
      - Nota final (0..100) = cognitivo(0..80) + atitudes(0..20)
    """

    # 1) Cognitivo (média 0..100 e nota 0..80)
    notas_qs = (
        NotaAvaliacaoCognitivaTIC.objects
        .select_related("avaliacao")
        .filter(
            aluno_id=boletim.aluno_id,
            avaliacao__turma_id=boletim.turma_id,
            avaliacao__periodo=boletim.periodo,
        )
    )

    total_peso = Decimal("0")
    soma_ponderada = Decimal("0")

    for n in notas_qs:
        peso = _d(n.avaliacao.peso_percentual)  # ex.: 50
        nota = _d(n.nota_0a100)                 # 0..100
        total_peso += peso
        soma_ponderada += (nota * peso)

    media_cognitiva_100 = (soma_ponderada / total_peso) if total_peso > 0 else Decimal("0")
    media_cognitiva_100 = _round2(media_cognitiva_100)

    nota_cognitiva_80 = _round2(media_cognitiva_100 * Decimal("0.80"))  # 0..80

    # 2) Atitudes (0..20) com tetos fixos
    atitudes = AtitudesPeriodoTIC.objects.filter(boletim=boletim).first()

    TETO_RESP = Decimal("3")
    TETO_EXIG = Decimal("6")
    TETO_CURI = Decimal("2")
    TETO_CIDA = Decimal("4")
    TETO_LIBE = Decimal("5")

    if atitudes:
        resp = min(_d(atitudes.responsabilidade_integridade), TETO_RESP)
        exig = min(_d(atitudes.excelencia_exigencia), TETO_EXIG)
        curi = min(_d(atitudes.curiosidade_reflexao_inovacao), TETO_CURI)
        cida = min(_d(atitudes.cidadania_participacao), TETO_CIDA)
        libe = min(_d(atitudes.liberdade), TETO_LIBE)

        nota_atitudes_20 = resp + exig + curi + cida + libe
    else:
        nota_atitudes_20 = Decimal("0")

    nota_atitudes_20 = _round2(nota_atitudes_20)

    # 3) Nota final (0..100)
    nota_final_100 = _round2(nota_cognitiva_80 + nota_atitudes_20)

    return ResultadoTIC(
        media_cognitiva_100=media_cognitiva_100,
        nota_cognitiva_80=nota_cognitiva_80,
        nota_atitudes_20=nota_atitudes_20,
        nota_final_100=nota_final_100,
        mencao_qualitativa=_mencao_qualitativa(nota_final_100),
        nivel_sge=_nivel_1a5(nota_final_100),
    )


# -------------------------
# Persistência (sem recursão)
# -------------------------
@transaction.atomic
def recalcular_boletim(boletim_id: int) -> None:
    boletim = (
        BoletimPeriodoTIC.objects
        .select_related("turma", "aluno")
        .get(pk=boletim_id)
    )

    r = calcular_resultado_boletim(boletim)

    # ✅ Update direto: NÃO chama save() e NÃO dispara signals.
    BoletimPeriodoTIC.objects.filter(pk=boletim.pk).update(
        media_cognitiva_100=r.media_cognitiva_100,
        nota_cognitiva_80=r.nota_cognitiva_80,
        nota_atitudes_20=r.nota_atitudes_20,
        nota_final_100=r.nota_final_100,
        mencao_qualitativa=r.mencao_qualitativa,
        nivel_sge=r.nivel_sge,
    )


@transaction.atomic
def garantir_e_recalcular_boletim(turma_id: int, aluno_id: int, periodo: int) -> None:
    boletim, _ = BoletimPeriodoTIC.objects.get_or_create(
        turma_id=turma_id,
        aluno_id=aluno_id,
        periodo=periodo,
        defaults={},
    )
    recalcular_boletim(boletim_id=boletim.id)


def agendar_recalculo_boletim(boletim_id: int) -> None:
    """
    ✅ Use isto dentro de signals/admin: só recalcula depois do commit.
    Evita erro de transação / comportamento estranho no admin.
    """
    transaction.on_commit(lambda: recalcular_boletim(boletim_id))


