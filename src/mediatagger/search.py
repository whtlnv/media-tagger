def search(library, query):
    terms = query.lower().split()
    required = [term for term in terms if not term.startswith("-")]
    excluded = {term[1:] for term in terms if term.startswith("-")}
    return [
        path
        for path in library.items_tagged(required[0])
        if set(required) <= _all_effective_tags(library, path)
        and not excluded & _all_effective_tags(library, path)
    ]


def _all_effective_tags(library, path):
    tags = library.effective_tags(path)
    return {*tags.own, *tags.inherited}
