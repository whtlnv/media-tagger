import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
UPDATE_DRIVE = REPO / "drive" / "update-drive.sh"
PACKAGE = REPO / "src" / "mediatagger"


def test_update_drive_puts_every_non_test_module_into_the_drive_app(tmp_path):
    drive = tmp_path / "drive"
    drive.mkdir()

    subprocess.run(["sh", str(UPDATE_DRIVE), str(drive)], check=True)

    modules = {
        p.name
        for p in PACKAGE.glob("*.py")
        if not p.name.startswith("test_") and p.name != "conftest.py"
    }
    on_drive = {p.name for p in (drive / "mediatagger" / "app" / "mediatagger").glob("*.py")}
    assert modules <= on_drive
    assert "__init__.py" in on_drive


def test_update_drive_leaves_test_modules_and_conftest_out_of_the_drive_app(tmp_path):
    drive = tmp_path / "drive"
    drive.mkdir()

    subprocess.run(["sh", str(UPDATE_DRIVE), str(drive)], check=True)

    on_drive = {p.name for p in (drive / "mediatagger" / "app" / "mediatagger").glob("*.py")}
    leaked = {name for name in on_drive if name.startswith("test_") or name == "conftest.py"}
    assert leaked == set()
