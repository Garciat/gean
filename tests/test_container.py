from typing import Generic, TypeVar

from gean import AmbiguousDependencyError, Container, MissingDependencyError, includes
import pytest  # type: ignore


_T = TypeVar('_T')


def test_missing() -> None:
  container = Container()
  with pytest.raises(MissingDependencyError):
    container.resolve(str)


def test_autowired_class() -> None:
  class Autowired:
    s: str

  container = Container()
  container.register_instance('hello')
  container.register_class(Autowired)
  container.resolve(Autowired)


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
  class A(Generic[_T]): pass
  class B(A[int]): pass

  container = Container()
  container.register_class(B)
  container.resolve(A[int])
