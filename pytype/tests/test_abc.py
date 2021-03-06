"""Tests for @abc.abstractmethod in abc_overlay.py."""

from pytype import utils
from pytype.tests import test_base


class AbstractMethodTests(test_base.TargetIndependentTest):
  """Tests for @abc.abstractmethod."""

  def test_instantiate_pyi_abstract_class(self):
    with utils.Tempdir() as d:
      d.create_file("foo.pyi", """
        import abc
        class Example(metaclass=abc.ABCMeta):
          @abc.abstractmethod
          def foo(self) -> None: ...
      """)
      _, errors = self.InferWithErrors("""\
        import foo
        foo.Example()
      """, pythonpath=[d.path])
      self.assertErrorLogIs(errors, [(2, "not-instantiable",
                                      r"foo\.Example.*foo")])

  def test_stray_abstractmethod(self):
    _, errors = self.InferWithErrors("""\
      import abc
      class Example(object):
        @abc.abstractmethod
        def foo(self):
          pass
    """)
    self.assertErrorLogIs(errors, [(2, "ignored-abstractmethod",
                                    r"foo.*Example")])

  def test_multiple_inheritance_implementation_pyi(self):
    with utils.Tempdir() as d:
      d.create_file("foo.pyi", """
        import abc
        class Interface(metaclass=abc.ABCMeta):
          @abc.abstractmethod
          def foo(self): ...
        class X(Interface): ...
        class Implementation(Interface):
          def foo(self) -> int: ...
        class Foo(X, Implementation): ...
      """)
      self.Check("""
        import foo
        foo.Foo().foo()
      """, pythonpath=[d.path])

  def test_multiple_inheritance_error_pyi(self):
    with utils.Tempdir() as d:
      d.create_file("foo.pyi", """
        import abc
        class X(object): ...
        class Interface(metaclass=abc.ABCMeta):
          @abc.abstractmethod
          def foo(self): ...
        class Foo(X, Interface): ...
      """)
      _, errors = self.InferWithErrors("""\
        import foo
        foo.Foo().foo()
      """, pythonpath=[d.path])
      self.assertErrorLogIs(errors, [(2, "not-instantiable", r"foo\.Foo.*foo")])

  def test_abc_metaclass_from_decorator(self):
    with utils.Tempdir() as d:
      d.create_file("six.pyi", """
        from typing import TypeVar, Callable
        T = TypeVar('T')
        def add_metaclass(metaclass: type) -> Callable[[T], T]: ...
      """)
      self.Check("""
        import abc
        import six
        @six.add_metaclass(abc.ABCMeta)
        class Foo(object):
          @abc.abstractmethod
          def foo(self):
            pass
      """, pythonpath=[d.path])

  def test_misplaced_abstractproperty(self):
    _, errors = self.InferWithErrors("""\
      import abc
      @abc.abstractproperty
      class Example(object):
        pass
      Example()
    """)
    self.assertErrorLogIs(errors,
                          [(5, "not-callable", r"'abstractproperty' object")])


if __name__ == "__main__":
  test_base.main()
