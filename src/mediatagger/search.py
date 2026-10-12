def search(library, query):
    terms = query.lower().split()
    return [
        path
        for path in library.items_tagged(terms[0])
        if set(terms) <= _all_effective_tags(library, path)
    ]


def _all_effective_tags(library, path):
    tags = library.effective_tags(path)
    return {*tags.own, *tags.inherited}
