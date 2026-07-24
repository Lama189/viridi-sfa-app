from uuid import uuid4

from app.domain.entities.media import MediaFile


def test_media_file_default_values():
    uploader = uuid4()
    mf = MediaFile(
        bucket="avatars",
        original_object_name="photo.jpg",
        content_type="image/jpeg",
        size=1024,
        uploaded_by=uploader,
    )
    assert mf.bucket == "avatars"
    assert mf.original_object_name == "photo.jpg"
    assert mf.content_type == "image/jpeg"
    assert mf.size == 1024
    assert mf.uploaded_by == uploader
    assert isinstance(mf.id, type(uuid4()))
    assert mf.thumbnail_object_name is None
    assert mf.original_filename is None
    assert mf.created_at is not None


def test_media_file_with_optional_fields():
    mf = MediaFile(
        bucket="docs",
        original_object_name="file.pdf",
        content_type="application/pdf",
        size=2048,
        uploaded_by=uuid4(),
        thumbnail_object_name="thumb_file.jpg",
        original_filename="report.pdf",
    )
    assert mf.thumbnail_object_name == "thumb_file.jpg"
    assert mf.original_filename == "report.pdf"
