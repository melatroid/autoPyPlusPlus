import builtins
import test_01_no_gui
import pytest

def test_main(monkeypatch, capsys):
    monkeypatch.setattr(builtins, "input", lambda _: "")
    test_01_no_gui.main()
    captured = capsys.readouterr()
    assert "Without a gui - test successfully" in captured.out

@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 5, 4),
])
def test_add(a, b, expected):
    assert test_01_no_gui.add(a, b) == expected

@pytest.mark.parametrize("x, y, result", [
    (2, 3, 6),
    (-1, 8, -8),
    (0, 5, 0),
])
def test_multiply(x, y, result):
    assert test_01_no_gui.multiply(x, y) == result

def test_divide_normal():
    assert test_01_no_gui.divide(10, 2) == 5

def test_divide_zero():
    with pytest.raises(ValueError):
        test_01_no_gui.divide(5, 0)

@pytest.mark.parametrize("name, greeting", [
    ("Alice", "Hello, Alice!"),
    ("Bob", "Hello, Bob!"),
    ("", "Hello, !"),
])
def test_greet(name, greeting):
    assert test_01_no_gui.greet(name) == greeting

@pytest.mark.parametrize("n, expected", [
    (2, True),
    (7, False),
    (0, True),
    (-2, True),
])
def test_is_even(n, expected):
    assert test_01_no_gui.is_even(n) == expected
