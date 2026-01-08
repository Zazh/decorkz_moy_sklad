# scraping/parsers/__init__.py

from .base import BaseParser, ParsedProduct

# Реестр всех парсеров
# При создании нового парсера добавь его сюда
PARSERS: dict[str, type[BaseParser]] = {
    # 'bosch': BoschParser,
    # 'makita': MakitaParser,
}


def get_parser(name: str) -> BaseParser:
    """
    Получить экземпляр парсера по имени.

    Args:
        name: Имя парсера (ключ в PARSERS)

    Returns:
        Экземпляр парсера

    Raises:
        ValueError: Если парсер не найден
    """
    parser_class = PARSERS.get(name)
    if not parser_class:
        available = ', '.join(PARSERS.keys()) if PARSERS else 'нет доступных парсеров'
        raise ValueError(f"Парсер '{name}' не найден. Доступные: {available}")
    return parser_class()


def get_all_parsers() -> list[BaseParser]:
    """Получить экземпляры всех зарегистрированных парсеров"""
    return [cls() for cls in PARSERS.values()]


def list_parsers() -> list[str]:
    """Получить список имён всех парсеров"""
    return list(PARSERS.keys())