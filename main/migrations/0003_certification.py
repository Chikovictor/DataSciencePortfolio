from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0002_portfolio_upgrade"),
    ]

    operations = [
        migrations.CreateModel(
            name="Certification",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=180)),
                ("issuing_organization", models.CharField(max_length=180)),
                ("issue_date", models.DateField()),
                ("verification_link", models.URLField()),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["display_order", "-issue_date", "-created_at"],
            },
        ),
    ]
