# DecorKZ PIM (Product Information Management)

Система управления товарной информацией с интеграцией МойСклад.

## Архитектура

### Приложения
```
config/          — Настройки Django
integration/     — Интеграция с МойСклад (сырые данные)
references/      — Справочники (Brand, Category, Attributes, Units)
mapping/         — Маппинг источников на справочники
products/        — Товары для витрины
cards/           — Карточки контента (описания, фото, характеристики)
pricing/         — Цены и типы цен
inventory/       — Склады и остатки
scraping/        — Парсинг сайтов производителей
legacy/          — Read-only доступ к старой базе
```

### Модели и связи
```
MoySkladProduct (integration)
    ↓ сырые данные из API
    ↓
Product (products) ←──────→ ProductCard (cards)
    │                            │
    ├── moysklad FK              ├── title, description
    ├── article (unique)         ├── images
    ├── slug (auto)              ├── attributes
    ├── brand FK ─────┐          └── source (manual/parsed)
    ├── category FK   │
    └── is_active     │
                      │
Brand (references) ←──┘
    │
    └── name, slug, logo
            ↑
            │
BrandMapping (mapping)
    ├── source ('moysklad' | 'parser')
    ├── source_name (как в источнике)
    └── brand FK (nullable → ждёт связи)
```

### Принцип разделения

**Product** — бизнес-сущность для витрины:
- Связывает МойСклад (цены, остатки) с контентом (карточка)
- Содержит классификацию (бренд, категория)
- Генерирует URL (slug)

**ProductCard** — чистый контент:
- Название, описание, изображения
- Характеристики (атрибуты)
- Источник данных (ручной ввод или парсинг)
- Независим от Product (можно создать до привязки)

**BrandMapping** — связь источник → справочник:
- Хранит все варианты написания бренда из разных источников
- Позволяет связать "DECOR KZ", "Decorkz", "Декор КЗ" → Brand("DECOR KZ")
- brand FK nullable — маппинг создаётся автоматически, связь вручную

### Workflow синхронизации
```bash
# 1. Загрузка сырых данных из МойСклад
python manage.py sync_products

# 2. Создание маппингов брендов (без связи)
python manage.py sync_brands

# 3. В админке: связать маппинги с брендами
#    Mapping → Brand Mappings → выбрать → привязать Brand

# 4. Синхронизация в Product (с брендами через маппинги)
python manage.py sync_pim

# 5. Синхронизация остатков (опционально)
python manage.py sync_pim --stock
```

### Management Commands

| Команда | Описание |
|---------|----------|
| `sync_products` | МойСклад API → MoySkladProduct |
| `sync_brands` | MoySkladProduct → BrandMapping |
| `sync_pim` | MoySkladProduct → Product (через маппинги) |
| `test_moysklad_connection` | Проверка подключения к API |
| `show_products` | Показать товары из МойСклад |

### Справочники (references)

- **Brand** — бренды (эталонные названия)
- **Category** — категории каталога (иерархия)
- **AttributeDefinition** — определения атрибутов
- **UnitGroup** — группы единиц измерения (Масса, Длина, Объём)
- **Unit** — единицы с коэффициентами конвертации

### Маппинг (mapping)

- **BrandMapping** — синонимы брендов из источников
- **CategoryMapping** — категории из источников (TODO)
- **AttributeMapping** — названия атрибутов из источников

## Настройка

### Environment (.env)
```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
DB_NAME=pim_db
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=db
DB_PORT=5432

# Legacy DB (read-only)
LEGACY_DB_NAME=old_db
LEGACY_DB_HOST=db

# МойСклад API
MOYSKLAD_API_URL=https://api.moysklad.ru/api/remap/1.2
MOYSKLAD_LOGIN=admin@company
MOYSKLAD_PASSWORD=password
# или
MOYSKLAD_TOKEN=your-token
```

### Docker
```bash
docker compose up -d
docker compose exec moysklad_integration python manage.py migrate
docker compose exec moysklad_integration python manage.py createsuperuser
```

## TODO

- [ ] CategoryMapping — маппинг категорий МойСклад → Category
- [ ] Парсеры сайтов производителей → ScrapedProduct
- [ ] ScrapedProduct → ProductCard (создание карточек)
- [ ] Product → ProductCard (привязка)
- [ ] Представления для витрины
- [ ] Webhooks МойСклад для real-time обновлений

## Статистика

- Товаров в МойСклад: ~5940
- Товаров в Product: ~5280 (исключены Реклама, Услуги)
- Брендов: 45
- Товаров с брендом: 2051 (39%)