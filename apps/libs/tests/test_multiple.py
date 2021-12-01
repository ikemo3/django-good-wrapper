from apps.libs.views.multiple import MultipleFormMixin


class FormForTest(MultipleFormMixin):
    success_url = "/admin/"


class TestMultipleFormMixin:
    def test_it(self):
        form = FormForTest()
        assert form.get_success_url() == "/admin/"
