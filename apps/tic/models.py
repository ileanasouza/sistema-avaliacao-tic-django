from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.nucleo.models import Turma, Aluno


# -----------------------------
# Choices
# -----------------------------
class Periodo(models.IntegerChoices):
    P1 = 1, "1.º Período"
    P2 = 2, "2.º Período"
    P3 = 3, "3.º Período"


# -----------------------------
# Boletim por período
# -----------------------------
class BoletimPeriodoTIC(models.Model):
    class Estado(models.TextChoices):
        ABERTO = "ABERTO", "Aberto"
        FECHADO = "FECHADO", "Fechado"

    turma = models.ForeignKey(
        Turma,
        on_delete=models.PROTECT,
        related_name="boletins_tic",
        verbose_name="Turma",
    )
    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.PROTECT,
        related_name="boletins_tic",
        verbose_name="Aluno",
    )

    periodo = models.PositiveSmallIntegerField(
        "Período",
        choices=Periodo.choices,
    )

    estado = models.CharField(
        "Estado",
        max_length=10,
        choices=Estado.choices,
        default=Estado.ABERTO,
    )

    # Autoavaliação do aluno (1 a 5) por período
    autoavaliacao_nivel = models.PositiveSmallIntegerField(
        "Autoavaliação (nível 1 a 5)",
        null=True,
        blank=True,
    )

    # -----------------------------
    # Resultados calculados (somente consulta no admin)
    # -----------------------------
    media_cognitiva_100 = models.DecimalField(
        "Média cognitiva (0 a 100)",
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    nota_cognitiva_80 = models.DecimalField(
        "Nota cognitiva (0 a 80)",
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    nota_atitudes_20 = models.DecimalField(
        "Atitudes (0 a 20)",
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    nota_final_100 = models.DecimalField(
        "Nota final (0 a 100)",
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    mencao_qualitativa = models.CharField(
        "Menção qualitativa",
        max_length=20,
        null=True,
        blank=True,
    )

    nivel_sge = models.PositiveSmallIntegerField(
        "Nível SGE (1 a 5)",
        null=True,
        blank=True,
    )

    observacao = models.TextField(
        "Observação",
        null=True,
        blank=True,
    )

    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Boletim TIC (período)"
        verbose_name_plural = "Boletins TIC (períodos)"
        unique_together = [("turma", "aluno", "periodo")]
        indexes = [
            models.Index(fields=["turma", "periodo"]),
            models.Index(fields=["aluno", "periodo"]),
        ]
        ordering = ["turma__nome", "periodo", "aluno__nome_completo"]

    def clean(self):
        super().clean()

        # garante coerência aluno↔turma
        if self.turma_id and self.aluno_id:
            # se o model Aluno tiver FK turma:
            if getattr(self.aluno, "turma_id", None) != self.turma_id:
                raise ValidationError("O aluno não pertence a esta turma.")

        # período já é limitado por choices, mas validamos por segurança
        if self.periodo not in Periodo.values:
            raise ValidationError({"periodo": "Período deve ser 1, 2 ou 3."})

        if self.autoavaliacao_nivel is not None and not (1 <= self.autoavaliacao_nivel <= 5):
            raise ValidationError({"autoavaliacao_nivel": "Autoavaliação deve ser um nível de 1 a 5."})

    def __str__(self) -> str:
        return f"{self.turma} - {Periodo(self.periodo).label} - {self.aluno}"


# -----------------------------
# Atitudes por período
# -----------------------------
class AtitudesPeriodoTIC(models.Model):
    """
    Guarda atitudes em PONTOS (tetos fixos), somando até 20.
    """

    # ✅ Padronizado para signals/services: instance.boletim
    boletim = models.OneToOneField(
        BoletimPeriodoTIC,
        on_delete=models.CASCADE,
        related_name="atitudes",
        verbose_name="Boletim TIC (período)",
    )

    responsabilidade_integridade = models.DecimalField(
        "Responsabilidade e integridade (0-3)",
        max_digits=4,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    excelencia_exigencia = models.DecimalField(
        "Excelência e exigência (0-6)",
        max_digits=4,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    curiosidade_reflexao_inovacao = models.DecimalField(
        "Curiosidade, reflexão e inovação (0-2)",
        max_digits=4,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    cidadania_participacao = models.DecimalField(
        "Cidadania e participação (0-4)",
        max_digits=4,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    liberdade = models.DecimalField(
        "Liberdade (0-5)",
        max_digits=4,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Atitudes TIC (período)"
        verbose_name_plural = "Atitudes TIC (períodos)"

    def total_atitudes_20(self) -> Decimal:
        return (
            self.responsabilidade_integridade
            + self.excelencia_exigencia
            + self.curiosidade_reflexao_inovacao
            + self.cidadania_participacao
            + self.liberdade
        )

    def clean(self):
        super().clean()

        checks = [
            ("responsabilidade_integridade", self.responsabilidade_integridade, Decimal("0.00"), Decimal("3.00")),
            ("excelencia_exigencia", self.excelencia_exigencia, Decimal("0.00"), Decimal("6.00")),
            ("curiosidade_reflexao_inovacao", self.curiosidade_reflexao_inovacao, Decimal("0.00"), Decimal("2.00")),
            ("cidadania_participacao", self.cidadania_participacao, Decimal("0.00"), Decimal("4.00")),
            ("liberdade", self.liberdade, Decimal("0.00"), Decimal("5.00")),
        ]

        for campo, valor, minimo, maximo in checks:
            if valor is None:
                raise ValidationError({campo: "Este campo é obrigatório."})
            if valor < minimo or valor > maximo:
                raise ValidationError({campo: f"Valor deve estar entre {minimo} e {maximo}."})

        total = self.total_atitudes_20()
        if total < Decimal("0.00") or total > Decimal("20.00"):
            raise ValidationError("A soma total de atitudes deve estar entre 0 e 20.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Atitudes - {self.boletim}"


# -----------------------------
# Avaliações cognitivas (definição)
# -----------------------------
class AvaliacaoCognitivaTIC(models.Model):
    """
    Avaliações do domínio cognitivo (testes/trabalhos), escala 0..100,
    com peso (percentual) para o período.
    Depois o cálculo converte para 0..80 no boletim.
    """

    turma = models.ForeignKey(
        Turma,
        on_delete=models.PROTECT,
        related_name="avaliacoes_tic",
        verbose_name="Turma",
    )

    periodo = models.PositiveSmallIntegerField(
        "Período",
        choices=Periodo.choices,
    )

    nome = models.CharField("Nome da avaliação", max_length=80)  # ex: "1º Trabalho"
    peso_percentual = models.DecimalField("Peso percentual (0-100)", max_digits=6, decimal_places=2)

    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Avaliação cognitiva TIC"
        verbose_name_plural = "Avaliações cognitivas TIC"
        unique_together = [("turma", "periodo", "nome")]
        ordering = ["turma__nome", "periodo", "nome"]

    def clean(self):
        super().clean()

        if self.periodo not in Periodo.values:
            raise ValidationError({"periodo": "Período deve ser 1, 2 ou 3."})

        if self.peso_percentual is None:
            raise ValidationError({"peso_percentual": "Este campo é obrigatório."})

        if self.peso_percentual <= Decimal("0.00") or self.peso_percentual > Decimal("100.00"):
            raise ValidationError({"peso_percentual": "Peso deve estar entre 0 e 100 (excluindo 0)."})


    def __str__(self):
        return f"{self.turma} | {Periodo(self.periodo).label} | {self.nome} ({self.peso_percentual}%)"


# -----------------------------
# Notas das avaliações cognitivas
# -----------------------------
class NotaAvaliacaoCognitivaTIC(models.Model):
    avaliacao = models.ForeignKey(
        AvaliacaoCognitivaTIC,
        on_delete=models.PROTECT,
        related_name="notas",
        verbose_name="Avaliação",
    )
    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.PROTECT,
        related_name="notas_avaliacoes_tic",
        verbose_name="Aluno",
    )

    nota_0a100 = models.DecimalField("Nota (0 a 100)", max_digits=6, decimal_places=2)

    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Nota avaliação cognitiva TIC"
        verbose_name_plural = "Notas avaliações cognitivas TIC"
        unique_together = [("avaliacao", "aluno")]

    def clean(self):
        super().clean()

        if self.nota_0a100 is None:
            raise ValidationError({"nota_0a100": "Este campo é obrigatório."})

        if self.nota_0a100 < Decimal("0.00") or self.nota_0a100 > Decimal("100.00"):
            raise ValidationError({"nota_0a100": "A nota deve estar entre 0 e 100."})

        # ✅ Regra importante: aluno tem que estar na turma da avaliação
        if self.avaliacao_id and self.aluno_id:
            aluno_turma_id = getattr(self.aluno, "turma_id", None)
            if aluno_turma_id is not None and aluno_turma_id != self.avaliacao.turma_id:
                raise ValidationError("O aluno não pertence à turma desta avaliação.")

    def __str__(self):
        return f"{self.aluno} - {self.avaliacao} = {self.nota_0a100}"


