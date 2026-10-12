def search(library, query):
    return library.items_tagged(query.lower())
