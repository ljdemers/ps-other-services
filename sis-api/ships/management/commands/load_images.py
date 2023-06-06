from django.core.management.base import BaseCommand
import os
import re
from PIL import Image
from django.conf import Settings
import logging

logger = logging.getLogger('sis_api')


def remove_quotes(value):
    if value is None:
        return None
    if len(value) >= 2 and value[0] == "\"" and value[-1] == "\"":
        return value[1:-1]
    return value


PHOTO_URL_BASE = getattr(
    Settings,
    "PHOTO_URL_BASE",
    "http://net.polestarglobal.sis-photos.s3.amazonaws.com/"
)


def add_photo(imo_id, source, taken_date, photo, photo_path):
    try:
        img = Image.open(photo_path)
        width, height = img.size
    except Exception:  # pylint disable-msg=W0703
        width, height = (None, None)

    if source:
        source = source.decode('iso-8859-1').encode('utf8')

    data = {
        "imo_id": imo_id,
        "source": source,
        "taken_date": taken_date,
        "url": PHOTO_URL_BASE + photo,
        "filename": photo,
        "width": width,
        "height": height,
    }

    f = open("photos.csv", "a")
    f.write(
        "%(imo_id)s,%(source)s,%(taken_date)s,%(url)s,%(filename)s,%(width)s,"
        "%(height)s\n" % data
    )
    f.close()


class Command(BaseCommand):
    args = "<image_dir>"
    help = "Load images into sis and upload them to an s3 bucket"

    def handle(self, image_dir, *args, **options):
        file_handle = open(image_dir + "/index.txt", "r")
        index_data = file_handle.read()
        file_handle.close()

        index = {}
        for line in index_data.split("\n"):
            if line == "":
                continue
            values = line.split("\t")
            # Pad with Nones so we always have 4 items
            while len(values) != 4:
                values.append(None)
            values = list(map(remove_quotes, values))
            index[values[0]] = values[1:]

        img_re = re.compile(r'.+_.+\.(jpg|png|jpeg|tif|tiff)$', re.IGNORECASE)
        for root, dir_names, file_names in os.walk(image_dir):
            for name in file_names:
                if img_re.match(name):
                    photo_id = name.split("_")[0]
                    if photo_id in index.keys():
                        imo_id, source, taken_date = index[photo_id]
                        add_photo(
                            imo_id,
                            source,
                            taken_date,
                            name,
                            os.path.join(root, name)
                        )
