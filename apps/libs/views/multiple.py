from django.http import HttpResponseRedirect
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View

# noinspection PyUnresolvedReferences
from django.views.generic.list import MultipleObjectMixin, MultipleObjectTemplateResponseMixin


# noinspection PyUnresolvedReferences
class MultipleFormMixin(ContextMixin):
    initial = {}
    form_classes = []
    success_url = None

    # noinspection PyUnusedLocal
    def get_initial(self, prefix):
        return self.initial.copy()

    def get_form_classes(self):
        return self.form_classes

    def get_form(self, prefix, form_class):
        return form_class(**self.get_form_kwargs(prefix))

    def get_forms(self):
        form_classes = self.get_form_classes()
        return [self.get_form(prefix, form_class) for prefix, form_class in form_classes]

    def get_form_kwargs(self, prefix):
        kwargs = {
            "initial": self.get_initial(prefix),
            "prefix": prefix,
        }

        if self.request.method == "POST":
            kwargs.update(
                {
                    "data": self.request.POST,
                    "files": self.request.FILES,
                }
            )

        return kwargs

    def get_success_url(self):
        return self.success_url

    def forms_valid(self, forms):
        return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, forms):
        return self.render_to_response(self.get_context_data(forms=forms))

    def get_context_data(self, **kwargs):
        if "forms" not in kwargs:
            kwargs["forms"] = self.get_forms()
        return super().get_context_data(**kwargs)


# noinspection PyUnresolvedReferences
class ProcessMultipleFormView(View):
    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        is_valid_list = [form.is_valid() for form in forms]
        if all(is_valid_list):
            return self.forms_valid(forms)
        else:
            return self.forms_invalid(forms)


class BaseMultipleFormView(MultipleFormMixin, ProcessMultipleFormView):
    pass


class MultipleFormView(TemplateResponseMixin, BaseMultipleFormView):
    pass


class MultipleFilterMixin:
    filterset_classes = []
    filterset_list = []

    def get_filterset_classes(self):
        return self.filterset_classes

    def get_filterset(self, filterset_class):
        # TODO: メソッドチェーンをやめる
        model_name = filterset_class._meta.model._meta.verbose_name
        kwargs = self.get_filterset_kwargs(filterset_class)
        return model_name, filterset_class(**kwargs)

    # noinspection PyUnresolvedReferences
    def get_filterset_kwargs(self, filterset_class):
        return {
            "data": self.request.GET,
            "request": self.request,
        }


class BaseMultipleFilterView(MultipleFilterMixin, MultipleObjectMixin, View):
    # noinspection PyAttributeOutsideInit,PyUnresolvedReferences
    def get(self, request, *args, **kwargs):
        filterset_classes = self.get_filterset_classes()
        self.filterset_list = [self.get_filterset(filterset_class) for filterset_class in filterset_classes]
        is_valid = all(filter_set.is_valid() for model_name, filter_set in self.filterset_list)

        if is_valid:
            self.object_list_list = [(model_name, filterset.qs) for model_name, filterset in self.filterset_list]
            count = sum(filterset.qs.count() for _, filterset in self.filterset_list)
        else:
            self.object_list_list = ()
            count = 0

        context = self.get_context_data(
            filter_list=self.filterset_list,
            object_list=self.object_list_list[0] if self.object_list_list else (),  # self.querysetを無理矢理定義するため
            object_list_list=self.object_list_list,
            count=count,
        )
        return self.render_to_response(context)


class MultipleFilterView(MultipleObjectTemplateResponseMixin, BaseMultipleFilterView):
    def get_template_names(self):
        # self.querysetが定義できないため、get_template_names()をオーバーライトしておく
        return [self.template_name]
