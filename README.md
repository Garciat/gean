[![PyPI version](https://badge.fury.io/py/gean.svg)](https://badge.fury.io/py/gean)
[![Build Status](https://travis-ci.org/Garciat/gean.svg?branch=master)](https://travis-ci.org/Garciat/gean)

# gean

A minimal IOC container inspired by Spring.

## Install

```
python3 -m pip install gean
```

## Requirements

`gean`, like Spring, relies on types and signatures to build and resolve the dependency graph.

Required language features: 
  - [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/) (Python 3.5+)
  - [PEP 526 - Syntax for Variable Annotations](https://www.python.org/dev/peps/pep-0526/) (Python 3.6+)

## Features

### Type hierarchies

A dependency of given type `X` is exposed not only as `X` but also all of its super types, including generic interfaces.

```python
class A: pass
class B(Generic[T]): pass
class C(A, B[int]): pass

container.register_class(C)
# All of these return an instance of C
container.resolve(A)
container.resolve(B[int])
container.resolve(C)
```

### Autowiring

```python
class Manager:
  subject: Subject  # will be autowired
  def run(self):
    self.subject.work()

class Subject:
  def work(self):
    print('working')

# Order of registration does not matter
container.register_class(Manager)
container.register_class(Subject)

# This prints 'working'
container.resolve(Manager).run()
```

### Modules

A **module** is a class whose name ends in `Module`.

A module may declaratively `@include` other classes or modules.

```python
class PingService:
  def ping(self, addr): ...

class DNSService:
  def resolve(self, name): ...

@include(
  DNSService,
  PingService,
)
class NetworkModule: pass

def Application:
  dns_service: DNSService
  ping_service: PingService
  def run(self):
    ping_service.ping(dns_service.resolve('garciat.com'))

@include(
  NetworkModule,
  Application,
)
class ApplicationModule: pass

# No other dependencies need to be declared manually
# Because the modules do so declaratively
container.register_module(ApplicationModule)

container.resolve(Application).run()
```

### Singletons

```python
# Both dependencies are of type `str`
container.register_instance('/tmp', name='tmp_dir')
container.register_instance('/home/garciat', tmp='user_dir')

# Disambiguate with name
container.resolve(str, name='tmp_dir')
```

## Usage

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
    print(self.world)
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

## History

`gean` started off as [a gist](https://gist.github.com/Garciat/ad8a3afbb3cef141fcc500ae6ba96bf4) I created to show @alexpizarroj how my team leverages Spring in our projects.
