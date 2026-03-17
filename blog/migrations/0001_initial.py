from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Заголовок')),
                ('description', models.CharField(blank=True, max_length=500, verbose_name='Описание')),
                ('slug', models.SlugField(blank=True, max_length=200, unique=True)),
                ('image', models.ImageField(blank=True, upload_to='blog_images', verbose_name='Изображение')),
                ('publish_date', models.DateTimeField(verbose_name='Дата публикации')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна')),
            ],
            options={
                'verbose_name': 'Статья',
                'verbose_name_plural': 'Статьи',
                'ordering': ['-publish_date'],
            },
        ),
        migrations.CreateModel(
            name='ContentBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(choices=[('p', 'Параграф'), ('h2', 'Заголовок 2'), ('h3', 'Заголовок 3'), ('ul', 'Маркированный список'), ('ol', 'Нумерованный список')], max_length=2, verbose_name='Тип')),
                ('text', models.TextField(verbose_name='Текст')),
                ('bold', models.BooleanField(default=False, verbose_name='Жирный')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks', to='blog.post')),
            ],
            options={
                'verbose_name': 'Блок контента',
                'verbose_name_plural': 'Блоки контента',
                'ordering': ['sort_order', 'id'],
            },
        ),
    ]
