# scraping/parsers/__init__.py

from .base import BaseParser, ParsedProduct
from .decor_dizayn import DecorDizaynParser

# Реестр всех парсеров
PARSERS: dict[str, type[BaseParser]] = {
    'decor_dizayn': DecorDizaynParser,
}


def get_parser(name: str, **kwargs) -> BaseParser:
    """
    Получить экземпляр парсера по имени.
    """
    parser_class = PARSERS.get(name)
    if not parser_class:
        available = ', '.join(PARSERS.keys()) if PARSERS else 'нет доступных парсеров'
        raise ValueError(f"Парсер '{name}' не найден. Доступные: {available}")
    return parser_class(**kwargs)


def get_all_parsers() -> list[BaseParser]:
    """Получить экземпляры всех зарегистрированных парсеров"""
    return [cls() for cls in PARSERS.values()]


def list_parsers() -> list[str]:
    """Получить список имён всех парсеров"""
    return list(PARSERS.keys())