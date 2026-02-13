# apps/tic/admin.py
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import admin
from django.utils.html import format_html
from django import forms

from apps.nucleo.models import Turma, Aluno
from apps.tic.models import (
    BoletimPeriodoTIC,
    AtitudesPeriodoTIC,
    AvaliacaoCognitivaTIC,
    NotaAvaliacaoCognitivaTIC,
    Periodo,  # ✅ usa as choices do model
)
from apps.tic.services.tic_calculator import garantir_e_recalcular_boletim


# =========================
# BOLETIM (somente consulta)
# =========================
@admin.register(BoletimPeriodoTIC)
class BoletimPeriodoTICAdmin(admin.ModelAdmin):
    list_display = (
        "turma",
        "aluno",
        "periodo",
        "estado",
        "nota_final_100",
        "nivel_sge",
        "mencao_qualitativa",
    )
    list_filter = ("turma", "periodo", "estado")
    search_fields = ("aluno__nome_completo", "turma__nome")

    # ✅ Só estes podem ser alterados
    fields = (
        "turma",
        "aluno",
        "periodo",
        "estado",
        "autoavaliacao_nivel",
        "observacao",
        # ✅ calculados (consulta)
        "nota_cognitiva_80",
        "nota_atitudes_20",
        "nota_final_100",
        "mencao_qualitativa",
        "nivel_sge",
        # ✅ tabelas (consulta)
        "tabela_atitudes",
        "tabela_avaliacoes",
    )

    readonly_fields = (
        "turma",
        "aluno",
        "periodo",
        "nota_cognitiva_80",
        "nota_atitudes_20",
        "nota_final_100",
        "mencao_qualitativa",
        "nivel_sge",
        "tabela_atitudes",
        "tabela_avaliacoes",
    )

    # não criar manualmente: o sistema cria automaticamente
    def has_add_permission(self, request):
        return False

    # não apagar (regra do teu enunciado)
    def has_delete_permission(self, request, obj=None):
        return False

    # ---------- helpers ----------
    @staticmethod
    def _q2(x: Decimal) -> Decimal:
        return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # ---------- TABELA ATITUDES ----------
    def tabela_atitudes(self, obj: BoletimPeriodoTIC):
        a = getattr(obj, "atitudes", None)  # related_name="atitudes" no OneToOne
        if not a:
            return "Sem atitudes registadas."

        total = a.total_atitudes_20()
        return format_html(
            """
            <table style="border-collapse:collapse; width:100%;">
              <tr><th style="text-align:left;">Item</th><th style="text-align:right;">Valor</th></tr>
              <tr><td>Responsabilidade e integridade</td><td style="text-align:right;">{}</td></tr>
              <tr><td>Excelência e exigência</td><td style="text-align:right;">{}</td></tr>
              <tr><td>Curiosidade, reflexão e inovação</td><td style="text-align:right;">{}</td></tr>
              <tr><td>Cidadania e participação</td><td style="text-align:right;">{}</td></tr>
              <tr><td>Liberdade</td><td style="text-align:right;">{}</td></tr>
              <tr><td><b>Total (0..20)</b></td><td style="text-align:right;"><b>{}</b></td></tr>
            </table>
            """,
            self._q2(Decimal(str(a.responsabilidade_integridade or 0))),
            self._q2(Decimal(str(a.excelencia_exigencia or 0))),
            self._q2(Decimal(str(a.curiosidade_reflexao_inovacao or 0))),
            self._q2(Decimal(str(a.cidadania_participacao or 0))),
            self._q2(Decimal(str(a.liberdade or 0))),
            self._q2(Decimal(str(total or 0))),
        )

    tabela_atitudes.short_description = "Atitudes (detalhe e total)"

    # ---------- TABELA AVALIAÇÕES + NOTAS + MÉDIA ----------
    def tabela_avaliacoes(self, obj: BoletimPeriodoTIC):
        qs = (
            NotaAvaliacaoCognitivaTIC.objects
            .select_related("avaliacao")
            .filter(
                aluno=obj.aluno,
                avaliacao__turma=obj.turma,
                avaliacao__periodo=obj.periodo,
            )
            .order_by("avaliacao__nome")
        )

        if not qs.exists():
            return "Sem notas cognitivas registadas."

        total_peso = Decimal("0")
        soma_ponderada = Decimal("0")
        rows = []

        for n in qs:
            peso = Decimal(str(n.avaliacao.peso_percentual or 0))
            nota = Decimal(str(n.nota_0a100 or 0))

            total_peso += peso
            soma_ponderada += (nota * peso)

            rows.append(
                f"<tr>"
                f"<td>{n.avaliacao.nome}</td>"
                f"<td style='text-align:right;'>{peso:.2f}</td>"
                f"<td style='text-align:right;'>{nota:.2f}</td>"
                f"</tr>"
            )

        # ✅ média ponderada (0..100)
        media_0_100 = self._q2((soma_ponderada / total_peso)) if total_peso > 0 else Decimal("0.00")

        # ✅ Linha final: mostrar APENAS a média (como pediste)
        rows.append(
            f"<tr style='border-top:2px solid #999;'>"
            f"<td><b>Resumo</b></td>"
            f"<td></td>"
            f"<td style='text-align:right;'><b>Média: {media_0_100:.2f}</b></td>"
            f"</tr>"
        )

        return format_html(
            """
            <table style="border-collapse:collapse; width:100%;">
              <tr>
                <th style="text-align:left;">Avaliação</th>
                <th style="text-align:right;">Peso (%)</th>
                <th style="text-align:right;">Nota (0..100)</th>
              </tr>
              {}
            </table>
            """,
            format_html("".join(rows)),
        )

    tabela_avaliacoes.short_description = "Avaliações cognitivas (peso, nota, média)"


