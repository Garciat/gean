from typing import Generic, TypeVar

from gean import linearize_type_hierarchy


_T = TypeVar('_T')


def test_generic_with_normal_base() -> None:
  class Z: pass
  class A(Generic[_T], Z): pass
  class B(A[int]): pass

  assert set(linearize_type_hierarchy(B)) == {B, A[int], Z}
