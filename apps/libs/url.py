from urllib.parse import ParseResult, parse_qs, urlencode, urlparse

from django.urls import path


def remove_next_url(url: str):
    if not url:
        return url

    parsed = urlparse(url)  # type: ParseResult

    # クエリストリングを解析して、"next"を除外
    query = parse_qs(parsed.query)
    query.pop("next", None)  # KeyErrorを出さないためにNoneを指定

    # クエリストリングに戻す(doseq=Trueとすることで、値がシーケンスの場合に対応)
    new_query = urlencode(query, doseq=True)

    # クエリストリングを置き換えたParseResultを作成してURLを返す
    new_parsed = parsed._replace(query=new_query)
    return new_parsed.geturl()


def remove_query_string(url: str):
    if not url:
        return url

    parsed = urlparse(url)  # type: ParseResult

    # クエリストリングを置き換えたParseResultを作成してURLを返す
    new_parsed = parsed._replace(query=None)
    return new_parsed.geturl()


def create_crudl(list_view, detail_view, add_view, edit_view, delete_view):
    return [
        path("", list_view.as_view(), name="list"),
        path("detail/<int:pk>/", detail_view.as_view(), name="detail"),
        path("add/", add_view.as_view(), name="add"),
        path("edit/<int:pk>/", edit_view.as_view(), name="edit"),
        path("delete/<int:pk>/", delete_view.as_view(), name="delete"),
    ]
