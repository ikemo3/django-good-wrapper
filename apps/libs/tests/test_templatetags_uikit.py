import pytest
from django import forms
from django.forms.fields import CharField, IntegerField


@pytest.mark.parametrize(
    "field_class, expected",
    (
        (CharField, '<input type="text" name="field" class="uk-input" required id="id_field">'),
        (IntegerField, '<input type="number" name="field" class="uk-input" required id="id_field">'),
    ),
)
def test_uikit(field_class, expected):
    from apps.libs.templatetags import uikit

    class FormForTest(forms.Form):
        field = field_class()

    f = FormForTest()
    f = uikit.uikit(f)

    assert expected in f.as_p()
