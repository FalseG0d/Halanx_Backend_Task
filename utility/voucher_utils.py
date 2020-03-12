from random import randint


def generate_voucher_item_code(used_codes):
    code = str(randint(11111111, 99999999))
    while code in used_codes:
        code = str(randint(11111111, 99999999))
    return code
