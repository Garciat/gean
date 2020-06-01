from abc import ABC
import sys
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
  class A: pass
  class B:
    a: A

  container = Container()
  container.register_class(A)
  container.register_class(B)

  b = container.resolve(B)

  assert isinstance(b, B)
  assert isinstance(b.a, A)
  assert b.a is container.resolve(A)


def test_constructor_class() -> None:
  class A: pass
  class B:
    def __init__(self, a: A):
      self.a = a

  container = Container()
  container.register_class(A)
  container.register_class(B)

  b = container.resolve(B)

  assert isinstance(b, B)
  assert isinstance(b.a, A)
  assert b.a is container.resolve(A)


def test_constructor_class_kw_only() -> None:
  class A: pass
  class B:
    def __init__(self, *, a: A):
      self.a = a

  container = Container()
  container.register_class(A)
  container.register_class(B)

  b = container.resolve(B)

  assert isinstance(b, B)
  assert isinstance(b.a, A)
  assert b.a is container.resolve(A)


if sys.version_info >= (3, 7):
  def test_constructor_dataclass() -> None:
    from dataclasses import dataclass

    class A: pass
    @dataclass(frozen=True)
    class B:
      a: A

    container = Container()
    container.register_class(A)
    container.register_class(B)

    b = container.resolve(B)

    assert isinstance(b, B)
    assert isinstance(b.a, A)
    assert b.a is container.resolve(A)


def test_callable() -> None:
  class A: pass
  class B:
    a: A
    s: str

  secret = 'from callable'

  def hello(a: A) -> B:
    b = B()
    b.a = a
    b.s = secret
    return b

  container = Container()
  container.register_class(A)
  container.register_callable(hello)

  b = container.resolve(B)

  assert isinstance(b, B)
  assert isinstance(b.a, A)
  assert b.a is container.resolve(A)
  assert b.s is secret


def test_callable_kw_only() -> None:
  class A: pass
  class B:
    a: A

  def hello(*, a: A) -> B:
    b = B()
    b.a = a
    return b

  container = Container()
  container.register_class(A)
  container.register_callable(hello)

  b = container.resolve(B)

  assert isinstance(b, B)
  assert isinstance(b.a, A)
  assert b.a is container.resolve(A)


def test_abc() -> None:
  class A(ABC): pass
  class B(A): pass

  container = Container()
  container.register_class(B)

  b = container.resolve(A)

  assert isinstance(b, B)


def test_ambiguous_supertype() -> None:
  class A: pass
  class B1(A): pass
  class B2(A): pass

  container = Container()
  container.register_class(B1)
  container.register_class(B2)

  with pytest.raises(AmbiguousDependencyError):
    container.resolve(A)


def test_generic_base() -> None:
  class A(Generic[_T]): pass
  class B(A[int]): pass

  container = Container()
  container.register_class(B)

  a_int = container.resolve(A[int])

  assert isinstance(a_int, B)

  # `A` is a generic type with unbound type parameters
  # so it is not registered as an interface for B
  with pytest.raises(MissingDependencyError):
    container.resolve(A)


def test_generic_return() -> None:
  class A(Generic[_T]): pass
  class B1(A[int]): pass
  class B2(A[str]): pass

  class XModule:
    def b1(self) -> A[int]:
      return B1()
    def b2(self) -> A[str]:
      return B2()

  container = Container()
  container.register_module(XModule)

  a_int = container.resolve(A[int])
  assert isinstance(a_int, B1)

  a_str = container.resolve(A[str])
  assert isinstance(a_str, B2)
