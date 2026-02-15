from __future__ import annotations

from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


# =========================================================
# Helpers: Ano letivo atual (Portugal) + próximos 3
# =========================================================

def _ano_letivo_atual(today: date | None = None) -> tuple[int, int]:
    """
    Regra (Portugal): o ano letivo inicia em setembro.
    - Se month >= 9: start = ano corrente
    - Se month < 9: start = ano corrente - 1
    """
    today = today or date.today()
    if today.month >= 9:
        start = today.year
    else:
        start = today.year - 1
    return start, start + 1


def _anos_letivos_permitidos(qtd_futuros: int = 3) -> list[str]:
    """
    Retorna lista com o ano letivo atual + próximos 3, no formato AAAA/AAAA.
    Ex.: ['2025/2026', '2026/2027', '2027/2028', '2028/2029']
    """
    start, _ = _ano_letivo_atual()
    out: list[str] = []
    for i in range(0, qtd_futuros + 1):
        a = start + i
        b = a + 1
        out.append(f"{a:04d}/{b:04d}")
    return out


def _validar_formato_ano_letivo(valor: str) -> None:
    """
    Garante formato exato AAAA/AAAA e coerência do intervalo (ex.: 2025/2026).
    """
    if not isinstance(valor, str):
        raise ValidationError("Ano letivo inválido.")
    if len(valor) != 9 or valor[4] != "/":
        raise ValidationError("Use o formato AAAA/AAAA (ex.: 2025/2026).")

    parte_a = valor[:4]
    parte_b = valor[5:]

    if not (parte_a.isdigit() and parte_b.isdigit()):
        raise ValidationError("Use o formato AAAA/AAAA (ex.: 2025/2026).")

    a = int(parte_a)
    b = int(parte_b)
    if b != a + 1:
        raise ValidationError(
            "Ano letivo inválido: o segundo ano deve ser o primeiro + 1 (ex.: 2025/2026)."
        )


# =========================================================
# MODELS
# =========================================================

