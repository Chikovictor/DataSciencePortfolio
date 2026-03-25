from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0003_certification"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="review",
            options={"ordering": ["-created_at"]},
        ),
    ]
