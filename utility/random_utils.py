import random

import numpy as np


def generate_random_code(initials='', existing_codes=(), n=8, unique_chars=False,
                         digits=True, alphabets=True, uppercase_alphabets=True, lowercase_alphabets=True):
    if len(initials) >= n:
        return initials[:n]

    code = initials
    characters = []

    if digits:
        characters += [str(x) for x in range(0, 10)]

    if alphabets:
        if uppercase_alphabets:
            characters += [chr(x) for x in range(65, 91)]

        if lowercase_alphabets:
            characters += [chr(x) for x in range(97, 123)]

    while 1:
        if unique_chars:
            code += ''.join(random.sample(characters, k=n))
        else:
            code += ''.join(np.random.choice(characters, size=n))

        if code not in existing_codes:
            break

    return code
