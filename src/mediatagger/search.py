def search(library, query):
    terms = query.lower().split()
    return [
        path
        for path in library.items_tagged(terms[0])
        if set(terms) <= {*library.effective_tags(path).own, *library.effective_tags(path).inherited}
    ]
