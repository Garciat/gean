import os.path
import subprocess
import tempfile

from gean import Container, includes


def test_readme_examples() -> None:
  with open('README.md', 'r') as f:
    readme = f.read()

  examples = []

  for chunk in readme.split('```python')[1:]:
    examples.append(chunk.split('```')[0])

  # tried using `exec` but type hint resolution was broken?
  with tempfile.TemporaryDirectory() as tmpdirname:
    for i, example in enumerate(examples):
      filename = 'example{}.py'.format(i + 1)
      filepath = os.path.join(tmpdirname, filename)

      with open(filepath, 'w') as f:
        f.write(example)

      subprocess.check_call(['python3', filepath])


def test_big_example() -> None:
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

