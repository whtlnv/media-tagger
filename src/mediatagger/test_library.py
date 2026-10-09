from mediatagger.library import Library


def test_a_newly_created_library_reports_the_same_drive_id_after_it_is_closed_and_opened_again(tmp_path):
    created = Library.create(tmp_path)
    drive_id = created.drive_id
    created.close()

    reopened = Library.open(tmp_path)

    assert drive_id
    assert reopened.drive_id == drive_id


def test_a_newly_created_library_records_its_schema_version_alongside_its_drive_id(tmp_path):
    created = Library.create(tmp_path)
    schema_version = created.schema_version
    created.close()

    reopened = Library.open(tmp_path)

    assert schema_version
    assert reopened.schema_version == schema_version
    assert reopened.drive_id == created.drive_id
