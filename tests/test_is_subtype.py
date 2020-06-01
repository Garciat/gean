from typing import Generic, TypeVar

from gean import is_subtype


_T = TypeVar('_T')
_U = TypeVar('_U')
_Tco = TypeVar('_Tco', covariant=True)
_Tcontra = TypeVar('_Tcontra', contravariant=True)


def test_generic_with_normal_base() -> None:
  class A: pass
  class B(Generic[_T], A): pass

  assert is_subtype(B[int], A)


def test_partial_generic() -> None:
  class G(Generic[_T, _U]): pass
  class H(Generic[_T]): pass

  class A(Generic[_T], G[int, _T]): pass
  class B(Generic[_T], A[_T], H[int]): pass
  class C(B[str]): pass

  assert is_subtype(C, B[str])
  assert is_subtype(C, A[str])
  assert is_subtype(C, G[int, str])
  assert is_subtype(C, H[int])

  assert is_subtype(B[bool], A[bool])
  assert is_subtype(B[bool], H[int])
  assert is_subtype(B[bool], G[int, bool])


def test_disjoint() -> None:
  class G(Generic[_T]): pass
  class H(Generic[_T]): pass

  class P(G[int], H[str]): pass

  assert is_subtype(P, G[int])
  assert is_subtype(P, H[str])


def test_covariance() -> None:
  class A: pass
  class B(A): pass
  class C(B): pass

  class G(Generic[_Tco]): pass
  class P(G[B]): pass

  assert is_subtype(P, P)
  assert is_subtype(P, G[A])
  assert is_subtype(P, G[B])

  assert not is_subtype(P, G[C])


def test_complex_variance() -> None:
  class A: pass
  class B(A): pass
  class C(B): pass

  class R: pass
  class S(R): pass
  class T(S): pass

  class G(Generic[_Tco, _Tcontra]): pass
  class H(Generic[_Tco]): pass

  class P(G[H[B], H[S]]): pass

  assert is_subtype(P, G[H[B], H[S]])
  assert is_subtype(P, G[H[A], H[S]])
  assert is_subtype(P, G[H[B], H[T]])
  assert is_subtype(P, G[H[A], H[T]])

  assert not is_subtype(P, G[H[C], H[S]])
  assert not is_subtype(P, G[H[B], H[R]])
  assert not is_subtype(P, G[H[C], H[R]])
