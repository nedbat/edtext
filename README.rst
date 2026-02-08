EdText — ed-like text selection
===============================

This library provides an ``EdText`` class for selecting and manipulating lines
of text from a string, using addressing inspired by the classic `ed text editor`__.

__ https://www.gnu.org/software/ed/manual/ed_manual.html#Line-addressing

..  [[[cog
..      from pathlib import Path
..      from textwrap import indent
..      from edtext import EdText
..      getty = EdText(Path("tests/gettysburg.txt").read_text())
..
..      def show_code(code):
..          print("\n.. code-block:: python3\n")
..          print(f"    >>> print({code})")
..          print(indent(str(eval(code)), "    "))
..  ]]]
..  [[[end]]] (sum: 1B2M2Y8Asg)

Suppose we have this file:

..  [[[cog
..      print("\n.. code-block::\n")
..      print(indent(str(getty), "    "))
..  ]]]

.. code-block::

    # gettysburg.txt

    Four score and seven years ago our fathers brought forth
    on this continent, a new nation, conceived in Liberty, and
    dedicated to the proposition that all men are created equal.

    Now we are engaged in a great civil war, testing whether that
    nation, or any nation so conceived and so dedicated, can long
    endure. We are met on a great battle-field of that war. We have
    come to dedicate a portion of that field, as a final resting
    place for those who here gave their lives that that nation
    might live. It is altogether fitting and proper that we should
    do this.

    -- Abraham Lincoln, Gettysburg PA, 1863

.. [[[end]]] (sum: JViqmdHeWm)

Make an ``EdText`` object from the text of the file::

    >>> getty = EdText(Path("gettysburg.txt").read_text())

The lines of text are stored for selection and manipulation. The full text is
recreated when the object is turned into a string:

..  [[[cog
..      print("\n.. code-block:: python3\n")
..      print("    >>> str(getty)[:60]")
..      print(f"    {str(getty)[:60]!r}")
..  ]]]

.. code-block:: python3

    >>> str(getty)[:60]
    '# gettysburg.txt\n\nFour score and seven years ago our fathers'
.. [[[end]]] (sum: e1Z4jEQYgP)


Line selection
--------------

Instead of using string slicing, ``EdText`` objects provide line selection.
It's available via three aliases: ``range()``, ``ranges()``, or list-like
slicing with square brackets.  All do the same operation: select lines based on
the addresses provided, and produce a new ``EdText`` object.

Here we select lines starting from the first line that matches "Four" to the
line before the next blank line:

.. [[[cog show_code('''getty.range("/Four/; /^$/-")''') ]]]

.. code-block:: python3

    >>> print(getty.range("/Four/; /^$/-"))
    Four score and seven years ago our fathers brought forth
    on this continent, a new nation, conceived in Liberty, and
    dedicated to the proposition that all men are created equal.

.. [[[end]]] (sum: lYph3U36kb)

The ``range`` argument is a string with the ed range to select. In this
example, ``/Four/`` means the first line containing the regex "Four", the
semicolon means to continue from that point, ``/^$/`` matches the next blank
line, and the trailing ``-`` backs up one line to select the line before the
blank line.

You can use a number of address ranges to select a more than one range at once:

.. [[[[cog show_code('''getty.range("/Four/; +2", "$")''') ]]]

.. code-block:: python3

    >>> print(getty.range("/Four/; +2", "$"))
    Four score and seven years ago our fathers brought forth
    on this continent, a new nation, conceived in Liberty, and
    dedicated to the proposition that all men are created equal.
    -- Abraham Lincoln, Gettysburg PA, 1863

.. [[[end]]] (sum: twF+T8gco0)

The ``/Four/;+2`` means the line matching "Four" then two more lines. ``$``
means the last line.

With multiple address ranges, each range starts from where the previous range
ended.

Although we are using strings to determine line numbers, this feels like
slicing, so square bracket slicing does the same thing as ``range()``:

.. [[[[cog show_code('''getty["/Now/;/\./", "$-;$"]''') ]]]

.. code-block:: python3

    >>> print(getty["/Now/;/\./", "$-;$"])
    Now we are engaged in a great civil war, testing whether that
    nation, or any nation so conceived and so dedicated, can long
    endure. We are met on a great battle-field of that war. We have

    -- Abraham Lincoln, Gettysburg PA, 1863

.. [[[end]]] (sum: GK+AYuhBd0)

Note that you must use strings, not integers, for slicing, and that like ed,
lines are numbered starting from 1. To get lines 10 through 12, ``[10, 12]``
won't work, you need to use ``["10, 12"]``:

.. [[[[cog show_code('''getty["10, 12"]''') ]]]

.. code-block:: python3

    >>> print(getty["10, 12"])
    come to dedicate a portion of that field, as a final resting
    place for those who here gave their lives that that nation
    might live. It is altogether fitting and proper that we should

.. [[[end]]] (sum: b1fyetynxl)

Since we can select a number of ranges at once, ``ranges()`` is an alias for
``range()``.


sub(range, pattern, repl)
-------------------------

Another operation is ``EdText.sub()``, which makes regex replacements on
selected lines:

.. [[[cog show_code('''getty.sub("g/and/", r"e", "E")["1,5"]''') ]]]

.. code-block:: python3

    >>> print(getty.sub("g/and/", r"e", "E")["1,5"])
    # gettysburg.txt

    Four scorE and sEvEn yEars ago our fathErs brought forth
    on this continEnt, a nEw nation, concEivEd in LibErty, and
    dedicated to the proposition that all men are created equal.

.. [[[end]]] (sum: IZEyyvR97V)

The first argument is a range of line addresses, the line in which to apply the
substitution. Note that ``/pat/`` finds the next matching line, not all
matching lines. Use ``g/pat/`` to select all lines matching the pattern.

The result of ``sub()`` is another ``EdText`` object. You can do further
manipulations or selections.

.. [[[cog show_code('''getty["g/and/"]''') ]]]

.. code-block:: python3

    >>> print(getty["g/and/"])
    Four score and seven years ago our fathers brought forth
    on this continent, a new nation, conceived in Liberty, and
    nation, or any nation so conceived and so dedicated, can long
    might live. It is altogether fitting and proper that we should

.. [[[end]]] (sum: lQeAfoNG9u)
