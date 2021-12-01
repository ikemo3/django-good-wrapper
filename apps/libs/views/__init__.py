from apps.libs.views.base import GenericRedirectView, GenericTemplateView, GenericView
from apps.libs.views.dates import (
    GenericLatestMonthRedirectView,
    GenericLatestYearRedirectView,
    GenericMonthArchiveView,
    GenericYearArchiveView,
)
from apps.libs.views.detail import GenericDetailView
from apps.libs.views.edit import (
    GenericAddView,
    GenericBulkFormView,
    GenericDeleteListView,
    GenericDeleteView,
    GenericEditView,
    GenericInlineFormsetView,
    GenericSortView,
    GenericStatusUpdateView,
)
from apps.libs.views.list import GenericChildListView, GenericListView
from apps.libs.views.misc import GenericFilterView

__all__ = [
    # base
    "GenericRedirectView",
    "GenericView",
    "GenericTemplateView",
    # dates
    "GenericMonthArchiveView",
    "GenericYearArchiveView",
    "GenericLatestMonthRedirectView",
    "GenericLatestYearRedirectView",
    # detail
    "GenericDetailView",
    # edit
    "GenericAddView",
    "GenericBulkFormView",
    "GenericEditView",
    "GenericStatusUpdateView",
    "GenericDeleteListView",
    "GenericDeleteView",
    "GenericSortView",
    "GenericInlineFormsetView",
    # list
    "GenericListView",
    "GenericChildListView",
    # misc
    "GenericFilterView",
]
