import pytest


@pytest.mark.django_db(transaction=True)
class GenericTestDashboard:
    pass
