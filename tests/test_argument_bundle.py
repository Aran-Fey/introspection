import pytest

from introspection import ArgumentBundle


@pytest.mark.parametrize(
    "func, args, kwargs, expected",
    [
        (int, ["12"], {}, 12),
        (bytes, ["hi"], {"encoding": "utf8"}, b"hi"),
    ],
)
def test_call(func, args, kwargs, expected):
    bundle = ArgumentBundle(*args, **kwargs)

    assert bundle.call(func) == expected


@pytest.mark.parametrize(
    "args, kwargs, expected",
    [
        ([12], {}, "(12)"),
        (["hi"], {"encoding": "utf8"}, "('hi', encoding='utf8')"),
    ],
)
def test_str(args, kwargs, expected):
    bundle = ArgumentBundle(*args, **kwargs)

    assert str(bundle) == expected


@pytest.mark.parametrize(
    "args, kwargs, expected",
    [
        ([12], {}, "ArgumentBundle(12)"),
        (["hi"], {"encoding": "utf8"}, "ArgumentBundle('hi', encoding='utf8')"),
    ],
)
def test_repr(args, kwargs, expected):
    bundle = ArgumentBundle(*args, **kwargs)

    assert repr(bundle) == expected
