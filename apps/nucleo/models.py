from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AnoLetivo(models.Model):
    """
    Ex.: 2025/2026
    """
    nome = models.CharField("Nome", max_length=9, unique=True)  # "2025/2026"
    data_inicio = models.DateField("Data de inicio", null=True, blank=True)
    data_fim = models.DateField("Data de fim", null=True, blank=True)

    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Ano letivo"
        verbose_name_plural = "Anos letivos"
        ordering = ["-nome"]

    def __str__(self) -> str:
        return self.nome


class Turma(models.Model):
    class TipoContexto(models.TextChoices):
        ENSINO_BASICO_TIC = "ENSINO_BASICO_TIC", "Ensino Basico (TIC)"
        ENSINO_PROFISSIONAL_UFCD = "ENSINO_PROFISSIONAL_UFCD", "Ensino Profissional (UFCD)"

    class Ciclo(models.TextChoices):
        CICLO_2 = "2C", "2º Ciclo"
        CICLO_3 = "3C", "3º Ciclo"
        SECUNDARIO = "SEC", "Ensino Secundario"
        NAO_APLICA = "NA", "Nao aplica"


    ano_letivo = models.ForeignKey(
        AnoLetivo,
        on_delete=models.PROTECT,
        related_name="turmas",
        verbose_name="Ano letivo",
    )

    nome = models.CharField("Nome da turma", max_length=50)  # ex.: "7A", "8D", "PROFIJ2-A"

    tipo_contexto = models.CharField(
        "Tipo de contexto",
        max_length=30,
        choices=TipoContexto.choices,
        default=TipoContexto.ENSINO_BASICO_TIC,
    )

    ciclo = models.CharField(
        "Ciclo",
        max_length=3,
        choices=Ciclo.choices,
        default=Ciclo.NAO_APLICA,
    )
    ano_escolaridade = models.PositiveSmallIntegerField("Ano de escolaridade", null=True, blank=True)  # 5..9

    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="turmas",
        verbose_name="Professor",
        null=True,
        blank=True,
    )

    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Turma"
        verbose_name_plural = "Turmas"
        unique_together = [("ano_letivo", "nome")]
        ordering = ["nome"]

    def clean(self):
        super().clean()

        if self.tipo_contexto == Turma.TipoContexto.ENSINO_BASICO_TIC:
            # para TIC, ciclo e ano_escolaridade devem fazer sentido
            if self.ciclo not in (Turma.Ciclo.CICLO_2, Turma.Ciclo.CICLO_3, Turma.Ciclo.SECUNDARIO):
                raise ValidationError({"ciclo": "Para TIC, o ciclo deve ser 2º, 3º ou Secundario."})
            if self.ano_escolaridade is None:
                raise ValidationError({"ano_escolaridade": "Para TIC, informe o ano (5 a 12)."})
            if not (5 <= self.ano_escolaridade <= 9):
                raise ValidationError({"ano_escolaridade": "Para TIC, o ano deve estar entre 5 e 12."})
        else:
            # profissional: nao obrigar ciclo/ano_escolaridade
            pass

    def __str__(self) -> str:
        return f"{self.nome} ({self.ano_letivo})"


class Aluno(models.Model):
    turma = models.ForeignKey(Turma, on_delete=models.PROTECT, related_name="alunos", verbose_name="Turma")
   #numero = models.CharField("Numero", max_length=10, null=True, blank=True)  # pode ser vazio no profissional
    numero = models.PositiveIntegerField("Numero", null=True, blank=True)
    nome_completo = models.CharField("Nome completo", max_length=150)

    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"
        ordering = ["turma__nome", "nome_completo"]
        unique_together = [("turma", "numero", "nome_completo")]

    def __str__(self) -> str:
#         if self.numero:
#             return f"{self.numero} - {self.nome_completo}"
        if self.numero is not None:
            return f"{self.numero} - {self.nome_completo}"
        return self.nome_completo
