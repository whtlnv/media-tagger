from mediatagger.folder import _natural_name_key


def search(library, query):
    terms = query.lower().split()
    if not terms:
        return []
    required = [_alternatives(library, term) for term in terms if not term.startswith("-")]
    excluded = {tag for term in terms if term.startswith("-") for tag in term[1:].split("|")}
    items = library.tagged_items()
    ancestors = {key: _ancestor_keys(key) for key in items}
    found = {key for key, (_, tags) in items.items() if _matches(_effective(items, tags, ancestors[key]), required, excluded)}
    top_most = [key for key in found if found.isdisjoint(ancestors[key])]
    return [library.root / key for key in sorted(top_most, key=lambda key: (items[key][0] != "dir", _natural_name_key(key)))]


def _alternatives(library, term):
    if term.endswith(":"):
        return {tag for tag in library.all_tags() if tag.startswith(term)}
    return set(term.split("|"))


def _ancestor_keys(key):
    ancestors = []
    while "/" in key:
        key = key.rpartition("/")[0]
        ancestors.append(key)
    return ancestors


def _effective(items, tags, ancestor_keys):
    return tags.union(*(items[key][1] for key in ancestor_keys if key in items))


def _matches(tags, required, excluded):
    return all(group & tags for group in required) and not excluded & tags
