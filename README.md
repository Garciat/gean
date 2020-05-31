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
container.resolve(A)
container.resolve(B[int])
container.resolve(C)
```

### Autowiring

```python
from gean import Container

class Subject:
  def work(self):
    print('working')

class Manager:
  subject: 'Subject'  # will be autowired
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

A module may declaratively `@include` other classes or modules.

```python
from gean import Container, includes

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

container = Container()
# No other dependencies need to be declared manually
# Because the modules do so declaratively
container.register_module(ApplicationModule)

container.resolve(Application).run()
```

### Singletons

```python
from gean import Container

container = Container()
# Both dependencies are of type `str`
container.register_instance('/tmp', name='tmp_dir')
container.register_instance('/home/garciat', tmp='user_dir')

# Disambiguate with name
container.resolve(str, name='tmp_dir')
```

## History

`gean` started off as [a gist](https://gist.github.com/Garciat/ad8a3afbb3cef141fcc500ae6ba96bf4) I created to show @alexpizarroj how my team leverages Spring in our projects.
