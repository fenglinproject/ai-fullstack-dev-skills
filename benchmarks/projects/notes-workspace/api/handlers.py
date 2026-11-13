from core.store import Note, NoteStore
from core.search import match_notes

class NotesController:
    def __init__(self, store):
        self.store = store

    def create_note(self, note_id, title, body):
        record = Note(note_id, title, body)
        self.store.save_note(record)
        return record

    def search_notes(self, query):
        return match_notes(self.store.list_active(), query)

    def archive_note(self, note_id):
        note = self.store.find_note(note_id)
        note.archived = True
