from gean import AmbiguousDependencyError, Container, includes
import pytest  # type: ignore

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
