from overload_web import __version__, __title__  # type: ignore


def test_version():
    assert __version__ == "0.1.0"


def test_title():
    assert __title__ == "Overload-Web"
