import pytest


@pytest.mark.django_db(transaction=True)
class GenericTestFilterSet:
    pass
