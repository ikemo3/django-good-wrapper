from apps.libs.tests.base import GenericTest, GenericTestNoDB
from apps.libs.tests.copy import GenericTestCopy, GenericTestMove
from apps.libs.tests.dashboard import GenericTestDashboard
from apps.libs.tests.dates import GenericTestLatestMonthRedirect, GenericTestLatestYearRedirect, GenericTestMonthArchive
from apps.libs.tests.detail import GenericTestDetail
from apps.libs.tests.edit import GenericTestAdd, GenericTestDelete, GenericTestDeleteList, GenericTestEdit
from apps.libs.tests.list import GenericTestChildList, GenericTestList
from apps.libs.tests.misc import GenericTestFilter, GenericTestSort
from apps.libs.tests.models import GenericTestInconsistency, GenericTestModel, GenericTestQuerySet

__all__ = [
    # base
    "GenericTest",
    "GenericTestNoDB",
    # copy
    "GenericTestCopy",
    "GenericTestMove",
    # dashboard,
    "GenericTestDashboard",
    # dates
    "GenericTestMonthArchive",
    "GenericTestLatestMonthRedirect",
    "GenericTestLatestYearRedirect",
    # detail
    "GenericTestDetail",
    # edit
    "GenericTestAdd",
    "GenericTestEdit",
    "GenericTestDelete",
    "GenericTestDeleteList",
    # list
    "GenericTestList",
    "GenericTestChildList",
    # misc
    "GenericTestFilter",
    "GenericTestSort",
    # model
    "GenericTestInconsistency",
    "GenericTestModel",
    "GenericTestQuerySet",
]
