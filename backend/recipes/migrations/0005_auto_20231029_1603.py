# Generated by Django 3.2 on 2023-10-29 13:03

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_auto_20231028_1919'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredient',
            options={'ordering': ('name',), 'verbose_name': 'продукт', 'verbose_name_plural': 'продукты'},
        ),
        migrations.AlterModelOptions(
            name='recipeingredient',
            options={'verbose_name': 'продукт в рецепте', 'verbose_name_plural': 'продукты в рецепте'},
        ),
        migrations.AlterField(
            model_name='recipe',
            name='ingredients',
            field=models.ManyToManyField(related_name='recipe', through='recipes.RecipeIngredient', to='recipes.Ingredient', verbose_name='продукт'),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='amount',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1, 'Минимальное значение = 1')], verbose_name='мера'),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='ingredient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipe_ingredient', to='recipes.ingredient', verbose_name='продукт'),
        ),
    ]