# Generated by Django 4.1 on 2022-08-17 09:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0004_rename_filmwork_genrefilmwork_film_work'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personfilmwork',
            name='role',
            field=models.TextField(choices=[('actor', 'actor'), ('director', 'director'), ('scenarist', 'scenarist')], default='actor', max_length=9, verbose_name='role'),
        ),
    ]