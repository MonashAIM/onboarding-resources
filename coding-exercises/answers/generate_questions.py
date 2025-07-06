"""
This script processes a jupyter notebook to clear all answers inside code cells. This works like:
```py
def id(x):
    #!Answer
    return x
```

Which will be replaced with the cells:
```py
def id(x):
    # Your Code Goes Here
    pass
```

This can also be done with a start and end tag like #!Answer Start and #!Answer End, which will clear all lines in between, but keep the indentation. The word `Alternative` can also be used in the tag, like `#!Alternative Answer`, which will also be cleared.

Additionally it will replace all occurrences of `../data/` with `./data/` in any line.
"""

import json
import re
import sys
from typing import Dict, List

_REGEX = r"^(\s*)#\!(Alternative\s*)?Answer\s*"
REGEX = _REGEX + R"$"
REGEX_START = _REGEX + r"Start\s*$"
REGEX_END = _REGEX + r"End\s*$"


fill = lambda x: f"{x}# Your Code Goes Here\n"
fill_pass = lambda x: [fill(x), f"{x}pass\n"]


def replace_data_path(lines: List[str]) -> List[str]:
    """Replace all occurrences of '../data/' with './data/' in any line."""
    return [line.replace("../data/", "./data/") for line in lines]


def clearAnswer(x: List[str]) -> List[str]:
    """Clear all answers in the notebook found in a source."""
    new = []
    i = 0
    while i < len(x):
        # If #!Answer
        if m := re.match(rf"{REGEX}$", x[i]):
            indent = m.group(1)
            new.extend(fill_pass(indent))

            # Remove all lines that start with the same indent
            i += 1
            while i < len(x) and (x[i].startswith(indent) or x[i].strip() == ""):
                i += 1
            continue
        # Scope for #!Answer Start
        elif m := re.match(REGEX_START, x[i]):
            indent = m.group(1)
            new.append(fill(indent))

            i += 1
            found_end = False
            while i < len(x) and not (found_end := re.match(REGEX_END, x[i])):
                i += 1
            if not found_end:
                raise ValueError(f"Expected #!Answer End as closing tag")
        else:
            new.append(x[i])
        i += 1
    return new


def clearAnswers(nb: Dict):
    """Clear all answers in the notebook found within code cells."""
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            data = replace_data_path(cell["source"])
            cell["source"] = clearAnswer(data)
            cell["outputs"] = []
            cell["traceback"] = []
            cell["execution_count"] = None


def test():
    """Test cases foor the replaceReg function."""
    # Case 1: Simple case with a single line
    x = [
        "def mean(x: NDArray) -> float:\n",
        "    #!Answer\n",
        "    # This computes the answer\n",
        "\n",
        "    return sum(x) / len(x)\n",
        "def mode(x: NDArray) -> int\n",
        "    return max(set(x), key=x.count)\n",
    ]
    res = clearAnswer(x)
    ans = [
        "def mean(x: NDArray) -> float:\n",
        "    # Your Code Goes Here\n",
        "    pass\n",
        "def mode(x: NDArray) -> int\n",
        "    return max(set(x), key=x.count)\n",
    ]
    assert res == ans, f"Expected: {ans},\nGot: {res}"

    # Case 2: Multiple lines with #!Answer Start
    y = [
        "def median(x: NDArray) -> float:\n",
        "    y = sorted(x)\n",
        "    #!AnswerStart\n",
        "    n = len(y)\n",
        "    if n % 2 == 0:\n",
        "        return (y[n // 2 - 1] + y[n // 2]) / 2\n",
        "    #!Answer End\n",
        "    return y[n // 2]\n",
    ]
    res = clearAnswer(y)
    ans = [
        "def median(x: NDArray) -> float:\n",
        "    y = sorted(x)\n",
        "    # Your Code Goes Here\n",
        "    return y[n // 2]\n",
    ]
    assert res == ans, f"Expected: {ans},\nGot: {res}"


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("-t", "--test"):
        test()
        sys.exit(0)
    if len(sys.argv) < 3:
        print(
            "Usage: python generate_questions.py [<output_dir> <input_file1> <input_file2> ...] [-t | --test]"
        )
        sys.exit(1)

    outdir = sys.argv[1]
    input_files = sys.argv[2:]

    for input_file in input_files:
        output_file = f"{outdir}/{input_file.split('/')[-1]}"
        print(f"Processing {input_file} -> {output_file}")
        with open(input_file, "r", encoding="utf-8") as f:
            nb = json.load(f)

        clearAnswers(nb)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(nb, f, indent=2, ensure_ascii=False)


main()
