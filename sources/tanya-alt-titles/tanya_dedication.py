import django

django.setup()

from sefaria.model import *


def add_tanya_dedication():
    tanya_index = library.get_index("Tanya")

    tanya_index.dedication = {
        'en': 'This text has been sponsored by Yitz Applbaum in honor of his dear friends and Chabad guiding lights Rabbi Itchel Krasnjansky and Rabbi Eitan Webb.',
        'he': 'הטקסט מובא בחסות ייץ אפלבאום (יצחק אייזק בן הרב יהושע) לכבוד חבריו היקרים ומאורות חב"ד, הרב איצ’ל קרסניאנסקי והרב איתן ווב'}

    tanya_index.save()


if __name__ == '__main__':
    add_tanya_dedication()
