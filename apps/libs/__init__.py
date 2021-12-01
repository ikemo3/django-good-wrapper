# 本番環境で呼び出されてもエラーにならないようにする
try:
    import pytest

    pytest.register_assert_rewrite("apps.libs.tests")
except ModuleNotFoundError:  # pragma: no cover
    pass
