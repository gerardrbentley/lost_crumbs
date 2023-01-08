---
title: How I Edit Text Files (VS Code Settings) 
description: How to use your code editor to help you think less and write more.
categories:
    - workflow
tags:
    - beginner 
    - habits 
    - general-coding
links:
  - Prerequisites:
    - setups/ide.md
date: 2020-04-01
---

# How I Edit Text Files (VS Code Settings)


Editing Text Files.
It's the core of programming.

I admit there are a lot of GUI and block coding tools in the 21st century.

But unless you're going to retire from coding and go to woodworking, you'll probably need to at least open and view some code files or non code files.

## Why use a Code Editor?

For the same reason some teachers allow cheatsheets: **So you can focus on the relevant task**.
It's not efficient to constantly think about the syntax of your program.
It's especially not efficient to constantly run into fixable bugs and errors.

A few features in text editors that I now take for granted are:

- templating
- autocompletion & suggestion
- syntax highlighting
- syntax correction

In this post I'll focus on how I set up my VS Code to help decrease my cognitive load when coding in Python (And some bonus tips for blogging / READMEs with Markdown).
I'll go over relevant extensions for the Python ecosystem, and try to discuss different settings options you may prefer better.

**NOTE:** I personally find VS Code more friendly for new users than older text editors like Emacs and Vim, but those are also incredibly powerful and customizable.
It also has significant community extension support.
In fact, this post was partially inspired and is partially fueled by ["How I VSCode"](https://howivscode.com/about) a 100% open-source VS Code extension by [Scott W](https://scottw.com) that generates a simple public profile to share the extensions you use.
Here's mine: [howivscode.com/gerardrbentley](https://howivscode.com/gerardrbentley).

## First Steps

### Download

A VS Code download for your system should be available [here](https://code.visualstudio.com/#alt-downloads).
If you need additional directions on downloading and installing, Microsoft already has an [extensive guide](https://code.visualstudio.com/docs/setup/setup-overview) on using VS Code that I'll reference a bit.

### Open Code

I recommend using your OS's search (probably `cmd + spacebar`, `windows key`, or `super key`) and typing `code` to search and if it pops up hit enter to open VS Code with just the keyboard.

If you don't want to use the keyboard, go to your Applications folder / Start menu / Launch menu to find VS Code

### New Project Folder

For this demo we'll only be making a few files, but VS Code works best when we have a project folder, so create one now.

Use `ctrl+k` then `ctrl+o` to Open a folder.
Go ahead and create one named `/vscodetests/` and put it on your Desktop (or use a different name and location, choose your own adventure!)

If you don't want to use the keyboard, the `File -> Open Folder` option from the top bar will do the same action.

### New File

You can use `ctrl+n` to create a New file, but I usually Right-Click on the name of the folder to put the file in and select `New File`; name it something like `basic_python.py`.

If you have only one folder you can Right-Click anywhere in the left "File Explorer" panel (`ctrl+shift+e` to get it back in focus if it's gone)

Check out the default keyboard shortcuts for [mac](https://code.visualstudio.com/shortcuts/keyboard-shortcuts-macos.pdf), [windows](https://code.visualstudio.com/shortcuts/keyboard-shortcuts-windows.pdf), [linux keyboard shortcuts](https://code.visualstudio.com/shortcuts/keyboard-shortcuts-linux.pdf)

## First Extensions

After opening a new file (or saving it with `.py` ending if you used `ctrl+n` to create one), you'll probably get a popup in the bottom right corner suggesting you install the Recommended Python Extensions.
This is from Microsoft and the de-facto Python settings extension in VS Code, so go ahead and install it from there.

In general when you open a new filetype you will get a popup like this.
The features vary by language / filetype, but there are many linters, formatters, and checkers that benefit from [Language Server Protocol (LSP)](https://en.wikipedia.org/wiki/Language_Server_Protocol) these days.

If you ever want to uninstall the Python extension or install new extensions, use `ctrl+shift+x` to open the "EXtensions" panel on the left.

Some good candidates for Python project contributors:
- Python Specific
    - Python Docstring Generator (Nils Werner)
    - Even Better TOML (tamasfe)
- General VS Code
    - **RETIRED, Built In Now** Bracket Pair Colorizer 2 (CoenraadS): Visualize nested brackets and parentheses more easily
    - indent-rainbow (oderwat): Visualize deeply indented blocks more easily
    - GitLens (Eric Amodio): Quickly check git history of files, branches, lines, etc.
- Various File Types
    - Markdown TOC (AlanWalk)
    - markdownlint (David Anson)
    - XML (Red Hat)
    - SQL Formatter (adpyke)

*Bonus:* For Emacs users, "Awesome Emacs Keymap" will get you most of the way to familiar text editing keybindings

### VS Code Set Python Env and Formatter

Recommended settings in VS Code

- Type `ctrl+shift+p` then type "settings json" and select the entry, add these key-value pairs to file
    - Edit the `CHANGEME:YOURNAME` with your Windows user. (On Ubuntu based systems use `/home/username/miniconda3/bin/python`, similar for other Unix systems but with relevant user home directory)

*note*: you can instead use `ctrl+shift+p` and search "settings ui" (or use `ctrl+,`) and then search for each of the keynames below to explore what other settings you might like to try (or different choices for these options!).

```json
{
    "files.autoSave": "onFocusChange",
    "editor.wordWrap": "on",
    "editor.wordWrapColumn": 88,
    "jupyter.alwaysTrustNotebooks": true,
    "python.linting.flake8Enabled": true,
    "python.linting.flake8Args": [
        "--max-line-length=88"
    ],
    "python.analysis.typeCheckingMode": "basic",
    "workbench.editorAssociations": [
        {
            "viewType": "jupyter.notebook.ipynb",
            "filenamePattern": "*.ipynb"
        }
    ],
    "python.linting.pylintEnabled": false,
    "python.formatting.provider": "black",
    "python.linting.ignorePatterns": [
        ".vscode/*.py",
        "**/site-packages/**/*.py",
        "venv/*.py"
    ],
    "python.testing.pytestEnabled": true,
    "python.venvPath": "${workspaceFolder}"
}
```

## Get on to Getting Things Done

That's the bare-bones Python setup.

Some of the suggestions below rely on popular Python packages:

```requirements.txt
# formatter
black
# linter + static checker
flake8
# interact with jupyter notebooks
ipykernel
# sort imports in a consistent fashion
isort
# let flake8 nag you about object naming
pep8-naming
```

You can install them to your current Python environment with `pip install black` for example.

### Python Things to Try

Feel free to try out / research the following (Python related):

- Typing error-filled python code and see how `flake8` warns you
- Start your `.py` document with `# %%` to make it a VS Code ["Python Interactive"](https://code.visualstudio.com/docs/python/jupyter-support-py) document (really awesome way to experiment with code blocks and debug small chunks)
- Use `alt+shift+f` or `ctrl+shift+p` and search 'Format Document' to format python according to `black` standard
- Text Editing and Searching [Guide](https://code.visualstudio.com/docs/editor/codebasics) including stuff like using multiple cursors, search and replace over multiple files, auto save (which is included in my `json` settings above)
- Make a new virtual environment for your project with `python -m venv venv` or look into using `conda` to manage your environments
- Look into VS Code's [live code sharing](https://visualstudio.microsoft.com/services/live-share/) and [git integrations](https://code.visualstudio.com/docs/editor/github) to collaborate better


### Other Languages

Or expand your environment by setting up a few more tools (tangential to Python):

- Look into [Emmet](https://code.visualstudio.com/docs/editor/emmet) the auto completer for html files built into VS Code
- Install [Node](https://nodejs.org/en/) if you're going to be doing some web development or otherwise need `npm`
- Install [Docker](https://www.docker.com/resources/what-container) if you want to explore modern container based deployment
- Find some good [Python Reading](https://nostarch.com/catalog/python) (Ok one more Python recommendation; some of these are available for low-to-no cost from the authors)

## Relevant Links

[PyCharm](https://www.jetbrains.com/pycharm/) is tooled specifically for Python and is very popular in the community.

[JupyterLab](https://jupyterlab.readthedocs.io/en/stable/) and plain [Jupyter Notebooks](https://jupyter.org/) are common development tools for Python users as well.

[Atom](https://atom.io) and [Sublime](https://sublimetext.com) are also still rather popular among coders.

[Emacs](https://www.gnu.org/software/emacs/) and [Vim](https://www.vim.org/) are also still great (well, Emacs [lacks a decent editor](https://en.wikipedia.org/wiki/Editor_war)...)