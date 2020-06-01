from abc import ABC
from abc import abstractmethod
from abc import abstractproperty
import inspect
import typing
from typing import Any
from typing import Callable
from typing import ClassVar
from typing import Dict
from typing import Generic
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import Union
from typing import cast


__all__ = [
  'Container',
  'includes',
]


_C = TypeVar('_C')
_T = TypeVar('_T')


def get_constructor(cls: Type[_T]) -> Callable[..., _T]:
  return cast(Callable[..., _T], getattr(cls, '__init__'))


def is_custom_constructor(constructor: Callable[..., _T]) -> bool:
  return constructor is not object.__init__


def generic_arguments(t: type) -> Optional[Tuple[type, ...]]:
  return cast(Optional[Tuple[type, ...]], getattr(t, '__args__', None))


def generic_parameters(t: type) -> Optional[Tuple[type, ...]]:
  return cast(Optional[Tuple[type, ...]], getattr(t, '__parameters__', None))


def generic_bases(t: type) -> Tuple[type, ...]:
  return cast(Tuple[type, ...], getattr(t, '__orig_bases__', ()))


def generic_origin(t: type) -> type:
  return cast(type, getattr(t, '__origin__'))


def has_unbound_type_args(t: type) -> bool:
  args = generic_parameters(t)
  if args is None:
    return False
  elif len(args) == 0:
    return False
  else:
    return True


def is_generic_type(t: type) -> bool:
  return generic_arguments(t) is not None


def is_generic_alias(t: type) -> bool:
  # ideally: isinstance(t, typing._GenericAlias)
  return is_generic_type(t) and not has_unbound_type_args(t)


def generic_tree(t: type) -> Iterable[type]:
  if is_generic_alias(t):
    yield t
  for child in generic_bases(t):
    yield from generic_tree(child)


def linearize_type_hierarchy(t: type) -> Iterable[type]:
  for child in generic_tree(t):
    yield child
  if is_generic_alias(t):
    # Generic aliases (saturated generic types) do not have an mro
    # Instead, the mro is found in the 'origin type' (the generic type itself)
    t = generic_origin(t)
  for child in inspect.getmro(t):
    if child in (object, Generic, ABC):
      # These bases are not useful interfaces
      continue
    elif has_unbound_type_args(child):
      # Do not expose generic types, because they are not complete types
      continue
    else:
      yield child


class Resolver(ABC):
  @abstractmethod
  def resolve(self, interface: Type[_T], *, name: Optional[str] =None) -> _T: ...


class Provider(ABC, Generic[_T]):
  @abstractproperty
  def typeof(self) -> Type[_T]: ...

  @abstractmethod
  def provide(self, resolver: Resolver) -> _T: ...

  @abstractmethod
  def __hash__(self) -> int: ...

  @abstractmethod
  def __eq__(self, other: object) -> bool: ...


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

  def __hash__(self) -> int:
    return hash(self._instance)

  def __eq__(self, other: object) -> bool:
    return isinstance(other, InstanceProvider) and self._instance == other._instance


class CallableProvider(Generic[_T], Provider[_T]):

  # _callable: Callable[..., _T]
  _annotations: Dict[str, type]

  def __init__(self, kallable: Callable[..., _T]):
    self._callable = kallable
    self._annotations = typing.get_type_hints(self._callable)

  @property
  def typeof(self) -> Type[_T]:
    return cast(Type[_T], self._annotations['return'])

  def provide(self, resolver: Resolver) -> _T:
    return self._callable(**kwargs_for_annotations(resolver, self._annotations))

  def __hash__(self) -> int:
    return hash(self._callable)

  def __eq__(self, other: object) -> bool:
    return isinstance(other, CallableProvider) and self._callable == other._callable


class AutowiredClassProvider(Generic[_T], Provider[_T]):

  _cls: Type[_T]

  def __init__(self, cls: Type[_T]):
    self._cls = cls

  @property
  def typeof(self) -> Type[_T]:
    return self._cls

  def provide(self, resolver: Resolver) -> _T:
    annotations = typing.get_type_hints(self._cls)
    instance = self._cls()

    for name, annotation in annotations.items():
      setattr(instance, name, resolver.resolve(annotation, name=name))

    return instance

  def __hash__(self) -> int:
    return hash(self._cls)

  def __eq__(self, other: object) -> bool:
    return isinstance(other, AutowiredClassProvider) and self._cls == other._cls


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
    annotations = typing.get_type_hints(self._constructor)
    return cast(Callable[..., _T], self._cls)(**kwargs_for_annotations(resolver, annotations))

  def __hash__(self) -> int:
    return hash(self._cls)

  def __eq__(self, other: object) -> bool:
    return isinstance(other, ConstructorClassProvider) and self._cls == other._cls


