import re

from django.db import migrations, models
import django.db.models.deletion


def migrar_turmas(apps, schema_editor):
    Turma = apps.get_model("academico", "Turma")
    banco = schema_editor.connection.alias
    usados = set()

    for turma in Turma.objects.using(banco).all().order_by("pk"):
        descricao = turma.serie or ""
        normalizada = descricao.casefold()
        nivel = "medio" if "médio" in normalizada or "medio" in normalizada else "fundamental"
        serie_match = re.search(r"\d+", descricao)
        if not serie_match:
            raise RuntimeError(
                f"Não foi possível converter a série da turma {turma.pk} ({descricao!r}). "
                "Corrija o cadastro e execute a migração novamente."
            )

        serie = int(serie_match.group())
        limite = 3 if nivel == "medio" else 9
        if not 1 <= serie <= limite:
            raise RuntimeError(
                f"A série {serie} da turma {turma.pk} não é válida para {nivel}. "
                "Corrija o cadastro e execute a migração novamente."
            )

        nome_original = (turma.nome or "").strip()
        # Nomes legados podem conter a série junto com a letra, por exemplo "3º Ano - A".
        sufixo = re.search(r"(?:[-–—]\s*|\s+)([A-Za-zÀ-ÿ]+)$", nome_original)
        nome = sufixo.group(1) if sufixo else nome_original
        nome = nome.strip().upper()
        if not nome:
            nome = "A"

        chave = (turma.ano_letivo_id, nivel, serie, nome.casefold())
        if chave in usados:
            base = nome
            tentativa = 1
            while True:
                sufixo = ""
                valor = tentativa
                while valor:
                    valor, resto = divmod(valor - 1, 26)
                    sufixo = chr(65 + resto) + sufixo
                nome = f"{base}{sufixo}"
                chave = (turma.ano_letivo_id, nivel, serie, nome.casefold())
                if chave not in usados:
                    break
                tentativa += 1

        usados.add(chave)
        turma.nivel_ensino = nivel
        turma.serie_numero = serie
        turma.nome = nome
        turma.save(using=banco, update_fields=["nivel_ensino", "serie_numero", "nome"])


class Migration(migrations.Migration):

    dependencies = [
        ("academico", "0001_initial"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="turma",
            name="turma_unica_por_ano",
        ),
        migrations.AddField(
            model_name="turma",
            name="nivel_ensino",
            field=models.CharField(
                choices=[("fundamental", "Ensino Fundamental"), ("medio", "Ensino Médio")],
                default="fundamental",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="turma",
            name="serie_numero",
            field=models.PositiveSmallIntegerField(null=True),
        ),
        migrations.RunPython(migrar_turmas, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="turma",
            name="serie",
        ),
        migrations.RenameField(
            model_name="turma",
            old_name="serie_numero",
            new_name="serie",
        ),
        migrations.AlterField(
            model_name="turma",
            name="serie",
            field=models.PositiveSmallIntegerField(help_text="Número da série dentro da etapa escolar"),
        ),
        migrations.AlterModelOptions(
            name="turma",
            options={
                "ordering": ["nivel_ensino", "serie", "nome"],
                "verbose_name": "Turma",
                "verbose_name_plural": "Turmas",
                "db_table": "core_turma",
            },
        ),
        migrations.AddConstraint(
            model_name="turma",
            constraint=models.UniqueConstraint(
                fields=("ano_letivo", "nivel_ensino", "serie", "nome"),
                name="turma_unica_por_serie",
            ),
        ),
        migrations.AddConstraint(
            model_name="turma",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("nivel_ensino", "fundamental"), ("serie__gte", 1), ("serie__lte", 9))
                    | models.Q(("nivel_ensino", "medio"), ("serie__gte", 1), ("serie__lte", 3))
                ),
                name="serie_valida_por_nivel_ensino",
            ),
        ),
    ]
