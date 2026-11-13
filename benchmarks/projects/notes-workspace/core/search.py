def tokenize_query(query):
    return query.casefold().split()

def match_notes(notes, query):
    words = tokenize_query(query)
    return [note for note in notes if all(word in (note.title+' '+note.body).casefold() for word in words)]
