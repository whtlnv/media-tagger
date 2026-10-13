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
    return sorted(_top_most(found), key=_folders_first_natural_order)


def _alternatives(library, term):
    if term.endswith(":"):
        return {tag for tag in library.all_tags() if tag.startswith(term)}
    return set(term.split("|"))


def _items_tagged_any(library, alternatives):
    return dict.fromkeys(path for tag in alternatives for path in library.items_tagged(tag))


def _top_most(found):
    inside_found_folder = {folder: not found.isdisjoint((folder, *folder.parents)) for folder in {path.parent for path in found}}
    return [path for path in found if not inside_found_folder[path.parent]]


def _folders_first_natural_order(path):
    return (not path.is_dir(), _natural_name_key(str(path)))


def _matches(tags, required, excluded):
    return all(group & tags for group in required) and not excluded & tags
