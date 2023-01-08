---
title: 3 Ways to Run Python Code
description: 3 common ways to run Python programs (and some upgrades to them!)
categories: 
    - workflow
tags:
    - python
    - beginner
links:
  - Prerequisites:
    - setups/python.md
date: 2022-02-01
---

# 3 Ways to Run Python Code


Cutting to the chase:

- `python -i` in a terminal. This begins an "interactive" or "REPL" session where you can enter code line by line or copy and paste into it. (you might be able to just enter `python`)
- `python script_name.py` in a terminal with a valid python file named "script_name.py" in the current directory. This runs the code in the file then exits
    - *Bonus:* `python -i script_name.py` combines both. It runs the code in the file, then allows you to continue entering python code in the REPL
- `python -m jupyter notebook` lets you access a code notebook in your browser for a mix of live coding and code editing. Requires `pip install notebook` or a code editor with ability to handle `.ipynb` files (such as [VS Code](https://code.visualstudio.com/blogs/2021/11/08/custom-notebooks))


<div class="video-wrapper">
<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/Arst9OlQJjA" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
</div>

## The REPL

`python -i` in a terminal.

The Python "interactive" session.
Known in other languages as a Read-Eval-Print-Loop (REPL).

This method of running Python is useful for small bits of code and experiments.
Need to test out what happens when you multiply an int and a string?
Try it out in the REPL:

```py
>>> 3 * "hello world "
```

*note:* The common notation in books and online is to use the `>>>` that appears in the terminal to indicate code can be entered as input to the Python REPL.
Don't include the `>>>` characters when copying though!

It's hard to save your work and sometimes awkward to paste code into the REPL as each line is executed without a chance to edit.

### Upgrading the REPL

Try out [iPython](https://ipython.readthedocs.io/en/stable/).
It provides a much richer experience with features such as autocomplete, command history, and saving your session.

It uses the same Jupyter kernel which powers the notebooks we'll see later. 

## Python Script

`python script_name.py` in a terminal.

Most common way to "run a Python script."
Many programmers will have their first script be something like `hello.py` with a line of code `print("hello world")`.
To execute that script, the `python` command has to be used (or use a play button in your code editor which calls `python` in the background for you)

Anything included after the script name is passed into the Python execution as entries in the `sys.argv` list, which has the script name itself as the first element.
`argv` is short for "argument values", which means they're usually used as the parameters for your script.

Save the following as `my_script.py`
```py
import sys
print(f"Command line args: {sys.argv}")
```

Then run the following in a terminal window with `my_script.py` in the current directory:
```sh
python my_script.py test args to be printed in sys.argv
```

Python will print any `print()` statements to the terminal window unless otherwise specified (see the "file" param in the [print docs](https://docs.python.org/3/library/functions.html#print)).

If your program gets stuck in an infinite loop or you need to interrupt it, hitting `ctrl+c` one or more times should give you back control of the command line.

Unlike the REPL, this is a valid way to run Python code in Production.
It doesn't require any user interaction so it can be included in a bash / batch / ci/cd script.

`python -i script_name.py` combines runs the code in the file, then allows you to continue entering python code in the REPL.
This can be useful for debugging, which can be done similarly with `breakpoint()` at the end of the script (which will require some understanding of [pdb](https://docs.python.org/3/library/pdb.html))

### Upgrading your script runs

In most cases you should prefer the built-in `argparse` and `logging` modules in order to handle command line arguments and output messages from your script.

If you're willing to use packages from outside of the standard library you can check out [Click](https://www.palletsprojects.com/p/click/), the incredibly popular CLI library.
For a project specifically focused on the CLI, [Typer](https://typer.tiangolo.com/) builds from Click with even more ~magic~ (sensible defaults and type-hinting)

As for logging, popular packages such as [structlog](https://www.structlog.org/en/stable/) (with enhancements via [rich](https://rich.readthedocs.io/en/stable/introduction.html)) and [loguru](https://github.com/Delgan/loguru) will help you format your logs in a way that's easy to read for you when you're developing and easy to parse by machines if you run your code in production.

## Jupyter Notebook

`python -m jupyter notebook` runs a code notebook server locally on your computer.

This lets you code in a Jupyter notebook in your browser.
Code notebooks are a non-traditional way of coding, but are quite popular in education, data science, and research.
Each notebook is made up of "cells" of either code or some documentation text (usually in Markdown).

Jupyter notebooks (and this post) are focused on Python code cells, but it's good to know some other languages allow this kind of interaction in various code editors and online tools.

The main benefit of notebooks is having a "live" coding environment.
You are able to run chunks of your code, observe the results, then tweak something and re-run just the last chunk.

Notebooks are also great for incorporating human readable documentation with your code and have some useful integrations with Image handling libraries and some charting and other data libraries.
Some of the most notable: `matplotlib`, `Pillow`, and `opencv`

If you didn't notice at the top, this post itself was generated from a notebook.
You can check out the notebook on github or make a copy of it and run the following Python code on your own.
Then make some changes with your own data and run it again.


```python
from datetime import datetime, date
BIRTH_YEAR = 1996

def get_min_days_old(birth_year):
    difference = date.today() - date(birth_year, 12, 31)
    return difference.days

min_days_old = get_min_days_old(BIRTH_YEAR)
min_days_old
```




    9163



### Upgrading your Notebooks

Many complaints about notebooks involve not being able to edit them like a normal text file, not being able to do normal Python library development, and difficulty testing.

Libraries such as [nbdev](https://nbdev.fast.ai/), [fastpages](https://fastpages.fast.ai/) (What this site is built with), and [fastdoc](https://fastai.github.io/fastdoc/) from [fast.ai](https://fast.ai/) address these gripes and more.

Code editors such as VS Code and Atom have ways of breaking your `.py` file up into runnable Jupyter cells with some magic comments.
VS Code calls this the [Python Interactive Window](https://code.visualstudio.com/docs/python/jupyter-support-py).
This method of using Jupyter allows more natural text-editing.
