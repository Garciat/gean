from abc import ABC
import sys
from typing import Generic, TypeVar

from gean import AmbiguousDependencyError, Container, MissingDependencyError, includes

import pytest  # type: ignore


_T = TypeVar('_T')
_Tco = TypeVar('_Tco', covariant=True)
_Tcontra = TypeVar('_Tcontra', contravariant=True)


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


def test_re_register() -> None:
  class A: pass
  class B:
    def __init__(self) -> None: ...
  class XModule:
    def m(self) -> str: ...
  def func() -> int: ...
  singleton = 'hello'

  container = Container()
  container.register_instance(singleton)
  container.register_instance(singleton)
  container.register_class(A)
  container.register_class(A)
  container.register_class(B)
  container.register_class(B)
  container.register_module(XModule)
  container.register_module(XModule)
  container.register_callable(func)
  container.register_callable(func)


def test_class_autowired() -> None:
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


def test_class_constructor() -> None:
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


def test_class_constructor_kw_only() -> None:
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


def test_module_constructor() -> None:
  class A: pass
  class B:
    a: A

  class XModule:
    a: A
    def __init__(self, a: A):
      self.a = a
    def b(self) -> B:
      b = B()
      b.a = self.a
      return b

  container = Container()
  container.register_class(A)
  container.register_module(XModule)

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


def test_unbound_generic() -> None:
  class A(Generic[_T]): pass

  container = Container()

  # `A` is a generic type with unbound type parameters
  # so it is not registered as an interface for B
  with pytest.raises(TypeError):
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


def test_covariant() -> None:
  class A: pass
  class B(A): pass
  class C(B): pass

  class G(Generic[_Tco]): pass
  class P(G[B]): pass

  container = Container()
  container.register_class(P)

  p1 = container.resolve(G[A])
  p2 = container.resolve(G[B])

  assert p1 is container.resolve(P)
  assert p2 is container.resolve(P)

  with pytest.raises(MissingDependencyError):
    container.resolve(G[C])


def test_contravariant() -> None:
  class A: pass
  class B(A): pass
  class C(B): pass

  class G(Generic[_Tcontra]): pass
  class P(G[B]): pass

  container = Container()
  container.register_class(P)

  p1 = container.resolve(G[B])
  p2 = container.resolve(G[C])

  assert p1 is container.resolve(P)
  assert p2 is container.resolve(P)

  with pytest.raises(MissingDependencyError):
    container.resolve(G[A])
