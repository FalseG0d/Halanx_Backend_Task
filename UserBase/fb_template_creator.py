import os
import textwrap
from io import BytesIO
from random import shuffle

import requests
from PIL import Image, ImageDraw, ImageOps, ImageFont
from django.conf import settings
from django.core.files import File

font_file = os.path.join(settings.BASE_DIR, 'static/fonts/dejavu-sans/DejaVuSans.ttf')
title_font = ImageFont.truetype(font_file, 30)
name_font = ImageFont.truetype(font_file, 40)
template_url = 'https://d28fujbigzf56k.cloudfront.net/static/img/fbtemplate2.png'


def write_title(draw, text, height, bgcolor="white", pad=10, line_width=30):
    lines = textwrap.wrap(text, width=line_width)
    y = height
    for line in lines:
        w, h = title_font.getsize(line)
        x = 600 + (600 - w) / 2
        draw.rectangle((675 - pad, y - pad, 1125 + pad, y + h + pad), fill=bgcolor)
        draw.text((x, y), line, fill="red", font=title_font)
        y += h + pad
    return y


def write_name(draw, name):
    w, h = name_font.getsize(name)
    draw.text(((600 - w) / 2, 500), name, fill="black", font=name_font)


def draw_photo(url):
    resp = requests.get(url)
    pic = Image.open(BytesIO(resp.content)).resize((260, 260), Image.ANTIALIAS)

    bigsize = (pic.size[0] * 3, pic.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pic.size, Image.ANTIALIAS)
    pic.putalpha(mask)
    output = ImageOps.fit(pic, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)
    resp = requests.get(template_url)
    background = Image.open(BytesIO(resp.content))
    background.paste(pic, (170, 185), pic)
    return background


def draw_template(customer):
    background = draw_photo(customer.profile_pic_url)
    draw = ImageDraw.Draw(background)
    write_name(draw, str(customer.user.first_name) + ' ' + str(customer.user.last_name))

    y = 170
    titles = list(set(poll.title for poll in customer.assigned_polls.all()))
    shuffle(titles)
    for title in titles:
        y = write_title(draw, title, y)
        y += 30
        if y >= 600:
            break

    final = BytesIO()
    background.save(final, format='JPEG')
    customer.fb_template.save('{}.jpg'.format(customer.user.username), File(final))
