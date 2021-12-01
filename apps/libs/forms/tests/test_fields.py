import pytest
from django.core.exceptions import ImproperlyConfigured

from apps.libs.forms.fields import PositiveIntegerField, PriceField
from apps.libs.tests import GenericTestNoDB


class TestPositiveIntegerField(GenericTestNoDB):
    def test_default(self):
        field = PositiveIntegerField()
        assert field.min_value == 0

    def test_invalid_min_value(self):
        with pytest.raises(ImproperlyConfigured):
            PositiveIntegerField(min_value=-1)


class TestPriceField(GenericTestNoDB):
    def test_default(self):
        field = PriceField()
        assert field.label == "価格(税込)"

    def test_label(self):
        field = PriceField(label="税込価格")
        assert field.label == "税込価格"
