from django.contrib import admin
from django import forms

from .models import AnoLetivo, Turma, Aluno, _anos_letivos_permitidos


# =========================
# FORM do Ano Letivo (Admin)
# =========================
class AnoLetivoAdminForm(forms.ModelForm):
    class Meta:
        model = AnoLetivo
        fields = ("nome", "data_inicio", "data_fim")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        nome_field = self.fields.get("nome")
        if not nome_field:
            return

        opcoes = [(v, v) for v in _anos_letivos_permitidos(3)]
        nome_field.widget = forms.Select(choices=opcoes)

        if self.instance and self.instance.pk:
            nome_field.disabled = True


@admin.register(AnoLetivo)
class AnoLetivoAdmin(admin.ModelAdmin):
    form = AnoLetivoAdminForm

    list_display = ("nome", "data_inicio", "data_fim", "criado_em")
    search_fields = ("nome",)

    fields = ("nome", "data_inicio", "data_fim", "criado_em", "atualizado_em")
    readonly_fields = ("criado_em", "atualizado_em")


# =========================
# FORM da Turma (Admin)
# =========================
class TurmaAdminForm(forms.ModelForm):
    """
    Objetivo:
    - Ciclo e Ano de escolaridade só “fazem sentido” depois de escolher Tipo de contexto.
    - Atualização imediata (sem precisar clicar em SALVAR) usando JS do Django Admin.
    - Professor obrigatório NO ADMIN (sem mexer no banco/migrations).
    """

    professor = forms.ModelChoiceField(
        queryset=Turma._meta.get_field("professor").remote_field.model.objects.all(),
        required=True,
        label="Professor",
    )

    # Importante: aqui deixamos o servidor aceitar as opções possíveis
    # (o JS é quem filtra o que aparece para o usuário).
    ciclo = forms.ChoiceField(
        required=True,
        label="Ciclo",
        choices=[
            ("", "— Selecione —"),
            (Turma.Ciclo.CICLO_2, Turma.Ciclo.CICLO_2.label),
            (Turma.Ciclo.CICLO_3, Turma.Ciclo.CICLO_3.label),
            (Turma.Ciclo.SECUNDARIO, Turma.Ciclo.SECUNDARIO.label),
        ],
    )

    ano_escolaridade = forms.TypedChoiceField(
        label="Ano de escolaridade",
        coerce=int,
        required=True,
        choices=[
            ("", "— Selecione —"),
            (5, "5.º ano"),
            (6, "6.º ano"),
            (7, "7.º ano"),
            (8, "8.º ano"),
            (9, "9.º ano"),
            (10, "10.º ano"),
            (11, "11.º ano"),
            (12, "12.º ano"),
        ],
    )

    class Meta:
        model = Turma
        fields = "__all__"

    class Media:
        # ✅ arquivo JS que vamos criar no passo 2
        js = ("nucleo/js/turma_admin.js",)

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
        cleaned = super().clean()

        tipo = cleaned.get("tipo_contexto")
        ciclo = cleaned.get("ciclo")
        ano = cleaned.get("ano_escolaridade")
        prof = cleaned.get("professor")

        # Professor obrigatório (Admin)
        if not prof:
            self.add_error("professor", "Selecione o Professor (campo obrigatório).")

        if not tipo:
            self.add_error("tipo_contexto", "Selecione o Tipo de contexto.")
            return cleaned

        if not ciclo:
            self.add_error("ciclo", "Selecione o Ciclo.")
            return cleaned

        if ano is None:
            self.add_error("ano_escolaridade", "Selecione o Ano de escolaridade.")
            return cleaned

        # Regras por Tipo de contexto (iguais ao teu enunciado)
        if tipo == Turma.TipoContexto.ENSINO_BASICO_TIC:
            if ciclo not in (Turma.Ciclo.CICLO_2, Turma.Ciclo.CICLO_3):
                self.add_error("ciclo", "Para Ensino Básico (TIC), o ciclo deve ser 2º ou 3º Ciclo.")
                return cleaned

            validos = self._anos_validos_por_ciclo(ciclo)
            if int(ano) not in validos:
                msg = "Para 2º Ciclo, o ano deve ser 5º ou 6º." if ciclo == Turma.Ciclo.CICLO_2 else "Para 3º Ciclo, o ano deve ser 7º, 8º ou 9º."
                self.add_error("ano_escolaridade", msg)

        elif tipo == Turma.TipoContexto.ENSINO_SECUNDARIO:
            if ciclo != Turma.Ciclo.SECUNDARIO:
                self.add_error("ciclo", "Para Ensino Secundário, o ciclo deve ser 'Ensino Secundário'.")
                return cleaned

            validos = self._anos_validos_por_ciclo(Turma.Ciclo.SECUNDARIO)
            if int(ano) not in validos:
                self.add_error("ano_escolaridade", "Para Ensino Secundário, o ano deve ser 10º, 11º ou 12º.")

        elif tipo == Turma.TipoContexto.ENSINO_PROFISSIONAL_UFCD:
            if ciclo not in (Turma.Ciclo.CICLO_2, Turma.Ciclo.CICLO_3, Turma.Ciclo.SECUNDARIO):
                self.add_error("ciclo", "No Ensino Profissional (UFCD), selecione 2º Ciclo, 3º Ciclo ou Secundário.")
                return cleaned

            validos = self._anos_validos_por_ciclo(ciclo)
            if int(ano) not in validos:
                if ciclo == Turma.Ciclo.CICLO_2:
                    msg = "Para 2º Ciclo, o ano deve ser 5º ou 6º."
                elif ciclo == Turma.Ciclo.CICLO_3:
                    msg = "Para 3º Ciclo, o ano deve ser 7º, 8º ou 9º."
                else:
                    msg = "Para Ensino Secundário, o ano deve ser 10º, 11º ou 12º."
                self.add_error("ano_escolaridade", msg)

        else:
            self.add_error("tipo_contexto", "Tipo de contexto inválido.")

        return cleaned


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    form = TurmaAdminForm

    list_display = ("nome", "ano_letivo", "tipo_contexto", "ciclo", "ano_escolaridade", "professor")
    list_filter = ("tipo_contexto", "ciclo", "ano_letivo")
    search_fields = ("nome",)
    autocomplete_fields = ("ano_letivo", "professor")


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("nome_completo", "numero", "turma")
    list_filter = ("turma",)
    search_fields = ("nome_completo", "numero")
    autocomplete_fields = ("turma",)

