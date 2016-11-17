import unittest

from needy.memoize import MemoizeMethod


class MemoizeMethodTest(unittest.TestCase):
    class Foo:
        def __init__(self, i=0):
            self.i = i
            self.call_count = 0

        @MemoizeMethod
        def foo(self, j, k=2):
            self.call_count += 1
            return self.i + j + k

        @MemoizeMethod
        def foo_unhashables(self, obj):
            self.call_count += 1
            return obj

    def test_class_method_memoize(self):
        f = MemoizeMethodTest.Foo(5)

        self.assertEqual(f.foo(1, k=5), 11)
        self.assertEqual(f.call_count, 1)

        self.assertEqual(f.foo(10), 17)
        self.assertEqual(f.call_count, 2)

        for i in range(10):
            self.assertEqual(f.foo(1, k=5), 11)
            self.assertEqual(f.foo(10), 17)

        self.assertEqual(f.call_count, 2)

    def test_class_method_memoize_unhashable_arguments(self):
        f = MemoizeMethodTest.Foo(5)

        self.assertEqual(f.foo_unhashables(['a', 'b']), ['a', 'b'])
        self.assertEqual(f.call_count, 1)

        self.assertEqual(f.foo_unhashables({'a': 'b'}), {'a': 'b'})
        self.assertEqual(f.call_count, 2)

        for i in range(10):
            self.assertEqual(f.foo_unhashables(['a', 'b']), ['a', 'b'])
            self.assertEqual(f.foo_unhashables({'a': 'b'}), {'a': 'b'})

        self.assertEqual(f.call_count, 2)
