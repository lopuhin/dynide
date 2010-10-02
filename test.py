import unittest

from autocomplete import search_b, ident_chars, search_b_balanced, inject_completions


class TestParser(unittest.TestCase):
    def test_search_b(self):
        for (string, index), (skip, stop) in [
            (('adsf.fooo', 5), (ident_chars, None)),
            (('ab(fdff', 3), (None, '()'))]:
            ind = search_b(string, skip, stop)
            print ind, string[ind:], string
            self.assertEqual(ind, index)

    def test_search_b_balanced(self):
        for string, index in [
            ('adsf(foo)', 4),
            ('(adsf(foo = bar(zap), baz = zoo(faz))', 5)]:
            ind = search_b_balanced(string, '(', ')')
            print ind, string[ind:], string
            self.assertEqual(ind, index)

    def test_inject_completions(self):
        for expr, pos, result in [
            ('    foo.ba, baz', 10, '    autocomplete._pr_methods(foo, "ba"), baz'),
            ('    filter(boo = fza, fok = foo(x)).exclude(foo).f().ba', 55,
             '    autocomplete._pr_methods(filter(boo = fza, fok = foo(x)).exclude(foo).f(), "ba")'),
            ('[(a.foo, baz) for baz, foo in x]', 7,
             '[(autocomplete._pr_methods(a, "foo"), baz) for baz, foo in x]'),
            ('    foo(bzr, ba)', 15, '    foo(bzr, autocomplete._pr_vars("ba"))'),]:
            self.assertEqual(result, inject_completions(expr, pos))
        

if __name__ == '__main__':
    unittest.main()
