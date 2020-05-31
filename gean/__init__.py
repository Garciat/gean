from abc import ABC
from abc import abstractmethod
from abc import abstractproperty
import inspect
from typing import Any
from typing import Callable
from typing import ClassVar
from typing import Dict
from typing import Generic
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import Union
from typing import cast
from typing import get_type_hints


__all__ = ['Container', 'includes']


_C = TypeVar('_C')
_T = TypeVar('_T')


class _Unreachable(Exception): pass


def get_constructor(cls: Type[_T]) -> Callable[..., _T]:
  return cast(Callable[..., _T], getattr(cls, '__init__'))


def is_custom_constructor(constructor: Callable[..., _T]) -> bool:
  return constructor is not object.__init__


def linearize_type_hierarchy(root: type) -> Iterable[type]:
  if root is object:
    return
  yield root
  for node in inspect.getclasstree([root]):
    if isinstance(node, tuple):
      parent, _ = node
      yield from linearize_type_hierarchy(parent)


class Resolver(ABC):
  @abstractmethod
  def resolve(self, interface: Type[_T], *, name: Optional[str] =None) -> _T: ...


class Provider(ABC, Generic[_T]):
  @abstractproperty
  def typeof(self) -> Type[_T]: ...

  @abstractmethod
  def provide(self, resolver: Resolver) -> _T: ...


def kwargs_for_annotations(resolver: Resolver, annotations: Dict[str, type]) -> Dict[str, Any]:
  kwargs: Dict[str, type] = {}

  for param_name, param_type in annotations.items():
    if param_name == 'return':
      continue
    kwargs[param_name] = resolver.resolve(param_type, name=param_name)

  return kwargs


class InstanceProvider(Generic[_T], Provider[_T]):

  _instance: _T

  def __init__(self, instance: _T):
    self._instance = instance

  @property
  def typeof(self) -> Type[_T]:
    return type(self._instance)

  def provide(self, resolver: Resolver) -> _T:
    return self._instance


class CallableProvider(Generic[_T], Provider[_T]):

  # _callable: Callable[..., _T]
  _annotations: Dict[str, type]

  def __init__(self, kallable: Callable[..., _T]):
    self._callable = kallable
    self._annotations = get_type_hints(self._callable)

  @property
  def typeof(self) -> Type[_T]:
    return cast(Type[_T], self._annotations['return'])

  def provide(self, resolver: Resolver) -> _T:
    return self._callable(**kwargs_for_annotations(resolver, self._annotations))


class AutowiredClassProvider(Generic[_T], Provider[_T]):

  _cls: Type[_T]

  def __init__(self, cls: Type[_T]):
    self._cls = cls

  @property
  def typeof(self) -> Type[_T]:
    return self._cls

  def provide(self, resolver: Resolver) -> _T:
    annotations = get_type_hints(self._cls)
    instance = self._cls()

    for name, annotation in annotations.items():
      setattr(instance, name, resolver.resolve(annotation, name=name))

    return instance


class ConstructorClassProvider(Generic[_T], Provider[_T]):

  _cls: Type[_T]
  # _constructor: Callable[..., _T]

  def __init__(self, cls: Type[_T], constructor: Callable[..., _T]):
    self._cls = cls
    self._constructor = constructor

  @property
  def typeof(self) -> Type[_T]:
    return self._cls

  def provide(self, resolver: Resolver) -> _T:
    annotations = get_type_hints(self._constructor)
    return self._constructor(**kwargs_for_annotations(resolver, annotations))


class ModuleMethodProvider(Generic[_C, _T], Provider[_T]):

  _module_cls: Type[_C]
  # _unbound_method: Callable[..., _T]

  def __init__(self, module_cls: Type[_C], unbound_method: Callable[..., _T]):
    self._module_cls = module_cls
    self._unbound_method = unbound_method

  @property
  def typeof(self) -> Type[_T]:
    return cast(Type[_T], get_type_hints(self._unbound_method)['return'])

  def provide(self, resolver: Resolver) -> _T:
    module = resolver.resolve(self._module_cls)
    method_name = getattr(self._unbound_method, '__name__')
    method = cast(Callable[..., _T], getattr(module, method_name))
    annotations = get_type_hints(method)
    return method(**kwargs_for_annotations(resolver, annotations))


class CacheSentinel: pass


