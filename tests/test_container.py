from typing import Generic, TypeVar

from gean import AmbiguousDependencyError, Container, MissingDependencyError, includes
import pytest  # type: ignore


_T = TypeVar('_T')


def test_missing() -> None:
  container = Container()
  with pytest.raises(MissingDependencyError):
    container.resolve(str)


def test_cache() -> None:
  class A: pass

  container = Container()
  container.register_class(A)

  a1 = container.resolve(A)
  a2 = container.resolve(A)

  assert a1 is a2


def test_autowired_class() -> None:
  class Autowired:
    s: str

  container = Container()
  container.register_instance('hello')
  container.register_class(Autowired)
  container.resolve(Autowired)


def test_constructor_class() -> None:
  class A: pass
  class B:
    def __init__(self, a: A):
      self._a = a

  str_instance = 'hello'

  container = Container()
  container.register_class(A)
  container.register_class(B)

  a = container.resolve(A)
  b = container.resolve(B)

  assert b._a is a


def test_hierarchy() -> None:
  class A: pass
  class B(A): pass
  class C(A): pass

  container = Container()
  container.register_class(B)
  container.register_class(C)
  container.resolve(B)
  container.resolve(C)

  with pytest.raises(AmbiguousDependencyError):
    container.resolve(A)


def test_generic_base() -> None:
  class A: pass
  class B(Generic[_T]): pass
  class C(A, B[int]): pass

  container = Container()
  container.register_class(C)
  c = container.resolve(C)

  assert isinstance(c, C)
  assert container.resolve(A) is c
  assert container.resolve(B[int]) is c


def test_generic_return() -> None:
  class A(Generic[_T]): pass
  class B(A[int]): pass
  class C(A[str]): pass

  class XModule:
    def b(self) -> A[int]:
      return B()
    def c(self) -> A[str]:
      return C()

  container = Container()
  container.register_module(XModule)

  a_int = container.resolve(A[int])
  assert isinstance(a_int, B)

  a_str = container.resolve(A[str])
  assert isinstance(a_str, C)

  # `A` is a generic type with unbound type parameters
  # so it is not registered as an interface for B or C
  with pytest.raises(MissingDependencyError):
    container.resolve(A)
