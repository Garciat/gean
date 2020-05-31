from gean import includes

import pytest  # type: ignore


def test_non_module() -> None:
  with pytest.raises(TypeError):
    @includes()
    class MissingSuffix: pass
