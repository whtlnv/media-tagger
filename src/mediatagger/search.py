def search(library, query):
    terms = query.lower().split()
    required = [set(term.split("|")) for term in terms if not term.startswith("-")]
    excluded = {term[1:] for term in terms if term.startswith("-")}
    return [
        path
        for path in _items_tagged_any(library, required[0])
        if _matches(_all_effective_tags(library, path), required, excluded)
    ]


def _items_tagged_any(library, alternatives):
    return dict.fromkeys(path for tag in alternatives for path in library.items_tagged(tag))


def _matches(tags, required, excluded):
    return all(group & tags for group in required) and not excluded & tags


def _all_effective_tags(library, path):
    tags = library.effective_tags(path)
    return {*tags.own, *tags.inherited}
