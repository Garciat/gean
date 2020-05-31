[![PyPI version](https://badge.fury.io/py/gean.svg)](https://badge.fury.io/py/gean)
[![Build Status](https://travis-ci.org/Garciat/gean.svg?branch=master)](https://travis-ci.org/Garciat/gean)
[![codecov](https://codecov.io/gh/Garciat/gean/branch/master/graph/badge.svg)](https://codecov.io/gh/Garciat/gean)

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

A dependency of a given type `X` is exposed not only as `X` but also all of its super types, including generic interfaces.

```python
from gean import Container
from typing import Generic, TypeVar

_T = TypeVar('_T')

class A: pass
class B(Generic[_T]): pass
class C(A, B[int]): pass

container = Container()
container.register_class(C)

# All of these return the same instance of C
c1 = container.resolve(A)
c2 = container.resolve(B[int])
c3 = container.resolve(C)
assert c1 is c2 is c3
assert isinstance(c1, C)
```

### Caching

All dependencies are cached as they are constructed.

```python
from gean import Container

class A: pass

container = Container()
container.register_class(A)

a1 = container.resolve(A)
a2 = container.resolve(A)
assert a1 is a2
```

### Autowiring

Dependencies can be autowired if a class does not declare an explicit constructor.

Field names can disambiguate same-type dependencies.

```python
from gean import Container

class Subject:
  def work(self):
    print('working')

class Manager:
  subject: Subject  # will be autowired
  def run(self):
    self.subject.work()

container = Container()
# Order of registration does not matter
container.register_class(Manager)
container.register_class(Subject)

# This prints 'working'
container.resolve(Manager).run()
```

### Constructor wiring

If a class defines an explicit constructor, dependencies will be passed as arguments.

Parameter names can disambiguate same-type dependencies.

```python
from gean import Container

class Subject:
  def work(self):
    print('working')

class Manager:
  def __init__(self, subject: Subject):
    self.subject = subject
  def run(self):
    self.subject.work()

container = Container()
# Order of registration does not matter
container.register_class(Manager)
container.register_class(Subject)

# This prints 'working'
container.resolve(Manager).run()
```

### Modules

A **module** is a class whose name ends in `Module`.

A module may use `@includes` to declaratively register other classes or modules.

A module may use public methods to create dependencies programmatically.

```python
from gean import Container, includes

class PingService:
  def ping(self, addr): ...

class DNSService:
  def resolve(self, name): ...

@includes(
  DNSService,
  PingService,
)
class NetworkModule: pass

class AppConfig: pass

class Application:
  config: AppConfig
  dns_service: DNSService
  ping_service: PingService
  def run(self):
    print(self.config)
    self.ping_service.ping(self.dns_service.resolve('garciat.com'))

def load_configuration() -> AppConfig: ...

@includes(
  NetworkModule,
  Application,
)
class ApplicationModule:
  # Create config programmatically
  def config(self) -> AppConfig:
    return load_configuration()

container = Container()
# No other dependencies need to be declared manually
# Because the modules do so declaratively
container.register_module(ApplicationModule)

container.resolve(Application).run()
```

### Singletons

Dependencies can be explicitly named so that disambiguation is possible.

```python
from gean import Container

container = Container()
# Both dependencies are of type `str`
container.register_instance('/tmp', name='tmp_dir')
container.register_instance('/home/garciat', name='user_dir')

# Disambiguate with name
container.resolve(str, name='tmp_dir')
```

## History

`gean` started off as [a gist](https://gist.github.com/Garciat/ad8a3afbb3cef141fcc500ae6ba96bf4) I created to show @alexpizarroj how my team leverages Spring in our projects.
