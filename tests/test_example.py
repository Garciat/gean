from gean import Container, includes

def test_example() -> None:
  class Michael:
    def speak(self) -> str:
      return 'what'

  @includes(Michael)
  class WhateverModule:
    def whatever(self) -> int:
      return 42

    def poop(self) -> int:
      return 100

  class Application:
    my_dir: str
    whatever: 'int'
    poop: int
    m: Michael

    def start(self) -> None:
      print(self.my_dir)
      print(self.whatever)
      print(self.poop)
      print(self.m.speak())

  @includes(
    WhateverModule,
    Application,
    Michael,
  )
  class ApplicationModule:
    config_dir: str

    def another_dir(self) -> str:
      return self.config_dir + '/another'

    def my_dir(self, another_dir: 'str') -> str:
      return another_dir + '/ñe'

  container = Container()
  container.register_instance('/etc/hello/world', name='config_dir')
  container.register_module(ApplicationModule)
  container.resolve(Application).start()

