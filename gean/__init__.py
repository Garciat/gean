import inspect
from typing import Any, Dict, Iterable, List, get_type_hints


def linearize_type_hierarchy(root: type) -> Iterable[type]:
  if root is object:
    return
  yield root
  for node in inspect.getclasstree([root]):
    if isinstance(node, tuple):
      parent, _ = node
      yield from linearize_type_hierarchy(parent)


class Resolver:
  def resolve(self, interface, *, name=None):
    raise NotImplementedError


class Provider:
  @property
  def typeof(self):
    raise NotImplementedError

  def provide(self, resolver):
    raise NotImplementedError


class InstanceProvider(Provider):
  def __init__(self, instance):
    self._instance = instance

  @property
  def typeof(self):
    return type(self._instance)

  def provide(self, resolver):
    return self._instance


def kwargs_for_annotations(resolver: Resolver, annotations: Dict[str, type]):
  kwargs = {}

  for param_name, param_type in annotations.items():
    if param_name == 'return':
      continue
    kwargs[param_name] = resolver.resolve(param_type, name=param_name)

  return kwargs


class CallableProvider(Provider):
  def __init__(self, kallable):
    self._callable = kallable
    self._annotations = get_type_hints(self._callable)

  @property
  def typeof(self):
    return self._annotations['return']

  def provide(self, resolver):
    return self._callable(**kwargs_for_annotations(resolver, self._annotations))


class ClassProvider(Provider):
  def __init__(self, cls):
    self._cls = cls

  @property
  def typeof(self):
    return self._cls

  def provide(self, resolver):
    if self._cls.__init__ is object.__init__:
      return self._provide_as_autowired(resolver)
    else:
      return self._provide_as_callable(resolver)

  def _provide_as_autowired(self, resolver):
    annotations = get_type_hints(self._cls)
    instance = self._cls()

    for name, annotation in annotations.items():
      setattr(instance, name, resolver.resolve(annotation, name=name))

    return instance

  def _provide_as_callable(self, resolver):
    annotations = get_type_hints(self._cls.__init__)
    return self._cls(**kwargs_for_annotations(resolver, annotations))


class ModuleMethodProvider(Provider):
  def __init__(self, module_cls, unbound_method):
    self._module_cls = module_cls
    self._unbound_method = unbound_method

  @property
  def typeof(self):
    return get_type_hints(self._unbound_method)['return']

  def provide(self, resolver):
    module = resolver.resolve(self._module_cls)
    method = getattr(module, self._unbound_method.__name__)
    annotations = get_type_hints(method)
    return method(**kwargs_for_annotations(resolver, annotations))


class CachedProvider(Provider):
  _UNSET = object()

  def __init__(self, subject: Provider):
    self._subject = subject
    self._instance = self._UNSET

  @property
  def typeof(self):
    return self._subject.typeof

  def provide(self, resolver):
    if self._instance is self._UNSET:
      self._instance = self._subject.provide(resolver)

    return self._instance


class DependencyModuleSupport:
  @staticmethod
  def is_module(cls):
    return inspect.isclass(cls) and cls.__name__.endswith('Module')

  @staticmethod
  def get_methods(cls):
    for name in dir(cls):
      if name.startswith('_'):
        continue
      member = getattr(cls, name)
      if inspect.isfunction(member):
        yield name, member


class includes:
  _PROP_NAME = '_includes'

  def __init__(self, *items):
    self._items = items

  def __call__(self, cls):
    if not DependencyModuleSupport.is_module(cls):
      raise TypeError('not a module')

    self.write(cls, self._items)

    return cls

  @classmethod
  def write(cls, target, items):
    setattr(target, cls._PROP_NAME, items)

  @classmethod
  def read(cls, target):
    return getattr(target, cls._PROP_NAME, [])


class ResolutionError(Exception): pass


class RegistrationError(Exception): pass


class Container:
  _providers: Dict[type, Dict[str, Provider]]

  def __init__(self):
    self._providers = {}

  def register_instance(self, instance, *, name=None):
    return self.register(InstanceProvider(instance), name=name)

  def register_class(self, cls, *, name=None):
    return self.register(ClassProvider(cls), name=name)

  def register_callable(self, kallable, *, name=None):
    return self.register(CallableProvider(kallable), name=name)

  def register_module(self, cls):
    self.register(ClassProvider(cls), name=None)

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

  def register(self, provider: Provider, *, name=None):
    cached_provider = CachedProvider(provider)
    for interface in linearize_type_hierarchy(provider.typeof):
      self._add(interface, name, cached_provider)

  def _add(self, interface, name, provider):
    named_providers = self._providers.setdefault(interface, {})
    if named_providers.setdefault(name, provider) is not provider:
      raise RegistrationError('provider already registered')

  def resolve(self, interface, *, name=None):
    named_providers = self._providers.setdefault(interface, {})

    if len(named_providers) == 0:
      raise ResolutionError('missing dependency name={!r} interface={!r}'.format(name, interface))
    elif len(named_providers) == 1:
      # name doesn't matter for unique providers
      for provider in named_providers.values():
        return provider.provide(self)
    else:
      if name is None:
        raise ResolutionError('ambiguous dependency interface={!r}'.format(interface))
      elif name not in named_providers:
        raise ResolutionError('missing dependency name={!r} interface={!r}'.format(name, interface))
      else:
        return named_providers[name].provide(self)
