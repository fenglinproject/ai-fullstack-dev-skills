from dataclasses import dataclass

@dataclass
class Note:
    note_id: str
    title: str
    body: str
    archived: bool = False

class NoteStore:
    def __init__(self):
        self.records = {}

    def save_note(self, note):
        self.records[note.note_id] = note

    def find_note(self, note_id):
        return self.records[note_id]

    def list_active(self):
        return [n for n in self.records.values() if not n.archived]