class AnoLetivo(models.Model):
    """
    Ex.: 2025/2026
    Regras:
      - nome deve estar no formato AAAA/AAAA
      - nome deve ser um dos anos permitidos (atual + próximos 3)
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

    def clean(self):
        super().clean()

        if self.nome:
            _validar_formato_ano_letivo(self.nome)

        permitidos = set(_anos_letivos_permitidos(3))
        if self.nome not in permitidos:
            raise ValidationError({
                "nome": (
                    "Ano letivo não permitido. "
                    f"Selecione apenas: {', '.join(sorted(permitidos))}."
                )
            })

    def save(self, *args, **kwargs):
        if not self.nome:
            self.nome = _anos_letivos_permitidos(3)[0]
        self.full_clean()
        return super().save(*args, **kwargs)


class Turma(models.Model):
    class TipoContexto(models.TextChoices):
        ENSINO_BASICO_TIC = "ENSINO_BASICO_TIC", "Ensino Básico (TIC)"
        ENSINO_SECUNDARIO = "ENSINO_SECUNDARIO", "Ensino Secundário"
        ENSINO_PROFISSIONAL_UFCD = "ENSINO_PROFISSIONAL_UFCD", "Ensino Profissional (UFCD)"

    class Ciclo(models.TextChoices):
        CICLO_2 = "2C", "2º Ciclo"
        CICLO_3 = "3C", "3º Ciclo"
        SECUNDARIO = "SEC", "Ensino Secundário"

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

    # Observação: no Admin vamos “filtrar” choices dinamicamente.
    # No model, deixamos choices completas e validamos em clean().
    ciclo = models.CharField(
        "Ciclo",
        max_length=3,
        choices=Ciclo.choices,
        default=Ciclo.CICLO_2,
    )

    ano_escolaridade = models.PositiveSmallIntegerField(
        "Ano de escolaridade",
        null=True,
        blank=True,
    )  # 5..12

    # ✅ AGORA OBRIGATÓRIO (para o Admin e para o BD)
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

    # ---------- helpers (regras de ano por ciclo) ----------
    @staticmethod
    def _anos_validos_por_ciclo(ciclo: str) -> set[int]:
        if ciclo == Turma.Ciclo.CICLO_2:
            return {5, 6}
        if ciclo == Turma.Ciclo.CICLO_3:
            return {7, 8, 9}
        if ciclo == Turma.Ciclo.SECUNDARIO:
            return {10, 11, 12}
        return set()

    def clean(self):
        super().clean()

        if self.ano_escolaridade is None:
            raise ValidationError({"ano_escolaridade": "Informe o ano de escolaridade."})

        # ------------------------------
        # Regras por Tipo de Contexto
        # ------------------------------

        # 1) Ensino Básico (TIC)
        if self.tipo_contexto == Turma.TipoContexto.ENSINO_BASICO_TIC:
            # Somente 2C ou 3C
            if self.ciclo not in (Turma.Ciclo.CICLO_2, Turma.Ciclo.CICLO_3):
                raise ValidationError({"ciclo": "Para Ensino Básico (TIC), o ciclo deve ser 2º ou 3º Ciclo."})

            anos_validos = self._anos_validos_por_ciclo(self.ciclo)
            if self.ano_escolaridade not in anos_validos:
                msg = "Para 2º Ciclo, o ano deve ser 5º ou 6º." if self.ciclo == Turma.Ciclo.CICLO_2 else \
                      "Para 3º Ciclo, o ano deve ser 7º, 8º ou 9º."
                raise ValidationError({"ano_escolaridade": msg})

        # 2) Ensino Secundário
        elif self.tipo_contexto == Turma.TipoContexto.ENSINO_SECUNDARIO:
            if self.ciclo != Turma.Ciclo.SECUNDARIO:
                raise ValidationError({"ciclo": "Para Ensino Secundário, o ciclo deve ser 'Ensino Secundário'."})

            anos_validos = self._anos_validos_por_ciclo(Turma.Ciclo.SECUNDARIO)
            if self.ano_escolaridade not in anos_validos:
                raise ValidationError({"ano_escolaridade": "Para Ensino Secundário, o ano deve ser 10º, 11º ou 12º."})

        # 3) Ensino Profissional (UFCD)
        elif self.tipo_contexto == Turma.TipoContexto.ENSINO_PROFISSIONAL_UFCD:
            # Pode escolher 2C, 3C ou SEC
            if self.ciclo not in (Turma.Ciclo.CICLO_2, Turma.Ciclo.CICLO_3, Turma.Ciclo.SECUNDARIO):
                raise ValidationError({"ciclo": "No Ensino Profissional (UFCD), selecione 2º Ciclo, 3º Ciclo ou Secundário."})

            anos_validos = self._anos_validos_por_ciclo(self.ciclo)
            if self.ano_escolaridade not in anos_validos:
                if self.ciclo == Turma.Ciclo.CICLO_2:
                    msg = "Para 2º Ciclo, o ano deve ser 5º ou 6º."
                elif self.ciclo == Turma.Ciclo.CICLO_3:
                    msg = "Para 3º Ciclo, o ano deve ser 7º, 8º ou 9º."
                else:
                    msg = "Para Ensino Secundário, o ano deve ser 10º, 11º ou 12º."
                raise ValidationError({"ano_escolaridade": msg})

        else:
            raise ValidationError({"tipo_contexto": "Tipo de contexto inválido."})

    def __str__(self) -> str:
        return f"{self.nome} ({self.ano_letivo})"


class Aluno(models.Model):
    turma = models.ForeignKey(Turma, on_delete=models.PROTECT, related_name="alunos", verbose_name="Turma")

    # Pode ser vazio (ex.: profissional), mas se existir deve ser único por turma.
    numero = models.PositiveIntegerField("Número", null=True, blank=True)

    nome_completo = models.CharField("Nome completo", max_length=150)

    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"
        ordering = ["turma__nome", "nome_completo"]
        constraints = [
            # ✅ Impede números repetidos NA MESMA TURMA quando numero não é NULL
            models.UniqueConstraint(
                fields=["turma", "numero"],
                condition=models.Q(numero__isnull=False),
                name="uniq_aluno_numero_por_turma_quando_preenchido",
            )
        ]

    def __str__(self) -> str:
        if self.numero is not None:
            return f"{self.numero} - {self.nome_completo}"
        return self.nome_completo

