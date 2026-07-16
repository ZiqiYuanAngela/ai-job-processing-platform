from app.services.workflow_service import split_text


def test_split_text_creates_multiple_chunks():
    text = "a" * 9000

    chunks = split_text(
        text=text,
        chunk_size=4000,
    )

    assert len(chunks) == 3
    assert len(chunks[0]) == 4000
    assert len(chunks[1]) == 4000
    assert len(chunks[2]) == 1000