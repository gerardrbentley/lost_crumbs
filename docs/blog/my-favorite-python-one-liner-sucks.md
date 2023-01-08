---
title: My Favorite Python One Liner Sucks
description: Turning Path into muscle memory
categories:
    - python
tags:
    - beginner
    - python
links:
  - Prerequisites:
    - setups/python.md
date: 2022-02-15
---

# My Favorite Python One Liner Sucks


## Writing to a file in one line

tl;dr it's now:


```python
# Write data to file called my_file.txt
Path('my_file.txt').write_text('\n'.join(some_data))
```




    15




```python
# Setup
some_data = ['alice', 'bob', 'chuck']  # Some sample data
from pathlib import Path
```

## Favorite One-Liner

Python is full of one-liners.

One of my favorites has been:


```python
open('my_file.txt', 'w').write('\n'.join(some_data))
```




    15



It opens a file in write mode and writes some data or other text to that file, returning the amount of bytes written to the file.
Generally useful for saving a list of column names or people names or what have you.
No external libraries, and even no extra imports because [`open()` is a built-in function](https://docs.python.org/3/library/functions.html#open)

But it leaves the file handle open...

Which may not be a problem in some usecases, but it can prevent other users or processes from moving or deleting the file.
[Google's Python style guide](https://google.github.io/styleguide/pyguide.html#311-files-and-sockets) provides some more reasons, including wasting resources and preventing logical errors in code.

## With Statement

Of course the `with ... as ...:` [syntax](https://docs.python.org/3/reference/compound_stmts.html#the-with-statement) from [PEP 343](https://www.python.org/dev/peps/pep-0343/) is great for this safe handling of a file object that has to be opened and closed.

It can be done in one line, but most prefer to break it up into 2.
This is more awkward to use in a REPL doing ad-hoc work or notebook trying to conserve cell space 


```python
with open('my_file.txt', 'w') as f: f.write('\n'.join(some_data))
```


```python
with open('my_file.txt', 'w') as f: 
    f.write('\n'.join(some_data))
```

## Comparing With and Without (With)

Checking out the bytecode on a simplified `write`, we can confirm that my favorite one-liner doesn't close the file, whereas the `with` one-liner does.

(If you're not familiar with [dis](https://docs.python.org/3/library/dis.html), it's the Python module for disassembling Python code into its C bytecode. Not always necessary, but will prove 100% whether 2 code snippets operate the same under the covers)


```python
from dis import dis
dis("open('my_file.txt', 'w').write('something')")
```

      1           0 LOAD_NAME                0 (open)
                  2 LOAD_CONST               0 ('my_file.txt')
                  4 LOAD_CONST               1 ('w')
                  6 CALL_FUNCTION            2
                  8 LOAD_METHOD              1 (write)
                 10 LOAD_CONST               2 ('something')
                 12 CALL_METHOD              1
                 14 RETURN_VALUE


Definitely no calls to `close()`.
What about in the with statement?


```python
dis("with open('my_file.txt', 'w') as f: f.write('something')")
```

      1           0 LOAD_NAME                0 (open)
                  2 LOAD_CONST               0 ('my_file.txt')
                  4 LOAD_CONST               1 ('w')
                  6 CALL_FUNCTION            2
                  8 SETUP_WITH              26 (to 36)
                 10 STORE_NAME               1 (f)
                 12 LOAD_NAME                1 (f)
                 14 LOAD_METHOD              2 (write)
                 16 LOAD_CONST               2 ('something')
                 18 CALL_METHOD              1
                 20 POP_TOP
                 22 POP_BLOCK
                 24 LOAD_CONST               3 (None)
                 26 DUP_TOP
                 28 DUP_TOP
                 30 CALL_FUNCTION            3
                 32 POP_TOP
                 34 JUMP_FORWARD            16 (to 52)
            >>   36 WITH_EXCEPT_START
                 38 POP_JUMP_IF_TRUE        42
                 40 RERAISE
            >>   42 POP_TOP
                 44 POP_TOP
                 46 POP_TOP
                 48 POP_EXCEPT
                 50 POP_TOP
            >>   52 LOAD_CONST               3 (None)
                 54 RETURN_VALUE


The context manager takes a lot more steps to manage the call stack.
But there's no clear call to the `close()` function, which is the other standard way of writing to a file and closing the handle.


```python
dis("f = open('my_file.txt', 'w')\nf.write('something')\nf.close()")
```

      1           0 LOAD_NAME                0 (open)
                  2 LOAD_CONST               0 ('my_file.txt')
                  4 LOAD_CONST               1 ('w')
                  6 CALL_FUNCTION            2
                  8 STORE_NAME               1 (f)
    
      2          10 LOAD_NAME                1 (f)
                 12 LOAD_METHOD              2 (write)
                 14 LOAD_CONST               2 ('something')
                 16 CALL_METHOD              1
                 18 POP_TOP
    
      3          20 LOAD_NAME                1 (f)
                 22 LOAD_METHOD              3 (close)
                 24 CALL_METHOD              0
                 26 POP_TOP
                 28 LOAD_CONST               3 (None)
                 30 RETURN_VALUE


The `open()` function code lives [here](https://github.com/python/cpython/blob/602630ac1855e38ef06361c68f6e216375a06180/Lib/_pyio.py#L73).

It's a wrapper around a FileIO object, whose `close` method will use `os.close()`, the low-level file closing method.

The FileIO inherits a context manager from IOBase that calls `close` when exited, so we can be sure it'll get called.

## Pathlib usage

Making the extra import is worth it for `Path` object to get the following:

- Accurate path on [any OS](https://docs.python.org/3/library/pathlib.html)
- file open and close with [`write_text()`](https://docs.python.org/3/library/pathlib.html#pathlib.Path.write_text)
- Still a similar one-liner!



```python
from pathlib import Path
Path('my_file.txt').write_text('\n'.join(some_data))
```




    15



Does the disassembler tell us anything?


```python
dis("Path('my_file.txt').write_text('something')")
```

      1           0 LOAD_NAME                0 (Path)
                  2 LOAD_CONST               0 ('my_file.txt')
                  4 CALL_FUNCTION            1
                  6 LOAD_METHOD              1 (write_text)
                  8 LOAD_CONST               1 ('something')
                 10 CALL_METHOD              1
                 12 RETURN_VALUE


Not really, what about on the write_text method specifically?


```python
dis(Path('my_file.txt').write_text)
```

    1282           0 LOAD_GLOBAL              0 (isinstance)
                   2 LOAD_FAST                1 (data)
                   4 LOAD_GLOBAL              1 (str)
                   6 CALL_FUNCTION            2
                   8 POP_JUMP_IF_TRUE        26
    
    1283          10 LOAD_GLOBAL              2 (TypeError)
                  12 LOAD_CONST               1 ('data must be str, not %s')
    
    1284          14 LOAD_FAST                1 (data)
                  16 LOAD_ATTR                3 (__class__)
                  18 LOAD_ATTR                4 (__name__)
    
    1283          20 BINARY_MODULO
                  22 CALL_FUNCTION            1
                  24 RAISE_VARARGS            1
    
    1285     >>   26 LOAD_FAST                0 (self)
                  28 LOAD_ATTR                5 (open)
                  30 LOAD_CONST               2 ('w')
                  32 LOAD_FAST                2 (encoding)
                  34 LOAD_FAST                3 (errors)
                  36 LOAD_CONST               3 (('mode', 'encoding', 'errors'))
                  38 CALL_FUNCTION_KW         3
                  40 SETUP_WITH              26 (to 68)
                  42 STORE_FAST               4 (f)
    
    1286          44 LOAD_FAST                4 (f)
                  46 LOAD_METHOD              6 (write)
                  48 LOAD_FAST                1 (data)
                  50 CALL_METHOD              1
                  52 POP_BLOCK
                  54 ROT_TWO
                  56 LOAD_CONST               4 (None)
                  58 DUP_TOP
                  60 DUP_TOP
                  62 CALL_FUNCTION            3
                  64 POP_TOP
                  66 RETURN_VALUE
             >>   68 WITH_EXCEPT_START
                  70 POP_JUMP_IF_TRUE        74
                  72 RERAISE
             >>   74 POP_TOP
                  76 POP_TOP
                  78 POP_TOP
                  80 POP_EXCEPT
                  82 POP_TOP
                  84 LOAD_CONST               4 (None)
                  86 RETURN_VALUE


Well that's a whole lot to end up looking like the same bytecode as the `with` statement...

In fact, pathlib would have gotten away with it too if it weren't for that meddling [source code](https://github.com/python/cpython/blob/602630ac1855e38ef06361c68f6e216375a06180/Lib/pathlib.py#L1070) to betray it!

We wind up calling the same with statement, but get a free assertion that our data is a valid string:

```python
# pathlib.Path.write_text
# ...
        with self.open(mode='w', encoding=encoding, errors=errors, newline=newline) as f:
            return f.write(data)
```

## Conclusion

Pathlib `write_text()` is just `with open()...` under the covers.

Nevertheless, I prefer the `write_text()` one-liner to the `with open() as f: ...` one-liner out of respect for colons.


