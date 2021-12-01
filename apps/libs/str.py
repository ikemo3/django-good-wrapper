from typing import Tuple, Type, Union


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def fqcn(klass_or_object: Union[Type, object]):
    if isinstance(klass_or_object, type):
        klass = klass_or_object
    else:
        klass = klass_or_object.__class__

    return f"{klass.__module__}.{klass.__qualname__}"


def _get_first_char(s: str):
    c = s[0]

    index = 1
    while True:
        c2 = s[index]
        if ord(c2) == 0x200D:
            # ゼロ幅接合子(ZERO WIDTH JOINER)の場合はその文字と次の文字を含める
            # https://ja.wikipedia.org/wiki/%E3%82%BC%E3%83%AD%E5%B9%85%E6%8E%A5%E5%90%88%E5%AD%90
            c = c + c2 + s[index + 1]
            index += 2
            continue
        elif 0xFE00 <= ord(c2) <= 0xFE0F:
            # 絵文字特化異体字セレクタの場合はその文字を含める
            # http://www.asahi-net.or.jp/~ax2s-kmtn/ref/unicode/ufe00.html
            c = c + c2
            index += 1
        else:
            return c

    raise AssertionError  # pragma: no cover


def split_first(s: str) -> Tuple[str, str]:
    """最初の文字を分割して返す"""
    first_char = _get_first_char(s)
    return _get_first_char(s), s[len(first_char) :]
