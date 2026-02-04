from __future__ import annotations

import re
from contextlib import nullcontext as produces

import pytest
from pytest import raises

from edtext import EdText
from edtext.edtext import Addr, Range


ten_lines = "\n".join(f"line {i + 1}" for i in range(10)) + "\n"


def test_text():
    assert EdText("line1\nline2\n") == "line1\nline2\n"


def test_str():
    assert str(EdText("line1\nline2\n")) == "line1\nline2\n"


def test_repr():
    assert repr(EdText("line1\nline2\n")) == "EdText('line1\\nline2\\n', 2 lines)"
    assert (
        repr(EdText(ten_lines))
        == "EdText('line 1\\nline 2\\nline 3\\nline 4\\nline 5\\nli...', 10 lines)"
    )


def test_eq():
    assert EdText("line1\n") == EdText("line1\n")
    assert EdText("line1\n") != EdText("line2\n")
    assert EdText("line1\n") == "line1\n"
    assert EdText("line1\n") != 3.14159  # NotImplemented makes it false.


@pytest.mark.parametrize(
    "expr, result",
    [
        ("10", produces(Addr(number=10))),
        ("/pattern/", produces(Addr(regex="pattern"))),
        ("  /pattern/", produces(Addr(regex="pattern"))),
        ("/pattern", produces(Addr(regex="pattern"))),
        ("/pattern/+12", produces(Addr(regex="pattern", delta=12))),
        ("/pattern/ + 12", produces(Addr(regex="pattern", delta=12))),
        ("/pattern/+12--", produces(Addr(regex="pattern", delta=12))),
        ("/pattern/+", produces(Addr(regex="pattern", delta=1))),
        ("/pattern/++++", produces(Addr(regex="pattern", delta=4))),
        ("/pattern/+ +   ++ ", produces(Addr(regex="pattern", delta=4))),
        ("/pattern/---", produces(Addr(regex="pattern", delta=-3))),
        (
            "/pattern/-+-",
            raises(ValueError, match=r"Invalid address delta: '/pattern/-\+-'"),
        ),
        ("/pattern/3", produces(Addr(regex="pattern", delta=3))),
        ("123more here", produces(Addr(number=123))),
        ("no good", produces(Addr())),
        ("$", produces(Addr(last=True))),
        ("$-5", produces(Addr(last=True, delta=-5))),
        ("$-5,hello", produces(Addr(last=True, delta=-5))),
        ("+++", produces(Addr(delta=3))),
        ("", produces(Addr())),
    ],
)
def test_parse_address(expr, result):
    with result as expected:
        assert Addr.parse(expr)[0] == expected


@pytest.mark.parametrize(
    "expr, result",
    [
        ("10", produces(Range(start=Addr(number=10)))),
        ("10!", raises(ValueError, match=r"Invalid range: '10!'")),
        ("hello", raises(ValueError, match=r"Invalid range: 'hello'")),
        (
            "10,20",
            produces(Range(start=Addr(number=10), end=Addr(number=20), from0=True)),
        ),
        (
            "10;20",
            produces(Range(start=Addr(number=10), end=Addr(number=20), from0=False)),
        ),
        (
            "/start/++; /end/ - 2",
            produces(
                Range(
                    start=Addr(regex="start", delta=2),
                    end=Addr(regex="end", delta=-2),
                    from0=False,
                )
            ),
        ),
        (
            "/start/+10,$",
            produces(Range(start=Addr(regex="start", delta=10), end=Addr(last=True))),
        ),
        ("12,20extra", raises(ValueError, match=r"Invalid range tail: 'extra'")),
    ],
)
def test_parse_range(expr, result):
    with result as expected:
        assert Range.parse(expr) == expected


@pytest.mark.parametrize(
    "range, result",
    [
        ("5,7", produces("line 5\nline 6\nline 7\n")),
        ("5", produces("line 5\n")),
        (",3", produces("line 1\nline 2\nline 3\n")),
        ("/line/,3", produces("line 1\nline 2\nline 3\n")),
        ("/line/;/line/", produces("line 1\nline 2\n")),
        ("/5/,7", produces("line 5\nline 6\nline 7\n")),
        ("/8$/,$", produces("line 8\nline 9\nline 10\n")),
        ("/5/+,7", produces("line 6\nline 7\n")),
        ("5,/7/-", produces("line 5\nline 6\n")),
        ("5;++", produces("line 5\nline 6\nline 7\n")),
        ("5;.+2", produces("line 5\nline 6\nline 7\n")),
        (".;.+2", produces("line 1\nline 2\nline 3\n")),
        ("5,++", raises(ValueError, match=r"Invalid range: '5,\+\+'")),
        ("5;/line [456]/", produces("line 5\nline 6\n")),
        (" 5 ; /line [456]/ ", produces("line 5\nline 6\n")),
        ("$-2,$", produces("line 8\nline 9\nline 10\n")),
        (
            "/5/--,7",
            produces("line 3\nline 4\nline 5\nline 6\nline 7\n"),
        ),
        ("/hello/", raises(ValueError, match=r"Pattern not found: /hello/")),
        ("5,3", raises(ValueError, match="Invalid range: start 5 > end 3")),
        (
            "/5/,/3/",
            raises(ValueError, match="Invalid range: start 5 > end 3"),
        ),
        ("20,25", raises(ValueError, match=r"Address 20 outside of range 1-10")),
        (
            "/line 2/-----,4",
            raises(ValueError, match=r"Address -3 outside of range 1-10"),
        ),
        ("/line 1/-,4", raises(ValueError, match=r"Address 0 outside of range 1-10")),
    ],
)
def test_range(range, result):
    with result as expected_text:
        assert EdText(ten_lines)[range] == expected_text


@pytest.mark.parametrize(
    "ranges, result",
    [
        (
            ["1,3", "7,9"],
            produces("line 1\nline 2\nline 3\nline 7\nline 8\nline 9\n"),
        ),
        (["5"], produces("line 5\n")),
        (
            ["/2/,/4/", "/8/,$"],
            produces(
                "line 2\nline 3\nline 4\nline 8\nline 9\nline 10\n",
            ),
        ),
        (
            ["/4/+1", "/line/++,/9/"],
            produces("line 5\nline 8\nline 9\n"),
        ),
        (
            [",3", "/line/;+"],
            produces("line 1\nline 2\nline 3\nline 4\nline 5\n"),
        ),
    ],
)
def test_ranges(ranges, result):
    with result as expected_text:
        assert EdText(ten_lines)[*ranges] == expected_text


@pytest.mark.parametrize(
    "pattern, repl, range, result",
    [
        (r"line", r"LINE", "2,3", produces("LINE 2\nLINE 3\n")),
        (r"l[aeiou]ne \d", r"lXne", "2,3", produces("lXne\nlXne\n")),
        (r"l[aeiou]ne (\d)", r"lXne\1\1", "2,3", produces("lXne22\nlXne33\n")),
        (r"hello", r"bye", "2,3", produces("line 2\nline 3\n")),
        (
            r"hi[",
            r"bye",
            "2,3",
            raises(re.PatternError, match=r"unterminated character set"),
        ),
        (
            r"hi",
            r"bye\3",
            "2,3",
            raises(re.PatternError, match=r"invalid group reference"),
        ),
    ],
)
def test_sub(pattern, repl, range, result):
    with result as expected:
        assert EdText(ten_lines).sub(pattern, repl)[range] == expected
