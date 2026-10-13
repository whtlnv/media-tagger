def search(library, query):
    terms = query.lower().split()
    if not terms:
        return []
    required = [_alternatives(library, term) for term in terms if not term.startswith("-")]
    excluded = {tag for term in terms if term.startswith("-") for tag in term[1:].split("|")}
    candidates = required[0] if required else library.all_tags()
    return [
        path
        for path in _items_tagged_any(library, candidates)
        if _matches(_all_effective_tags(library, path), required, excluded)
    ]


def _alternatives(library, term):
    if term.endswith(":"):
        return {tag for tag in library.all_tags() if tag.startswith(term)}
    return set(term.split("|"))


def _items_tagged_any(library, alternatives):
    return dict.fromkeys(path for tag in alternatives for path in library.items_tagged(tag))


def _matches(tags, required, excluded):
    return all(group & tags for group in required) and not excluded & tags


def _all_effective_tags(library, path):
    tags = library.effective_tags(path)
    return {*tags.own, *tags.inherited}
