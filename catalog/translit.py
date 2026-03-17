"""
Транслитерация кириллицы в латиницу для URL-slugов и имён файлов.
"""
import re
import unicodedata

CYRILLIC_TO_LATIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
    'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
    'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
    'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
    'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch',
    'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '',
    'э': 'e', 'ю': 'yu', 'я': 'ya',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
    'Е': 'E', 'Ё': 'Yo', 'Ж': 'Zh', 'З': 'Z', 'И': 'I',
    'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
    'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
    'У': 'U', 'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch',
    'Ш': 'Sh', 'Щ': 'Shch', 'Ъ': '', 'Ы': 'Y', 'Ь': '',
    'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
}


def transliterate(text):
    """Транслитерирует кириллицу в латиницу."""
    if not text:
        return ''
    return ''.join(CYRILLIC_TO_LATIN.get(ch, ch) for ch in text)


def translit_slugify(text, max_length=200):
    """
    Транслитерация + slugify: кириллица → латиница → slug.
    Результат содержит только [a-z0-9-].
    """
    if not text:
        return ''
    # Транслитерация
    text = transliterate(text)
    # Нормализация Unicode
    text = unicodedata.normalize('NFKD', text)
    # Оставляем только ASCII буквы, цифры и дефисы
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)  # пробелы/подчёркивания → дефис
    text = re.sub(r'-+', '-', text)  # убираем повторные дефисы
    text = text.strip('-')
    return text[:max_length]


def safe_filename(filename):
    """
    Транслитерирует имя файла, оставляя расширение.
    Результат: только [a-z0-9_-] + расширение.
    """
    if not filename:
        return filename

    # Разделяем имя и расширение
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
        ext = transliterate(ext).lower()
        # Если ext содержит не только буквы расширения (напр. "13000мм_laconistiq"),
        # значит точка была частью имени — склеиваем обратно
        if not re.match(r'^[a-z0-9]{1,10}$', ext):
            name = filename
            ext = ''
    else:
        name = filename
        ext = ''

    # Транслитерация
    name = transliterate(name)
    # Оставляем только безопасные символы
    name = name.lower()
    name = re.sub(r'[^a-z0-9_-]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')

    if not name:
        name = 'file'

    if ext:
        return f'{name}.{ext}'
    return name
