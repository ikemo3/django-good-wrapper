import os
import secrets
from typing import Callable

CHARS = "0123456789abcdef"


def random_filepath(base_dir: str, filename_length: int = 64) -> Callable[[str], str]:
    """ランダムなファイル名を返す関数を作る関数"""

    def f(original_filename):
        filename = "".join(secrets.choice(CHARS) for i in range(filename_length))
        ext = os.path.splitext(original_filename)[1]
        return f"{base_dir}/{filename}{ext.lower()}"

    return f
