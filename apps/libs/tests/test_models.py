from apps.libs.db.models import NoteField
from apps.libs.tests import GenericTest


class TestNoteField(GenericTest):
    def test_default(self):
        note = NoteField()
        name, path, args, kwargs = note.deconstruct()

        # noinspection PyArgumentList
        new_note = NoteField(*args, **kwargs)

        assert note.max_length == new_note.max_length
        assert note.verbose_name == new_note.verbose_name
        assert note.null == new_note.null
        assert note.default == new_note.default

    def test_fields(self):
        note = NoteField(max_length=500, verbose_name="備考1", blank=False, null=True, default="abc")
        name, path, args, kwargs = note.deconstruct()

        # noinspection PyArgumentList
        new_note = NoteField(*args, **kwargs)

        assert note.max_length == new_note.max_length
        assert note.verbose_name == new_note.verbose_name
        assert note.null == new_note.null
        assert note.default == new_note.default

        assert note.max_length == 500
        assert note.verbose_name == "備考1"
        assert note.blank is False
        assert note.null is True
        assert note.default == "abc"
