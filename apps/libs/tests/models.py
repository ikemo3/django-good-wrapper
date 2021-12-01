import pytest


@pytest.mark.django_db(transaction=True)
class GenericTestModel:
    pass


@pytest.mark.django_db(transaction=True)
class GenericTestQuerySet:
    pass


@pytest.mark.django_db(transaction=True)
class GenericTestInconsistency:
    pass
