def search(library, query):
    required = [term for term in query.lower().split() if not term.startswith("-")]
    return [
        path
        for path in library.items_tagged(required[0])
        if set(required) <= _all_effective_tags(library, path)
    ]


def _all_effective_tags(library, path):
    tags = library.effective_tags(path)
    return {*tags.own, *tags.inherited}