class CachedProvider(Generic[_T], Provider[_T]):

  _UNSET: ClassVar[CacheSentinel] = CacheSentinel()

  _subject: Provider[_T]
  _instance: Union[CacheSentinel, _T]

  def __init__(self, subject: Provider[_T]):
    self._subject = subject
    self._instance = self._UNSET

  @property
  def typeof(self) -> type:
    return self._subject.typeof

  def provide(self, resolver: Resolver) -> _T:
    if isinstance(self._UNSET, CacheSentinel):
      self._instance = instance = self._subject.provide(resolver)
      return instance
    else:
      return self._instance


class DependencyModuleSupport:
  @staticmethod
  def is_module(cls: type) -> bool:
    return inspect.isclass(cls) and cls.__name__.endswith('Module')

  @staticmethod
  def get_methods(cls: type) -> Iterable[Tuple[str, Callable[..., Any]]]:
    for name in dir(cls):
      if name.startswith('_'):
        continue
      member = getattr(cls, name)
      if inspect.isfunction(member):
        yield name, member


class includes:

  _PROP_NAME: ClassVar[str] = '_includes'

  _items: Tuple[type, ...]

  def __init__(self, *items: type):
    self._items = items

  def __call__(self, cls: type) -> type:
    if not DependencyModuleSupport.is_module(cls):
      raise TypeError('not a module')

    self.write(cls, self._items)

    return cls

  @classmethod
  def write(cls, target: type, items: Tuple[type, ...]) -> None:
    setattr(target, cls._PROP_NAME, items)

  @classmethod
  def read(cls, target: type) -> Tuple[type, ...]:
    return cast(Tuple[type, ...], getattr(target, cls._PROP_NAME, ()))


class ResolutionError(Exception): pass


class RegistrationError(Exception): pass


class Container(Resolver):

  _providers: Dict[type, Dict[Optional[str], Provider[Any]]]

  def __init__(self) -> None:
    self._providers = {}

  def register_instance(self, instance: Any, *, name: Optional[str]=None) -> None:
    return self.register(InstanceProvider(instance), name=name)

  def register_class(self, cls: Type[_T], *, name: Optional[str] = None) -> None:
    constructor = get_constructor(cls)
    if is_custom_constructor(constructor):
      return self.register(ConstructorClassProvider(cls, constructor), name=name)
    else:
      return self.register(AutowiredClassProvider(cls), name=name)

  def register_callable(self, kallable: Callable[..., Any], *, name: Optional[str]=None) -> None:
    return self.register(CallableProvider(kallable), name=name)

  def register_module(self, cls: type) -> None:
    self.register_class(cls, name=None)

    for item in includes.read(cls):
      try:
        if DependencyModuleSupport.is_module(item):
          self.register_module(item)
        elif inspect.isclass(item):
          self.register_class(item)
        else:
          raise TypeError('included item cannot be handled')
      except RegistrationError:
        # includes are declarative; dupes are fine for only modules & classes
        pass

    for name, method in DependencyModuleSupport.get_methods(cls):
      self.register(ModuleMethodProvider(cls, method), name=name)

  def register(self, provider: Provider[_T], *, name: Optional[str]=None) -> None:
    cached_provider = CachedProvider(provider)
    for interface in linearize_type_hierarchy(provider.typeof):
      self._add(interface, name, cached_provider)

  def _add(self, interface: type, name: Optional[str], provider: Provider[_T]) -> None:
    named_providers = self._providers.setdefault(interface, {})
    if named_providers.setdefault(name, provider) is not provider:
      raise RegistrationError('provider already registered')

  def resolve(self, interface: Type[_T], *, name: Optional[str]=None) -> _T:
    named_providers = cast(Dict[Optional[str], Provider[_T]], self._providers.setdefault(interface, {}))

    if len(named_providers) == 0:
      raise ResolutionError('missing dependency name={!r} interface={!r}'.format(name, interface))
    elif len(named_providers) == 1:
      # name doesn't matter for unique providers
      for provider in named_providers.values():
        return provider.provide(self)
      raise _Unreachable
    else:
      if name is None:
        raise ResolutionError('ambiguous dependency interface={!r}'.format(interface))
      elif name not in named_providers:
        raise ResolutionError('missing dependency name={!r} interface={!r}'.format(name, interface))
      else:
        return named_providers[name].provide(self)
