from django.contrib import admin
from .models import AnoLetivo, Turma, Aluno


@admin.register(AnoLetivo)
class AnoLetivoAdmin(admin.ModelAdmin):
    list_display = ("nome", "data_inicio", "data_fim", "criado_em")
    search_fields = ("nome",)


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
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