class ModuleMethodProvider(Generic[_C, _T], Provider[_T]):

  _module_cls: Type[_C]
  # _unbound_method: Callable[..., _T]

  def __init__(self, module_cls: Type[_C], unbound_method: Callable[..., _T]):
    self._module_cls = module_cls
    self._unbound_method = unbound_method

  @property
  def typeof(self) -> Type[_T]:
    return cast(Type[_T], typing.get_type_hints(self._unbound_method)['return'])

  def provide(self, resolver: Resolver) -> _T:
    module = resolver.resolve(self._module_cls)
    method_name = getattr(self._unbound_method, '__name__')
    method = cast(Callable[..., _T], getattr(module, method_name))
    annotations = typing.get_type_hints(method)
    return method(**kwargs_for_annotations(resolver, annotations))

  def __hash__(self) -> int:
    return hash((self._module_cls, self._unbound_method))

  def __eq__(self, other: object) -> bool:
    return isinstance(other, ModuleMethodProvider) \
      and (self._module_cls, self._unbound_method) == (other._module_cls, other._unbound_method)


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
    if isinstance(self._instance, CacheSentinel):
      self._instance = instance = self._subject.provide(resolver)
      return instance
    else:
      return self._instance

  def __hash__(self) -> int:
    return hash(self._subject)

  def __eq__(self, other: object) -> bool:
    return isinstance(other, CachedProvider) and self._subject == other._subject


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


class MissingDependencyError(ResolutionError):
  def __init__(self, interface: type, name: Optional[str]):
    super().__init__('missing dependency name={!r} interface={!r}'.format(name, interface))


class AmbiguousDependencyError(ResolutionError):
  def __init__(self, interface: type, name: Optional[str], candidates: Set[Provider[Any]]):
    super().__init__('ambiguous dependency name={!r} interface={!r} candidates={!r}'.format(name, interface, candidates))


class Container(Resolver):

  _providers: Dict[type, Dict[Optional[str], Set[Provider[Any]]]]

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
      if DependencyModuleSupport.is_module(item):
        self.register_module(item)
      elif inspect.isclass(item):
        self.register_class(item)
      else:
        raise TypeError('Module {} includes an item that cannot be handled'.format(cls))

    for name, method in DependencyModuleSupport.get_methods(cls):
      self.register(ModuleMethodProvider(cls, method), name=name)

  def register(self, provider: Provider[_T], *, name: Optional[str]=None) -> None:
    cached_provider = CachedProvider(provider)
    hierarchy = list(linearize_type_hierarchy(provider.typeof))
    for interface in hierarchy:
      self._add(interface, name, cached_provider)

  def _add(self, interface: type, name: Optional[str], provider: Provider[_T]) -> None:
    for_interface: Dict[Optional[str], Set[Provider[_T]]] = self._interface_providers(interface)
    for_name = for_interface.setdefault(name, set())
    for_name.add(provider)

  def resolve(self, interface: Type[_T], *, name: Optional[str] = None) -> _T:
    candidates: Set[Provider[_T]] = set(self._get_candidates(interface, name))

    if len(candidates) == 0:
      raise MissingDependencyError(interface, name)
    elif len(candidates) == 1:
      for provider in candidates:
        return provider.provide(self)
      raise Exception('unreachable')
    else:
      raise AmbiguousDependencyError(interface, name, candidates)

  def _get_candidates(self, interface: Type[_T], name: Optional[str]) -> Iterable[Provider[_T]]:
    for_interface = self._interface_providers(interface)

    for available_name, for_name in for_interface.items():
      for provider in for_name:
        if name is None or available_name is None or name == available_name:
          yield provider

  def _interface_providers(self, interface: Type[_T]) -> Dict[Optional[str], Set[Provider[_T]]]:
    return cast(Dict[Optional[str], Set[Provider[_T]]], self._providers.setdefault(interface, {}))
