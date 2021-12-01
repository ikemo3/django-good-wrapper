from django.http import QueryDict


def is_empty_query(data: QueryDict):
    """検索条件が空かどうか"""
    for key in data.keys():
        # どれでも値があればOK
        values = data.getlist(key)
        for value in values:
            if value:
                return False

    return True
