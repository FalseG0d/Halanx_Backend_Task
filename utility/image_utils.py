from io import BytesIO

from PIL import Image as Img


def compress_image(image, quality=80, create_thumbnail=False):
    img = Img.open(BytesIO(image.read()))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    output = BytesIO()
    h, w = img.size
    WIDTH = min(400, w)
    img = img.resize((int((h / w) * WIDTH), WIDTH), Img.ANTIALIAS)
    img.save(output, format='JPEG', quality=quality, optimize=True)
    temp_name = image.name

    if create_thumbnail:
        thumbnail = BytesIO()
        img = img.resize((int((h / w) * 100), 100), Img.ANTIALIAS)
        img.save(thumbnail, format='JPEG', quality=100, optimize=True)
        image.delete(save=False)
        return temp_name, output, thumbnail

    image.delete(save=False)
    return temp_name, output


def create_thumbnail(image):
    img = Img.open(BytesIO(image.read()))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    h, w = img.size
    temp_name = image.name

    thumbnail = BytesIO()
    img = img.resize((int((h / w) * 100), 100), Img.ANTIALIAS)
    img.save(thumbnail, format='JPEG', quality=100, optimize=True)
    return temp_name, thumbnail
