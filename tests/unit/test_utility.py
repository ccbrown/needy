import unittest
import textwrap

import needy.utility


class UtilityTest(unittest.TestCase):
    def test_dedented_unified_diff(self):
        self.assertEqual(needy.utility.dedented_unified_diff(
            a=textwrap.dedent('''\
                1
                2
                3
                            4
                            5
                            6
                            7
                            8
                            9
                            10''').split('\n'),
            b=textwrap.dedent('''\
                1
                2
                3
                            4
                            5
                            6
                            7''').split('\n'),
            fromfile='before',
            tofile='after',
            lineterm=''
        ), [
                '--- before',
                '+++ after',
                '@@ -5,6 +5,3 @@',
                ' 5',
                ' 6',
                ' 7',
                '-8',
                '-9',
                '-10',
            ]
        )
