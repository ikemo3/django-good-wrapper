from apps.libs.path import random_filepath


def test_random_filename():
    f = random_filepath("base")
    generated = f("original_filename.png")
    assert generated.startswith("base/")
    assert len(generated) == 5 + 64 + 4, "`base/` + ランダムな文字列(64文字) + 拡張子(`.png`)"
