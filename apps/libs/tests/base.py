from dataclasses import dataclass

import pytest


@pytest.mark.django_db(transaction=True)
class GenericTest:
    pass


@pytest.mark.django_db(transaction=True)
class GenericTestTemplate:
    pass


class GenericTestNoDB:
    pass


@dataclass
class NullEntity:
    """test_not_foundのための空っぽのエンティティもどき"""

    id = 0
