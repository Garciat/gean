# gean

A minimal IOC container inspired by Spring.

## Example

```python
from gean import Container, includes

class Michael:
  def speak(self):
    return 'what'

@includes(Michael)
class WhateverModule:
  def whatever(self) -> int:
    return 42

  def world(self) -> int:
    return 100

class Application:
  my_dir: str
  whatever: 'int'
  world: int
  m: Michael

  def start(self):
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

def _main():
  container = Container()
  container.register_instance('/etc/hello/world', name='config_dir')
  container.register_module(ApplicationModule)
  container.resolve(Application).start()

if __name__ == '__main__':
  _main()
```

## Requirements

`gean`, like Spring, relies on types and signatures to build and resolve the dependency graph.

Required language features: 
  - [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/) (Python 3.5+)
  - [PEP 526 - Syntax for Variable Annotations](https://www.python.org/dev/peps/pep-0526/) (Python 3.6+)

## Design

### Dependency registration

Each dependency of type `T` is registered not only as `T` but also as all of its implemented interfaces throguh its inheritance hierarchy.

Dependencies may be explicitly named if multiple of the same type are needed.

### Dependency kinds

**Instances**: the provided type is `type(instance)`

**Classes**: the provided type is `cls` itself

**Callables**: the provided type is `get_type_hints(callable)['return']`

**Modules**: for each public method of the module `m`, the provided type is `get_type_hints(m)['return']`. Additionally, each dependency is automatically _named_ after the module method that provides it.

## History

`gean` started off as [a gist](https://gist.github.com/Garciat/ad8a3afbb3cef141fcc500ae6ba96bf4) I created to show @alexpizarroj how my team leverages Spring in our projects.
