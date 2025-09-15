"""统一后端组合入口。"""


def create_app(*args, **kwargs):
    from apps.backend_app.app import create_app as _create_app

    return _create_app(*args, **kwargs)


__all__ = ["create_app"]
