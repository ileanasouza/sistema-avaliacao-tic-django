from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.tic.models import (
    NotaAvaliacaoCognitivaTIC,
    AtitudesPeriodoTIC,
    AvaliacaoCognitivaTIC,
)
from apps.tic.services.tic_calculator import garantir_e_recalcular_boletim


def _recalcular(turma_id: int, aluno_id: int, periodo: int) -> None:
    """
    Recalcula o boletim após o commit da transação.
    Evita erros no Admin (objeto ainda não commitado) e comportamentos inconsistentes.
    """
    transaction.on_commit(
        lambda: garantir_e_recalcular_boletim(
            turma_id=turma_id,
            aluno_id=aluno_id,
            periodo=periodo,
        )
    )


# -------------------------
# NOTAS COGNITIVAS
# -------------------------
@receiver(post_save, sender=NotaAvaliacaoCognitivaTIC)
def recalcular_quando_salvar_nota(sender, instance: NotaAvaliacaoCognitivaTIC, **kwargs):
    _recalcular(
        turma_id=instance.avaliacao.turma_id,
        aluno_id=instance.aluno_id,
        periodo=instance.avaliacao.periodo,
    )


@receiver(post_delete, sender=NotaAvaliacaoCognitivaTIC)
def recalcular_quando_apagar_nota(sender, instance: NotaAvaliacaoCognitivaTIC, **kwargs):
    _recalcular(
        turma_id=instance.avaliacao.turma_id,
        aluno_id=instance.aluno_id,
        periodo=instance.avaliacao.periodo,
    )


# -------------------------
# ATITUDES
# -------------------------
@receiver(post_save, sender=AtitudesPeriodoTIC)
def recalcular_quando_salvar_atitudes(sender, instance: AtitudesPeriodoTIC, **kwargs):
    boletim = instance.boletim
    _recalcular(
        turma_id=boletim.turma_id,
        aluno_id=boletim.aluno_id,
        periodo=boletim.periodo,
    )


@receiver(post_delete, sender=AtitudesPeriodoTIC)
def recalcular_quando_apagar_atitudes(sender, instance: AtitudesPeriodoTIC, **kwargs):
    boletim = instance.boletim
    _recalcular(
        turma_id=boletim.turma_id,
        aluno_id=boletim.aluno_id,
        periodo=boletim.periodo,
    )


# -------------------------
# AVALIAÇÃO COGNITIVA (se alterar peso/período/nome)
# -------------------------
@receiver(post_save, sender=AvaliacaoCognitivaTIC)
def recalcular_quando_mudar_avaliacao(sender, instance: AvaliacaoCognitivaTIC, **kwargs):
    """
    Se o professor alterar a Avaliação (ex.: peso), recalcula os boletins
    dos alunos que têm nota nessa avaliação.
    """
    aluno_ids = (
        NotaAvaliacaoCognitivaTIC.objects.filter(avaliacao=instance)
        .values_list("aluno_id", flat=True)
        .distinct()
    )

    for aluno_id in aluno_ids:
        _recalcular(
            turma_id=instance.turma_id,
            aluno_id=aluno_id,
            periodo=instance.periodo,
        )

