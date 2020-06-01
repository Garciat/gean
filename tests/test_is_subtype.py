from typing import Generic, TypeVar

from gean import is_subtype


_T = TypeVar('_T')
_Tco = TypeVar('_Tco', covariant=True)
_Tcontra = TypeVar('_Tcontra', contravariant=True)


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
