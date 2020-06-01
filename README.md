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

A dependency of a given type `X` is exposed not only as `X` but also all of its super types, including generic interfaces. Variance is supported on generic types.

#### Regular inheritance

```python
from abc import ABC
from gean import Container

# Works with or without ABC
class Worker(ABC): pass
class WorkerImpl(Worker): pass

container = Container()
container.register_class(WorkerImpl)

# All of these return the same instance
c1 = container.resolve(WorkerImpl)
c2 = container.resolve(Worker)
assert c1 is c2
assert isinstance(c1, WorkerImpl)
```

#### Covariance

```python
from gean import Container
from typing import Generic, TypeVar

_Tco = TypeVar('_Tco', covariant=True)

class Person: pass
class Student(Person): pass

class Factory(Generic[_Tco]): pass

class StudentFactory(Factory[Student]): pass

container = Container()
container.register_class(StudentFactory)

# All of these return the same instance
c1 = container.resolve(StudentFactory)
c2 = container.resolve(Factory[Student])
c3 = container.resolve(Factory[Person])
assert c1 is c2 is c3
assert isinstance(c1, StudentFactory)
```

#### Contravariance

```python
from gean import Container
from typing import Generic, TypeVar

_Tcontra = TypeVar('_Tcontra', contravariant=True)

class Person: pass
class Student(Person): pass

class Validator(Generic[_Tcontra]): pass

class PersonValidator(Validator[Person]): pass

container = Container()
container.register_class(PersonValidator)

# All of these return the same instance
c1 = container.resolve(PersonValidator)
c2 = container.resolve(Validator[Student])
c3 = container.resolve(Validator[Person])
assert c1 is c2 is c3
assert isinstance(c1, PersonValidator)
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

## Alternatives

As of June 1 2020, this is a non-exhaustive list of alternative solutions that also leverage Type Hints.

### [injector](https://github.com/alecthomas/injector)

  - Does not support hierarchy with generic interfaces

<!-- do not add syntax highlighting, otherwise it will be executed -->
```
from typing import Generic, TypeVar

from injector import Injector, Module, inject, provider, singleton


_T = TypeVar('_T')

class A(Generic[_T]): pass
class B(A[int]): pass

class C:
  @inject
  def __init__(self, a: A[int]):
    self.a = a


class MyModule(Module):
  @singleton
  @provider
  def provide_b(self) -> B:  # works if return type is A[int] explicitly
    return B()


i = Injector([MyModule])

# injector.UnknownProvider: couldn't determine provider for __main__.A[int] to None
i.get(C)
```

### [bobthemighty/punq](https://github.com/bobthemighty/punq)

  - Does not support type hierarchies

### [jbasko/auto-init](https://github.com/jbasko/auto-init)

  - Performs default initialization. E.g. `0` for `int`, `None` for objects
  - Does not support generic interfaces

### [asyncee/wint](https://github.com/asyncee/wint)

  - Global state

## History

`gean` started off as [a gist](https://gist.github.com/Garciat/ad8a3afbb3cef141fcc500ae6ba96bf4) I created to show @alexpizarroj how my team leverages Spring in our projects.
