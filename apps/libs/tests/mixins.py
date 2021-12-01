from apps.libs.tests.utils import (
    ObjectItemList,
    _get_last_record,
    _normalize_for_display,
    _normalize_record,
    _set_form,
    get_heading,
    get_title,
    prepare_inputs,
)


class SingleInstanceTestMixin:
    def get_display_keys(self, instance):
        raise NotImplementedError("get_display_keys(self)を実装してください")  # pragma: no cover

    @staticmethod
    def assert_title(auth0_app, url, title):
        # 画面取得
        res = auth0_app.get(url)
        assert res.status_code == 200

        # タイトルの検証
        assert get_title(res) == title

    @staticmethod
    def assert_heading(auth0_app, url, heading):
        # 画面取得
        res = auth0_app.get(url)
        assert res.status_code == 200

        # 見出しの検証
        assert get_heading(res) == heading

    @staticmethod
    def assert_display(auth0_app, url, instance, display_keys):
        # 画面取得
        res = auth0_app.get(url)
        assert res.status_code == 200

        item_list = ObjectItemList(res.html.select("dl > dd"))
        texts = item_list.texts()
        expected_texts = []
        for display_key in display_keys:
            if hasattr(instance, f"get_{display_key}_display"):
                attr = getattr(instance, f"get_{display_key}_display")()
            else:
                attr = getattr(instance, display_key)
            expected_texts.append(_normalize_for_display(attr))

        assert texts == expected_texts, "表示内容が正しいこと"

    @staticmethod
    def assert_not_found(auth0_app, url):
        # 画面取得
        res = auth0_app.get(url, expect_errors=True)
        assert res.status_code == 404


class CreateInstanceTestMixin:
    def get_model(self):
        raise NotImplementedError("get_model(self)を実装してください")  # pragma: no cover

    def get_form_id(self):
        raise NotImplementedError("get_form_id(self)を実装してください")  # pragma: no cover

    def assert_minimum_inputs(self, auth0_app, url, success_url, minimum_inputs, assert_exclude_keys):
        """フォームの値を必要最小限の値のみ埋めたときのテスト"""
        # フォームに入れる値の準備
        minimum_inputs = prepare_inputs(minimum_inputs)

        # 検証に使用するため、レコード数を保存
        before_count = self.get_model().objects.count()

        # 画面取得
        res = auth0_app.get(url)
        assert res.status_code == 200

        # フォーム入力
        form = res.forms[self.get_form_id()]
        _set_form(form, minimum_inputs)

        # 送信正常 & 次の画面に移動
        res = form.submit()
        assert res.status_code == 302
        assert res.location == success_url

        # レコードの中身確認
        assert self.get_model().objects.count() == before_count + 1, "レコード数が1つ増えていること"
        record = _get_last_record(self.get_model())

        record_values, input_values = _normalize_record(minimum_inputs, record, assert_exclude_keys)
        assert record_values == input_values

        self.after_test_minimum_inputs(record)

    def after_test_minimum_inputs(self, record):
        pass

    def assert_maximum_inputs(self, auth0_app, url, success_url, maximum_inputs, assert_exclude_keys):
        """フォームの値を全部埋めたときのテスト"""
        # フォームに入れる値の準備
        maximum_inputs = prepare_inputs(maximum_inputs)

        # 検証に使用するため、レコード数を保存
        before_count = self.get_model().objects.count()

        # 画面取得
        res = auth0_app.get(url)
        assert res.status_code == 200

        # フォーム入力
        form = res.forms[self.get_form_id()]
        _set_form(form, maximum_inputs)

        # 送信正常 & 次の画面に移動
        res = form.submit()
        assert res.status_code == 302
        assert res.location == success_url

        # レコードの中身確認
        assert self.get_model().objects.count() == before_count + 1, "レコード数が1つ増えていること"
        record = _get_last_record(self.get_model())

        input_values, record_values = _normalize_record(maximum_inputs, record, assert_exclude_keys)
        assert record_values == input_values

    def assert_required(self, auth0_app, url, maximum_inputs, required_key):
        """必須項目が足りてない場合のテスト"""
        # フォームに入れる値の準備
        maximum_inputs = prepare_inputs(maximum_inputs)

        # 画面取得
        res = auth0_app.get(url)
        assert res.status_code == 200

        # フォーム入力
        form = res.forms[self.get_form_id()]
        _set_form(form, maximum_inputs)

        # 必須項目を空にする(choicesがある場合セットできないため、force_valueを使う)
        form[required_key].force_value("")

        # 送信するとエラーで戻ってくる
        res = form.submit()
        assert res.status_code == 200
