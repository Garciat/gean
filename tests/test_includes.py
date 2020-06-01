from gean import includes

import pytest  # type: ignore


def test_ok() -> None:
  @includes()
  class MyModule: pass


def test_non_module() -> None:
  with pytest.raises(TypeError):
    @includes()
    class MissingSuffix: pass


def test_bad_include() -> None:
  with pytest.raises(TypeError):
    @includes('hello')  # type: ignore
    class MyModule: pass
