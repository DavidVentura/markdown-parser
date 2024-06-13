import pytest
from markdown_parser.parser import make_parser


@pytest.fixture(scope="session")
def parser():
    p = make_parser()
    yield p

