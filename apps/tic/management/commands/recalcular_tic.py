from django.core.management.base import BaseCommand

from apps.tic.models import BoletimPeriodoTIC
from apps.tic.services.tic_calculator import recalcular_e_gravar_periodo


class Command(BaseCommand):
    help = "Recalcula e grava as notas finais TIC para boletins (por turma/periodo opcional)."

    def add_arguments(self, parser):
        parser.add_argument("--turma_id", type=int, default=None)
        parser.add_argument("--periodo", type=int, default=None)

    def handle(self, *args, **options):
        turma_id = options["turma_id"]
        periodo = options["periodo"]

        qs = BoletimPeriodoTIC.objects.all()
        if turma_id:
            qs = qs.filter(turma_id=turma_id)
        if periodo:
            qs = qs.filter(periodo=periodo)

        total = qs.count()
        self.stdout.write(self.style.NOTICE(f"Boletins encontrados: {total}"))

        ok = 0
        for boletim in qs:
            recalcular_e_gravar_periodo(boletim)
            ok += 1

        self.stdout.write(self.style.SUCCESS(f"Recalculo finalizado: {ok}/{total}"))
