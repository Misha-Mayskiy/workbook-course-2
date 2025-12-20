import os
import sys


def resource_path(relative_path: str) -> str:
    """ Получает путь к файлу, который будет работать и в EXE """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
