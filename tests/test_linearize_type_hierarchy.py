from abc import ABC
from typing import Generic, TypeVar

from gean import linearize_type_hierarchy


_T = TypeVar('_T')
_Tco = TypeVar('_Tco', covariant=True)


def test_simple() -> None:
  class A: pass

  assert set(linearize_type_hierarchy(A)) == {A}


def test_derived() -> None:
  class A: pass
  class B(A): pass

  assert set(linearize_type_hierarchy(B)) == {B, A}


def test_diamond() -> None:
  class A: pass
  class B1(A): pass
  class B2(A): pass
  class C(B1, B2): pass

  assert set(linearize_type_hierarchy(C)) == {C, B1, B2, A}


def test_multiple_generic_bases() -> None:
  class A(Generic[_T]): pass
  class B(Generic[_T]): pass
  class C(A[int], B[Exception]): pass

  assert set(linearize_type_hierarchy(C)) == {C, A[int], B[Exception]}


def test_generic_with_normal_base() -> None:
  class Z: pass
  class A(Generic[_T], Z): pass
  class B(A[int]): pass

  assert set(linearize_type_hierarchy(B)) == {B, A[int], Z}


def test_abc() -> None:
  class A(ABC): pass
  class B(A): pass

  assert set(linearize_type_hierarchy(B)) == {B, A}


def test_covariant() -> None:
  class A: pass
  class B(A): pass
  class G(Generic[_Tco]): pass
  class P(G[B]): pass

  assert set(linearize_type_hierarchy(P)) == {P, G[B], G[A]}
