from django.test import SimpleTestCase

from ton_restaurant import calc

class TestingSub(SimpleTestCase):
    def test_calc(self):
        self.assertEqual(calc.add(5, 3), 8)

    def test_sub(self):
        res = calc.sub(100, 99)

        self.assertEqual(res, 1)