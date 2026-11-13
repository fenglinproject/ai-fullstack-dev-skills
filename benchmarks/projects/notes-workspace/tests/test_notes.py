import unittest
from core.store import NoteStore
from api.handlers import NotesController

class NoteTests(unittest.TestCase):
    def test_search(self):
        controller = NotesController(NoteStore())
        controller.create_note('n1', 'Ideas', 'Gamma release')
        self.assertEqual(len(controller.search_notes('gamma')), 1)
        controller.archive_note('n1')
        self.assertFalse(controller.search_notes('gamma'))

if __name__ == '__main__':
    unittest.main()