# =========================
# ATITUDES (com total 0..20)
# =========================
class AtitudesPeriodoTICAdminForm(forms.ModelForm):
    # campos “auxiliares” para escolher o contexto do boletim
    turma = forms.ModelChoiceField(queryset=Turma.objects.all(), required=True)
    aluno = forms.ModelChoiceField(queryset=Aluno.objects.all(), required=True)
    periodo = forms.ChoiceField(choices=Periodo.choices, required=True)

    class Meta:
        model = AtitudesPeriodoTIC
        fields = (
            "turma",
            "aluno",
            "periodo",
            "responsabilidade_integridade",
            "excelencia_exigencia",
            "curiosidade_reflexao_inovacao",
            "cidadania_participacao",
            "liberdade",
        )


@admin.register(AtitudesPeriodoTIC)
class AtitudesPeriodoTICAdmin(admin.ModelAdmin):
    form = AtitudesPeriodoTICAdminForm

    list_display = ("id", "boletim", "total_atitudes")
    readonly_fields = ("total_atitudes",)

    def total_atitudes(self, obj):
        return obj.total_atitudes_20()

    total_atitudes.short_description = "Total atitudes (0..20)"

    def save_model(self, request, obj, form, change):
        turma = form.cleaned_data["turma"]
        aluno = form.cleaned_data["aluno"]
        periodo = int(form.cleaned_data["periodo"])

        # 1) garante boletim (cria se não existir) + recalcula
        garantir_e_recalcular_boletim(turma_id=turma.id, aluno_id=aluno.id, periodo=periodo)

        # 2) liga o OneToOne corretamente
        boletim = BoletimPeriodoTIC.objects.get(turma=turma, aluno=aluno, periodo=periodo)
        obj.boletim = boletim

        # 3) grava atitudes
        super().save_model(request, obj, form, change)

        # 4) recalcula boletim agora com atitudes gravadas
        garantir_e_recalcular_boletim(turma_id=turma.id, aluno_id=aluno.id, periodo=periodo)


# =========================
# AVALIAÇÕES COGNITIVAS
# =========================
@admin.register(AvaliacaoCognitivaTIC)
class AvaliacaoCognitivaTICAdmin(admin.ModelAdmin):
    list_display = ("turma", "periodo", "nome", "peso_percentual")
    list_filter = ("turma", "periodo")
    search_fields = ("nome",)
    autocomplete_fields = ("turma",)


# =========================
# NOTAS DAS AVALIAÇÕES
# =========================
@admin.register(NotaAvaliacaoCognitivaTIC)
class NotaAvaliacaoCognitivaTICAdmin(admin.ModelAdmin):
    list_display = ("avaliacao", "aluno", "nota_0a100", "criado_em")
    list_filter = ("avaliacao__turma", "avaliacao__periodo")
    search_fields = ("aluno__nome_completo", "avaliacao__nome")
    autocomplete_fields = ("avaliacao", "aluno")


