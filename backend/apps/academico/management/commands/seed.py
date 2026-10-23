from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.academico.models import AnoLetivo, Escola, Turma

User = get_user_model()

TURMAS = [
    {"nome": "A", "serie": "6º Ano", "turno": "manha"},
    {"nome": "B", "serie": "6º Ano", "turno": "tarde"},
    {"nome": "A", "serie": "7º Ano", "turno": "manha"},
    {"nome": "B", "serie": "7º Ano", "turno": "tarde"},
    {"nome": "A", "serie": "8º Ano", "turno": "manha"},
    {"nome": "A", "serie": "9º Ano", "turno": "tarde"},
]


class Command(BaseCommand):
    help = "Popula o banco com dados iniciais para demonstração"

    def handle(self, *args, **kwargs):
        # Superusuário para o painel /admin
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@demo.com", "admin123")
            self.stdout.write("Superusuário 'admin' criado.")

        # Usuário da escola
        usuario_escola, _ = User.objects.get_or_create(
            username="escola",
            defaults={"email": "escola@demo.com"},
        )
        usuario_escola.set_password("escola123")
        usuario_escola.save()

        # Escola
        escola, criada = Escola.objects.get_or_create(
            nome="Escola Estadual Exemplo",
            defaults={
                "cnpj": "00.000.000/0001-00",
                "endereco": "Rua das Flores, 123 - Centro",
                "usuario": usuario_escola,
                "ativo": True,
            },
        )
        if criada:
            self.stdout.write(f"Escola '{escola.nome}' criada.")
        elif not escola.usuario:
            escola.usuario = usuario_escola
            escola.save(update_fields=["usuario"])

        # Ano letivo
        ano_letivo, _ = AnoLetivo.objects.get_or_create(
            escola=escola,
            ano=2025,
            defaults={"ativo": True},
        )

        # Turmas
        for t in TURMAS:
            _, criada = Turma.objects.get_or_create(
                ano_letivo=ano_letivo,
                nome=t["nome"],
                defaults={"serie": t["serie"], "turno": t["turno"], "ativo": True},
            )
            if criada:
                self.stdout.write(f"Turma '{t['serie']} {t['nome']}' criada.")

        self.stdout.write(self.style.SUCCESS("\nSeed concluído!"))
        self.stdout.write("  Escola → usuário: escola  | senha: escola123")
        self.stdout.write("  Admin  → usuário: admin   | senha: admin123")
