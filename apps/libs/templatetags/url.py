from urllib.parse import parse_qs, quote, urlparse

from django import template

register = template.Library()


@register.filter
def concat_next_url(url: str, next_url: str):
    escaped_next_url = quote(next_url)
    if "?" in url:
        return f"{url}&next={escaped_next_url}"
    else:
        return f"{url}?next={escaped_next_url}"


@register.filter
def inherit_next_url(url: str, current_url: str):
    parsed = urlparse(current_url)
    query = parse_qs(parsed.query)

    if not query.get("next"):
        return url

    next_param = query.get("next")[0]
    parsed_next_param = urlparse(next_param)
    query_next_param = parse_qs(parsed_next_param.query)
    if query_next_param.get("next"):
        next_next_param = query_next_param.get("next")[0]
        return f"{url}?next={next_next_param}"
    else:
        return f"{url}?next={next_param}"
