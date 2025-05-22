import random
import string


def capitalize(text: str) -> str:
    return text.capitalize()

def lowercase(text: str) -> str:
    return text.lower()

def randomText(length: int = 8) -> str:
    letters = string.ascii_letters  # a-z, A-Z
    return ''.join(random.choice(letters) for _ in range(length))