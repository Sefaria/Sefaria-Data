import pytest


@pytest.fixture()
def create_footnote():
    i = 2
    comment_body = "ABCDE"
    return f"<sup class=\"footnote-marker\">{i + 1}</sup><i class=\"footnote\">{comment_body}</i>"


def test_create_footnote(create_footnote):
    assert create_footnote == f"<sup class=\"footnote-marker\">3</sup><i class=\"footnote\">ABCDE</i>"
