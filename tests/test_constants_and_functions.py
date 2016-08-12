import pytest


def test_constants():
    from pybind11_tests import some_constant

    assert some_constant == 14


def test_function_overloading(capture):
    from pybind11_tests import EMyEnumeration, test_function

    with capture:
        assert test_function() is False
        assert test_function(7) == 3.5
        assert test_function(EMyEnumeration.EFirstEntry) is None
        assert test_function(EMyEnumeration.ESecondEntry) is None
    assert capture == """
        test_function()
        test_function(7)
        test_function(enum=1)
        test_function(enum=2)
    """


def test_unscoped_enum():
    from pybind11_tests import EMyEnumeration, EFirstEntry

    assert str(EMyEnumeration.EFirstEntry) == "EMyEnumeration.EFirstEntry"
    assert str(EMyEnumeration.ESecondEntry) == "EMyEnumeration.ESecondEntry"
    assert str(EFirstEntry) == "EMyEnumeration.EFirstEntry"

    # no TypeError exception for unscoped enum ==/!= int comparisons
    y = EMyEnumeration.ESecondEntry
    assert y == 2
    assert y != 3

    assert int(EMyEnumeration.ESecondEntry) == 2
    assert str(EMyEnumeration(2)) == "EMyEnumeration.ESecondEntry"


def test_scoped_enum(capture):
    from pybind11_tests import ECMyEnum, test_ecenum

    with capture:
        test_ecenum(ECMyEnum.Three)
    assert capture == "test_ecenum(ECMyEnum::Three)"
    z = ECMyEnum.Two
    with capture:
        test_ecenum(z)
    assert capture == "test_ecenum(ECMyEnum::Two)"

    # expected TypeError exceptions for scoped enum ==/!= int comparisons
    with pytest.raises(TypeError):
        assert z == 2
    with pytest.raises(TypeError):
        assert z != 3


def test_implicit_conversion(capture):
    from pybind11_tests import ExampleWithEnum

    assert str(ExampleWithEnum.EMode.EFirstMode) == "EMode.EFirstMode"
    assert str(ExampleWithEnum.EFirstMode) == "EMode.EFirstMode"

    f = ExampleWithEnum.test_function
    first = ExampleWithEnum.EFirstMode
    second = ExampleWithEnum.ESecondMode

    with capture:
        f(first)
    assert capture == "ExampleWithEnum::test_function(enum=1)"

    with capture:
        assert f(first) == f(first)
        assert not f(first) != f(first)

        assert f(first) != f(second)
        assert not f(first) == f(second)

        assert f(first) == int(f(first))
        assert not f(first) != int(f(first))

        assert f(first) != int(f(second))
        assert not f(first) == int(f(second))
    assert capture == """
        ExampleWithEnum::test_function(enum=1)
        ExampleWithEnum::test_function(enum=1)
        ExampleWithEnum::test_function(enum=1)
        ExampleWithEnum::test_function(enum=1)
        ExampleWithEnum::test_function(enum=1)
        ExampleWithEnum::test_function(enum=2)
        ExampleWithEnum::test_function(enum=1)
        ExampleWithEnum::test_function(enum=2)
        ExampleWithEnum::test_function(enum=1)
        ExampleWithEnum::test_function(enum=1)
        ExampleWithEnum::test_function(enum=1)
        ExampleWithEnum::test_function(enum=1)
        ExampleWithEnum::test_function(enum=1)
        ExampleWithEnum::test_function(enum=2)
        ExampleWithEnum::test_function(enum=1)
        ExampleWithEnum::test_function(enum=2)
    """

    with capture:
        # noinspection PyDictCreation
        x = {f(first): 1, f(second): 2}
        x[f(first)] = 3
        x[f(second)] = 4
    assert capture == """
        ExampleWithEnum::test_function(enum=1)
        ExampleWithEnum::test_function(enum=2)
        ExampleWithEnum::test_function(enum=1)
        ExampleWithEnum::test_function(enum=2)
    """
    # Hashing test
    assert str(x) == "{EMode.EFirstMode: 3, EMode.ESecondMode: 4}"


def test_bytes(capture):
    from pybind11_tests import return_bytes, print_bytes

    with capture:
        print_bytes(return_bytes())
    assert capture == """
        bytes[0]=1
        bytes[1]=0
        bytes[2]=2
        bytes[3]=0
    """
