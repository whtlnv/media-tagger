import ast
from pathlib import Path

PACKAGE = Path(__file__).parent

# The symbols the app's texts use beyond ASCII, each checked (with fc-list) to be in DejaVu Sans, Book and Bold: the
# Pi's default font. Emoji are not; there they draw as empty squares.
DEJAVU_SANS_SYMBOLS = set("°·×–—…←↑→↓▶✓✗⟳")


def string_literals(module):
    """Every string constant in the module's code, docstrings left out: they are never drawn."""
    tree = ast.parse(module.read_text())
    docstrings = {id(node.body[0].value) for node in ast.walk(tree)
                  if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)) and ast.get_docstring(node) is not None}
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings]


def test_every_string_in_the_app_uses_only_characters_the_pis_default_font_has():
    modules = [path for path in sorted(PACKAGE.glob("*.py")) if not path.name.startswith("test_")]
    outside = {(module.name, char) for module in modules for text in string_literals(module) for char in text
               if not char.isascii() and char not in DEJAVU_SANS_SYMBOLS}

    assert outside == set()
