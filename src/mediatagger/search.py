from mediatagger.folder import _natural_name_key


def search(library, query):
    terms = query.lower().split()
    if not terms:
        return []
    required = [_alternatives(library, term) for term in terms if not term.startswith("-")]
    excluded = {tag for term in terms if term.startswith("-") for tag in term[1:].split("|")}
    candidates = required[0] if required else library.all_tags()
    effective = library.effective_tags_of(list(_items_tagged_any(library, candidates)))
    found = {path for path, tags in effective.items() if _matches({*tags.own, *tags.inherited}, required, excluded)}
    found_within = {folder: not found.isdisjoint((folder, *folder.parents)) for folder in {path.parent for path in found}}
    top_most = [path for path in found if not found_within[path.parent]]
    return sorted(top_most, key=lambda path: (not path.is_dir(), _natural_name_key(str(path))))


def _alternatives(library, term):
    if term.endswith(":"):
        return {tag for tag in library.all_tags() if tag.startswith(term)}
    return set(term.split("|"))


def _items_tagged_any(library, alternatives):
    return dict.fromkeys(path for tag in alternatives for path in library.items_tagged(tag))


def _matches(tags, required, excluded):
    return all(group & tags for group in required) and not excluded & tags
