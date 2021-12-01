import pytest

from apps.libs.url import remove_next_url, remove_query_string


class TestRemoveNextUrl:
    @pytest.mark.parametrize(
        "url, expected",
        (
            ("/path/only", "/path/only"),
            ("/path/to/?next=/next/url", "/path/to/"),
            ("/path/to/?next=/next/url&status=1", "/path/to/?status=1"),
            ("/path/to/?status=1&next=/next/url", "/path/to/?status=1"),
            ("", ""),
            (None, None),
        ),
    )
    def test_it(self, url, expected):
        assert remove_next_url(url) == expected


class TestRemoveQueryString:
    @pytest.mark.parametrize(
        "url, expected",
        (
            ("/path/only", "/path/only"),
            ("/path/to/?next=/next/url", "/path/to/"),
            ("/path/to/?next=/next/url&status=1", "/path/to/"),
            ("/path/to/?status=1&next=/next/url", "/path/to/"),
            ("", ""),
            (None, None),
        ),
    )
    def test_it(self, url, expected):
        assert remove_query_string(url) == expected
