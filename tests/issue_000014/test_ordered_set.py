from random import shuffle

from pytest import raises

from typefit.utils import OrderedSet


def test_init():
    s = OrderedSet([1, 2, 3])
    assert s._set == {1: True, 2: True, 3: True}


def test_add():
    s = OrderedSet()

    s.add(1)
    assert s._set == {1: True}

    s.add(2)
    assert s._set == {1: True, 2: True}


def test_order_init():
    s = OrderedSet(range(1000))
    assert [*s] == [*range(1000)]


def test_order_add():
    s = OrderedSet()

    for i in range(1000):
        s.add(i)

    assert [*s] == [*range(1000)]


def test_order_shuffle_add():
    s = OrderedSet(range(1000))

    insert = [*range(1000), *range(500), *range(700), *range(200)]
    shuffle(insert)

    for i in insert:
        s.add(i)

    assert [*s] == [*range(1000)]


def test_discard():
    s = OrderedSet([1])
    s.discard(1)
    assert [*s] == []
    s.discard(1)
    assert [*s] == []


def test_remove():
    s = OrderedSet([1])
    s.remove(1)
    assert [*s] == []

    with raises(KeyError):
        s.remove(1)


def test_union():
    s1 = OrderedSet(range(500))
    s2 = OrderedSet(range(200, 1000))
    s = s1 | s2

    assert [*s] == [*range(1000)]


def test_intersect():
    s1 = OrderedSet(range(500))
    s2 = OrderedSet(range(400, 1000))
    s = s1 & s2

    assert [*s] == [*range(400, 500)]


def test_subtract():
    s1 = OrderedSet(range(500))
    s2 = OrderedSet(range(400))
    s = s1 - s2

    assert [*s] == [*range(400, 500)]
