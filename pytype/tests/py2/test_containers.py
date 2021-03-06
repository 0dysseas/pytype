"""Test list, dict, etc."""

from pytype import utils
from pytype.tests import test_base


class ContainerTest(test_base.TargetPython27FeatureTest):
  """Tests for containers."""

  # A lot of these tests depend on comprehensions like [x for x in ...] binding
  # x in the outer scope, which does not happen in python3.
  #
  # TODO(pytype): Write python3 versions of these.

  def testIteratePyiListNothing(self):
    with utils.Tempdir() as d:
      d.create_file("a.pyi", """
        from typing import List
        lst1 = ...  # type: List[nothing]
      """)
      ty = self.Infer("""
        import a
        lst2 = [x for x in a.lst1]
        x.some_attribute = 42
        y = x.some_attribute
      """, pythonpath=[d.path])
      self.assertTypesMatchPytd(ty, """
        from typing import Any, List
        a = ...  # type: module
        lst2 = ...  # type: List[nothing]
        x = ...  # type: Any
        y = ...  # type: Any
      """)

  def testIteratePyiListAny(self):
    # Depends on [x for x in ...] binding x in the outer scope
    with utils.Tempdir() as d:
      d.create_file("a.pyi", """
        from typing import Any, List
        lst1 = ...  # type: List[Any]
      """)
      ty = self.Infer("""
        import a
        lst2 = [x for x in a.lst1]
        x.some_attribute = 42
        y = x.some_attribute
      """, pythonpath=[d.path])
      self.assertTypesMatchPytd(ty, """
        from typing import Any
        a = ...  # type: module
        lst2 = ...  # type: list
        x = ...  # type: Any
        y = ...  # type: Any
      """)

  def testLeakingType(self):
    ty = self.Infer("""
      import sys
      a = [str(ty) for ty in (float, int, bool)[:len(sys.argv)]]
    """)
    self.assertTypesMatchPytd(ty, """
      from typing import List, Type
      sys = ...  # type: module
      a = ...  # type: List[str, ...]
      ty = ...  # type: Type[float or int]
    """)

  def testCallEmpty(self):
    ty = self.Infer("""
      empty = []
      y = [x() for x in empty]
    """)
    self.assertTypesMatchPytd(ty, """
      from typing import Any, List
      empty = ...  # type: List[nothing]
      y = ...  # type: List[nothing]
      x = ...  # type: Any
    """)

  def testIteratePyiListUnion(self):
    with utils.Tempdir() as d:
      d.create_file("a.pyi", """
        from typing import List, Set
        lst1 = ...  # type: List[nothing] or Set[int]
      """)
      ty = self.Infer("""
        import a
        lst2 = [x for x in a.lst1]
      """, pythonpath=[d.path])
      self.assertTypesMatchPytd(ty, """
        from typing import List
        a = ...  # type: module
        lst2 = ...  # type: List[int]
        x = ...  # type: int
      """)

  def testIteratePyiList(self):
    with utils.Tempdir() as d:
      d.create_file("a.pyi", """
        lst1 = ...  # type: list
      """)
      ty = self.Infer("""
        import a
        lst2 = [x for x in a.lst1]
        x.some_attribute = 42
        y = x.some_attribute
      """, pythonpath=[d.path])
      self.assertTypesMatchPytd(ty, """
        from typing import Any
        a = ...  # type: module
        lst2 = ...  # type: list
        x = ...  # type: Any
        y = ...  # type: Any
      """)

  def testIteratePyiListInt(self):
    with utils.Tempdir() as d:
      d.create_file("a.pyi", """
        from typing import List
        lst1 = ...  # type: List[int]
      """)
      ty = self.Infer("""
        import a
        lst2 = [x for x in a.lst1]
      """, pythonpath=[d.path])
      self.assertTypesMatchPytd(ty, """
        from typing import List
        a = ...  # type: module
        lst2 = ...  # type: List[int]
        x = ...  # type: int
      """)

  def testIsInstanceEmpty(self):
    ty = self.Infer("""
      empty = []
      y = [isinstance(x, int) for x in empty]
    """)
    self.assertTypesMatchPytd(ty, """
      from typing import Any, List
      empty = ...  # type: List[nothing]
      y = ...  # type: List[bool]
      x = ...  # type: Any
    """)

  def testInnerClassEmpty(self):
    ty = self.Infer("""
      empty = []
      def f(x):
        class X(x):
          pass
        return {X: X()}
      y = [f(x) for x in empty]
    """)
    self.assertTypesMatchPytd(ty, """
      from typing import Any, Dict, List
      empty = ...  # type: List[nothing]
      def f(x) -> Dict[type, Any]
      y = ...  # type: List[Dict[type, Any]]
      x = ...  # type: Any
    """)

  def testIterateEmptyList(self):
    ty = self.Infer("""
      lst1 = []
      lst2 = [x for x in lst1]
      x.some_attribute = 42
      y = x.some_attribute
    """)
    self.assertTypesMatchPytd(ty, """
      from typing import Any, List
      lst1 = ...  # type: List[nothing]
      lst2 = ...  # type: List[nothing]
      x = ...  # type: Any
      y = ...  # type: Any
    """)

  def testBranchEmpty(self):
    ty = self.Infer("""
      empty = []
      def f(x):
        if x:
          return 3
        else:
          return "foo"
      y = [f(x) for x in empty]
    """)
    self.assertTypesMatchPytd(ty, """
      from typing import Any, List
      empty = ...  # type: List[nothing]
      def f(x) -> int or str
      y = ...  # type: List[int or str]
      x = ...  # type: Any
    """)

  def testDictComprehension(self):
    # uses byte_MAP_ADD
    ty = self.Infer("""
      def f():
        return {i: i for i in xrange(3)}
      f()
    """, deep=False, show_library_calls=True)
    self.assertHasOnlySignatures(ty.Lookup("f"),
                                 ((),
                                  self.int_int_dict))

  def testConstructorEmpty(self):
    ty = self.Infer("""
      empty = []
      y = [list(x) for x in empty]
    """)
    self.assertTypesMatchPytd(ty, """
      from typing import Any, List
      empty = ...  # type: List[nothing]
      y = ...  # type: List[List[nothing]]
      x = ...  # type: Any
    """)

  # Uses unicode
  def testEmptyTypeParamAsArg(self):
    ty = self.Infer("""
      def f():
        return u"".join(map(unicode, ()))
    """)
    self.assertTypesMatchPytd(ty, """
      def f() -> unicode
    """)


if __name__ == "__main__":
  test_base.main()
