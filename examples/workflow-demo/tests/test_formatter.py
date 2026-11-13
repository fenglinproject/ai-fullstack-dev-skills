import unittest
from src.formatter import greet

class FormatterTests(unittest.TestCase):
    def test_greeting_punctuation(self):
        self.assertEqual(greet('Ada'), 'Hello Ada!')
