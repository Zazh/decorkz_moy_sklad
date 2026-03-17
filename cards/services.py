# cards/services.py

import os
import logging
from io import BytesIO
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

# Качество WebP (100 — без потерь качества)
WEBP_QUALITY = 100
WEBP_MAX_DIMENSION = 1200  # Максимальная сторона


def convert_image_to_webp(card_image, quality=WEBP_QUALITY, max_dim=WEBP_MAX_DIMENSION):
    """
    Конвертирует изображение ProductCardImage в WebP.

    - Если уже .webp — пропускает
    - Сжимает до max_dim по большей стороне
    - Удаляет старый файл
    - Обновляет запись в БД

    Возвращает True если конвертировано, False если пропущено.
    """
    if not card_image.image:
        return False

    name = card_image.image.name
    if name.lower().endswith('.webp'):
        return False

    file_path = os.path.join(settings.MEDIA_ROOT, name)

    # Файл на диске
    if not os.path.exists(file_path):
        logger.warning(f'Файл не найден: {file_path}')
        return False

    try:
        with Image.open(file_path) as img:
            # RGBA → RGB (WebP поддерживает alpha, но для фото не нужен)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Ресайз если слишком большое
            w, h = img.size
            if max(w, h) > max_dim:
                ratio = max_dim / max(w, h)
                new_size = (int(w * ratio), int(h * ratio))
                img = img.resize(new_size, Image.LANCZOS)

            # Сохраняем в буфер
            buf = BytesIO()
            img.save(buf, format='WEBP', quality=quality, method=4)
            webp_data = buf.getvalue()

    except Exception as e:
        logger.error(f'Ошибка конвертации {name}: {e}')
        return False

    # Новое имя файла
    base_name = name.rsplit('.', 1)[0] if '.' in name else name
    new_name = f'{base_name}.webp'

    # Удаляем старый файл
    try:
        os.remove(file_path)
    except OSError:
        pass

    # Сохраняем WebP через Django storage
    card_image.image.save(
        os.path.basename(new_name),
        ContentFile(webp_data),
        save=True,
    )

    return True


def convert_uploaded_bytes_to_webp(content_bytes, filename, quality=WEBP_QUALITY, max_dim=WEBP_MAX_DIMENSION):
    """
    Конвертирует байты изображения в WebP.
    Используется при скачивании из МойСклад — конвертируем до сохранения на диск.

    Возвращает (webp_bytes, new_filename) или (None, None) при ошибке.
    """
    try:
        with Image.open(BytesIO(content_bytes)) as img:
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            w, h = img.size
            if max(w, h) > max_dim:
                ratio = max_dim / max(w, h)
                new_size = (int(w * ratio), int(h * ratio))
                img = img.resize(new_size, Image.LANCZOS)

            buf = BytesIO()
            img.save(buf, format='WEBP', quality=quality, method=4)

        # Меняем расширение
        base = filename.rsplit('.', 1)[0] if '.' in filename else filename
        new_filename = f'{base}.webp'

        return buf.getvalue(), new_filename

    except Exception as e:
        logger.error(f'Ошибка конвертации в WebP ({filename}): {e}')
        return None, None
