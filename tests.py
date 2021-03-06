import collections
import copy
import pickle

import pytest

from skin import Skin, SkinValueError


@pytest.fixture(scope="function")
def d():
    return dict(a=1, b=[1, 2, dict(a=1, b=2)], c=dict(a=dict(a=1)))


@pytest.fixture(scope="function")
def s(d):
    return Skin(d)


def test_get_known(d, s):
    assert s.a == 1
    assert s.b is not d["b"]
    assert s.b.value is d["b"]
    assert s.b[0] == 1
    assert s.b[-1] is not d["b"][-1]
    assert s.b[-1].value is d["b"][-1]
    assert s.b[-1].b == 2
    assert s.c is not d["c"]
    assert s.c.value is d["c"]
    assert s.c.a.a == 1
    assert s.value is d


def test_get_unknown(d, s):
    assert isinstance(s.foo, Skin)
    assert isinstance(s.foo.bar, Skin)
    assert isinstance(s.foo.bar[0].baz, Skin)
    assert "foo" not in d
    assert "foo" not in s
    assert s.foo is not s.foo


def test_set_known(d, s):
    s.a = "foo"
    assert s.a == "foo"
    assert d["a"] == "foo"
    assert s.a is d["a"]


def test_set_unknown(d, s):
    s.foo.bar[0].baz = "baz"
    assert s.foo.bar[0].baz == s["foo"]["bar"][0]["baz"]
    assert s.foo.bar[0].baz == d["foo"]["bar"][0]["baz"]


def test_no_getitem():
    with pytest.raises(SkinValueError):
        Skin(1)


def test_not_allowed():
    with pytest.raises(SkinValueError):
        Skin(dict(), allowed=(str,))


def test_forbidden():
    with pytest.raises(SkinValueError):
        Skin(dict(), forbidden=(dict,))


def test_skin_of_skin():
    s1 = Skin(dict(a=1))
    s2 = Skin(s1)
    assert s1.a is s2.a
    assert s1.a == s2.a == 1


def test_item_attribute(d, s):
    s.b.append(4)
    assert s.b[-1] == 4
    assert s.b[-1] is d["b"][-1]
    assert len(d["b"]) == 4


def test_magic_methods(d, s):
    assert len(s.b) == len(d["b"]) == 3
    assert set(s) == set(d)
    assert "b" in s
    assert 1 in s.b


def test_set_known_attribute():

    class A:

        def __init__(self):
            self.x = []

        def __getitem__(self, name):
            raise NotImplementedError

    a = A()
    s = Skin(a)
    assert a.x is s.x
    s.x = 2
    assert a.x is s.x


def test_del_known_attribute():

    class A:

        def __init__(self):
            self.x = []

        def __getitem__(self, name):
            raise NotImplementedError

    a = A()
    s = Skin(a)
    assert a.x is s.x
    del s.x
    with pytest.raises(AttributeError):
        print(a.x)


def test_del_known_value(d, s):
    del s.c
    with pytest.raises(KeyError):
        d["c"]
    assert isinstance(s.c, Skin)
    with pytest.raises(KeyError):
        d["c"]


def test_repr():
    s = Skin()
    assert repr(s) == "Skin({})"


def test_reversed(d, s):
    ls = list(reversed(s.b))[::-1]
    assert d["b"][:2] == ls[:2]
    assert d["b"][2] != ls[2]
    assert isinstance(ls[2], Skin)
    assert d["b"][2] == ls[2].value
    assert ls[2].a == 1


def test_defaultdict():
    d = collections.defaultdict(list)
    s = Skin(d)
    assert isinstance(s.foo.value, list)
    assert len(s) == 1
    s.bar.append(1)
    assert s.bar.value == [1]
    assert s.foo.value is d["foo"]
    assert s.bar.value is d["bar"]


def test_foo_copy():
    s = Skin()
    s.foo = []
    t = Skin(s.copy())
    u = copy.copy(s)
    assert s is not t
    assert s is not u
    assert s.foo.value is t.foo.value
    assert s.foo.value is u.foo.value


def test_deepcopy():
    s = Skin()
    s.foo = []
    t = copy.deepcopy(s)
    assert s.foo.value is not t.foo.value


def test_iteration(d, s):
    ls = list(s.b)
    assert d["b"][:2] == ls[:2]
    assert d["b"][2] != ls[2]
    assert isinstance(ls[2], Skin)
    assert d["b"][2] == ls[2].value
    assert ls[2].a == 1


def test_config_inheritance():
    s1 = Skin(forbidden=(set,))
    s2 = s1.foo.bar.baz
    assert super(Skin, s1).__getattribute__("forbidden") is super(Skin, s2).__getattribute__("forbidden")


def test_pickle(s):
    x = pickle.loads(pickle.dumps(s))
    assert x.value == s.value


def test_equality(s, d):
    s2 = Skin(d)
    assert s is not s2
    assert s == s2
    assert s != d
    assert s.value is s2.value
    assert s2.value is d
