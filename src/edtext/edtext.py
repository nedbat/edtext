from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Addr:
    """An ed-like line address."""

    number: int | None = None
    regex: str | None = None
    last: bool = False
    delta: int = 0

    @classmethod
    def parse(cls, expr: str) -> tuple[Addr, str]:
        m = re.match(
            r"""(?x)
            ^
            \s*                         # optional whitespace
            (?:
                (?P<number>\d+)         # line number
                |
                (?P<regex>/[^/]+?(/|$)) # regex
                |
                (?P<last>\$)            # last line
                |
                \.                      # current line
            )?
            \s*                         # optional whitespace
            (?:
                (?P<delta>[+-]?\s*\d+)  # optional numeric delta
                |
                (?P<plus>[ +-]+)        # optional plus/minus delta
            )?
            """,
            expr,
        )
        assert m is not None  # the pattern can match nothing, so it always matches
        addr = cls()
        if m["number"] is not None:
            addr.number = int(m["number"])
        elif m["regex"] is not None:
            addr.regex = m["regex"].strip("/")
        elif m["last"] is not None:
            addr.last = True
        if m["delta"] is not None:
            addr.delta = int(m["delta"].replace(" ", ""))
        elif m["plus"] is not None:
            plus = m["plus"].replace(" ", "")
            if len(set(plus)) != 1:
                raise ValueError(f"Invalid address delta: {expr!r}")
            addr.delta = len(plus) * (1 if plus[0] == "+" else -1)
        return addr, expr[m.end() :]

    def is_relative(self) -> bool:
        """Return True if this address is relative (no number, regex, or last)."""
        return self.number is None and self.regex is None and not self.last


@dataclass
class Range:
    """An expression for a range of lines specified by one or two addresses."""

    start: Addr
    end: Addr | None = None
    from0: bool = True

    @classmethod
    def parse(cls, expr: str) -> Range:
        start, rest = Addr.parse(expr)
        r = Range(start=start)
        if not rest:
            return r
        if rest[0] not in ",;":
            raise ValueError(f"Invalid range: {expr!r}")
        r.from0 = rest[0] == ","
        r.end, rest = Addr.parse(rest[1:])
        if rest:
            raise ValueError(f"Invalid range tail: {rest!r}")
        return r


class EdText:
    """A string-like object that supports ed-like line addressing."""

    def __init__(self, text: str, lines: list[str] | None = None) -> None:
        self._text = text
        if lines is not None:
            self._lines = lines
        else:
            self._lines = text.splitlines(keepends=True)

    @classmethod
    def from_lines(cls, lines: list[str]) -> EdText:
        return cls("".join(lines), lines=lines)

    def __str__(self) -> str:
        return self._text

    def __eq__(self, other: object) -> bool:
        if isinstance(other, EdText):
            return self._text == other._text
        if isinstance(other, str):
            return self._text == other
        return NotImplemented

    def _resolve_addr(self, addr: Addr, start: int) -> int:
        """Return the one-based line index for the given address.
        `start` is the one-based index of the current line, except 0 means
        start from the beginning.
        """
        if addr.number is not None:
            res = addr.number + addr.delta
        elif addr.regex is not None:
            for num, line in enumerate(self._lines[start:], start=start + 1):
                if re.search(addr.regex, line):
                    res = num + addr.delta
                    break
            else:
                raise ValueError(f"Pattern not found: /{addr.regex}/")
        elif addr.last:
            res = len(self._lines) + addr.delta
        else:
            if start == 0:
                start = 1
            res = start + addr.delta
        return res

    def _line_numbers(self, *range_exprs: str) -> list[int]:
        """Get the list of line numbers for the given range expressions."""
        numbers = []
        start = 0
        for range_expr in range_exprs:
            r = Range.parse(range_expr)
            start_idx = self._resolve_addr(r.start, start=start)
            if r.end is None:
                end_idx = start_idx
            else:
                start = 1 if r.from0 else start_idx
                if r.end.is_relative() and r.from0:
                    raise ValueError(f"Invalid range: {range_expr!r}")
                end_idx = self._resolve_addr(r.end, start=start)
            if start_idx > end_idx:
                raise ValueError(f"Invalid range: start {start_idx} > end {end_idx}")
            numbers.extend(range(start_idx - 1, end_idx))
            start = end_idx
        return numbers

    def ranges(self, *range_exprs: str) -> EdText:
        """Make a new EdText with the lines selected by the given ranges."""
        return EdText.from_lines(
            [self._lines[i] for i in self._line_numbers(*range_exprs)]
        )

    range = ranges

    def __getitem__(self, key: str | tuple[str, ...]) -> EdText:
        if isinstance(key, str):
            key = (key,)
        return self.ranges(*key)
