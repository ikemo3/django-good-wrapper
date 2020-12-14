class TableViewModelMixin:
    @staticmethod
    def display_as():
        return "table"

    @staticmethod
    def headers():
        raise NotImplementedError("headersを定義してください")

    def columns(self):
        raise NotImplementedError("columnsを定義してください")


class GroupedModelMixin:
    @staticmethod
    def display_as():
        return "grouping"

    def group_by(self):
        raise NotImplementedError("group_byを定義してください")
