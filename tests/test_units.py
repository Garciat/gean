from gean import Container, includes

def test_autowired_class() -> None:
  class Autowired:
    s: str

  container = Container()
  container.register_instance('hello')
  container.register_class(Autowired)
  container.resolve(Autowired)

