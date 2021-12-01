class RedirectException(Exception):
    """リダイレクトさせるための例外"""

    def __init__(self, to):
        self.to = to
