from dataclasses import dataclass

import factory


@dataclass
class UploadFile:
    filename: str
    contents: bytes


def random_number():
    """正の整数をランダムに返す
    https://faker.readthedocs.io/en/master/providers/baseprovider.html#faker.providers.BaseProvider.random_number
    """
    return factory.Faker("random_number")


def random_date():
    """1970-01-01〜今日までの日付をランダムに返す
    https://faker.readthedocs.io/en/master/providers/faker.providers.date_time.html#faker.providers.date_time.Provider.date
    """
    return factory.Faker("date")


def random_year():
    """
    https://faker.readthedocs.io/en/master/providers/faker.providers.date_time.html#faker.providers.date_time.Provider.year
    """
    return factory.Faker("year")


def random_url():
    """http/https のURLをランダムに返す
    https://faker.readthedocs.io/en/master/providers/faker.providers.internet.html#faker.providers.internet.Provider.url
    """
    return factory.Faker("url")


def random_user_name():
    """ユーザ名に使われる、英数字からなる文字列をランダムに返す
    https://faker.readthedocs.io/en/master/providers/faker.providers.internet.html#faker.providers.internet.Provider.user_name
    """
    return factory.Faker("user_name")


def sequential_str(base: str):
    return factory.Sequence(lambda n: f"{base}{n}")


def sequential_number(start: int):
    return factory.Sequence(lambda n: n + start - 1)


def random_str():
    return factory.Faker("paragraph")


def dummy_image() -> bytes:
    return factory.django.ImageField()._make_data({"width": 1024, "height": 768})
