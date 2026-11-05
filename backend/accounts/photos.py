"""Profile photo handling. Uploads are untrusted files.

Only the pixels are kept: every upload is decoded and saved as a new JPEG, which
drops metadata such as GPS location and anything hidden in the original file.
The uploaded name and content type are ignored, and a random name is used.
"""

import io
import uuid

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework.exceptions import ValidationError

MAX_PHOTO_BYTES = 5 * 1024 * 1024
# Limits memory use: a small file can decode to a huge image.
MAX_PHOTO_PIXELS = 25_000_000
PHOTO_SIZE = 256
# Limits which decoders can run. Excludes SVG, which can carry scripts.
ALLOWED_FORMATS = ('JPEG', 'PNG', 'WEBP')

TOO_LARGE_MESSAGE = 'Choose an image of 5 MB or less.'
NOT_AN_IMAGE_MESSAGE = 'Choose a JPEG, PNG or WebP image.'


def _reencode(uploaded):
    if uploaded.size > MAX_PHOTO_BYTES:
        raise ValidationError({'photo': [TOO_LARGE_MESSAGE]})

    try:
        with Image.open(uploaded, formats=ALLOWED_FORMATS) as image:
            if image.width * image.height > MAX_PHOTO_PIXELS:
                raise ValidationError({'photo': ['This image is too large. Choose a smaller one.']})

            image = ImageOps.exif_transpose(image).convert('RGBA')
            # Transparent areas become white, because JPEG has no transparency.
            flattened = Image.new('RGB', image.size, 'white')
            flattened.paste(image, mask=image.getchannel('A'))
            square = ImageOps.fit(flattened, (PHOTO_SIZE, PHOTO_SIZE))

            output = io.BytesIO()
            square.save(output, format='JPEG', quality=85)
            return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError):
        raise ValidationError({'photo': [NOT_AN_IMAGE_MESSAGE]})


def remove_profile_photo(user):
    old_photo = user.photo
    if not old_photo:
        return
    storage, old_name = old_photo.storage, old_photo.name
    user.photo = ''
    user.save(update_fields=['photo'])
    storage.delete(old_name)


def save_profile_photo(user, uploaded):
    content = _reencode(uploaded)
    old_photo = user.photo
    storage, old_name = old_photo.storage, old_photo.name

    user.photo.save(f'{uuid.uuid4().hex}.jpg', ContentFile(content), save=False)
    user.save(update_fields=['photo'])

    if old_name:
        storage.delete(old_name)
