import itertools

import pytest

from repomanager.utils import yaml_dump

EXPECTED_YAML_LIST_SIMPLE = """\
- 1
- 2
- 3
"""

TEST_DATA_LIST_SIMPLE = (
    [1, 2, 3],
    EXPECTED_YAML_LIST_SIMPLE,
)

EXPECTED_YAML_LIST_NESTED = """\
- - 3
  - 2
  - 1
- - a
  - c
  - b
"""

TEST_DATA_LIST_NESTED = (
    [
        [3, 2, 1],
        ["a", "c", "b"],
    ],
    EXPECTED_YAML_LIST_NESTED,
)

EXPECTED_YAML_DICT_NESTED = """\
b:
  - 3
  - 1
  - 2
a: 1
c:
  e: f
  d:
    - z
    - x
    - y
"""

TEST_DATA_DICT_NESTED = (
    {
        "b": [3, 1, 2],
        "a": 1,
        "c": {
            "e": "f",
            "d": ["z", "x", "y"],
        },
    },
    EXPECTED_YAML_DICT_NESTED,
)

TEST_DATA = (
    TEST_DATA_LIST_SIMPLE,
    TEST_DATA_LIST_NESTED,
    TEST_DATA_DICT_NESTED,
)


@pytest.mark.parametrize("test_input, expected_yaml", TEST_DATA, ids=itertools.count())
def test_yaml_dump(tmp_path, test_input, expected_yaml):

    out_file_path = tmp_path / "test.yml"

    with out_file_path.open("w") as file:
        yaml_dump(test_input, file)

    assert out_file_path.read_text() == expected_yaml
