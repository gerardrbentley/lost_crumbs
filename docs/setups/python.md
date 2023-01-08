---
title: Python
description: Programming language popular for readability and powerful packages.
links:
  - Prerequisites:
    - setup_terminal
    - setup_ide
---

# Python


<div class="video-wrapper">
<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/dK52tHClH34" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
</div>

## Install Conda

- Use [Miniconda](https://docs.conda.io/en/latest/miniconda.html), the little sibling of [Anaconda](https://www.anaconda.com/products/individual#Downloads).
It manages downloading and using different python versions and has some unique "virtual environment" features that are especially nice in data science work.
    - For the most up to date information (i.e. if the following doesn't work), see the [official guide](https://conda.io/projects/conda/en/latest/user-guide/install/index.html) and click the link for your OS
    - Browser / GUI method:
        - Download the installer for Python 3.9 for your computer's OS (or 3.10 if available).
            - *note* most Windows computers are 64-bit these days, if you're unsure just [double check](https://support.microsoft.com/en-us/office/determine-whether-your-computer-is-running-a-32-bit-version-or-64-bit-version-of-the-windows-operating-system-aac162a1-0cb3-46f2-888f-2f22897396ce#:~:text=System%20Information%20window-,Click%20Start%2C%20type%20system%20in%20the%20search%20box%2C%20and%20then,the%20System%20Type%20under%20Item.)
        - Run the file that was downloaded (probably in your `~/Downloads` folder)
            - Ask it to add python to your account's `PATH` variable. 
            - Installing just for yourself should be fine for most users
    - Command line method:
        - *note* right click links on website to get specific base version of Python (latest is fine in most cases)
        - Windows Powershell
```sh
# Download the installer exe
curl -uri https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe -outfile MinicondaInstaller.exe
# Install
& .\MinicondaInstaller.exe /AddToPath=0 /InstallationType=JustMe /RegisterPython=0 /S /D=%UserProfile%\Miniconda3
```
        - Linux bash (MacOS needs different download link)
```sh
# Download
curl -url https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh --output MinicondaInstaller.sh
# Install
bash MinicondaInstaller.sh
```
        

## Setup Conda

*note* This glosses over what virtual environments actually are entirely.
This is intended to keep the document short.
In essence they are folders that each hold a specific version of python and specific versions of python packages.

2 Goals:
- Python can make new virtual environments for different projects
- Allows your code editor to utilize tools like `black` and `flake8` to automatically format your code, show you what variables and functions you can use, and catch simple errors and tpyos before you run your code

### Conda Init

After Installing Miniconda
- On windows open Anaconda Powershell Prompt on Windows, terminal for linux
    - Enter `conda init powershell` then close and move on to the next step
        - *note* if Windows fails to do the initialization and instead makes a pop-up about "Folder Security", click the pop up then take action to allow the changes.
        You'll need to re-run the `conda init` command.
- open up a new terminal
    - *note* if you installed via command line method, you may need to close your current terminal and reopen
    - If you see `(base)` on the left of your current line try running the following command
```sh
python --version
```
    - If you don't see `(base)`, try running the following command.
    Then open a new terminal window and try something like the `python --version` command again.
```sh
conda init
```

### Python Base Environment


- Install some packages in the `(base)` conda virtual environment that are useful for code formatting and testing:

```sh
# Windows Powershell
# Download the requirements file
(base)$> curl -uri https://gist.githubusercontent.com/gerardrbentley/b4fd6bdeb9167462cf990160ec246512/raw/e7194b303bb59e518e5d28c65e916cf3ebf1032a/base.requirements.txt -outfile base.requirements.txt
# Install
(base)$> python -m pip install -r base.requirements.txt

# Unix
# Download the requirements file
(base)$> curl -url https://gist.githubusercontent.com/gerardrbentley/b4fd6bdeb9167462cf990160ec246512/raw/e7194b303bb59e518e5d28c65e916cf3ebf1032a/base.requirements.txt --output base.requirements.txt
# Install
(base)$> python -m pip install -r base.requirements.txt
```

```txt
# formatter
black
# % testing coverage
coverage
# linter + static checker
flake8
# interact with jupyter notebooks
ipykernel
# sort imports in a consistent fashion
isort
# let flake8 nag you about object naming
pep8-naming
# test your code
pytest
# make pytest and coverage play nicely
pytest-cov
```

## Configure VS Code for Python

VS Code is a very popular code editor with powerful features, active community extensions, and gets useful updates frequently.
It's by no means the only way to program with Python, but it's one of the most beginner friendly ways to work on a variety of projects.

### Set up test project

Make a folder called something like `test_python` and a file inside it called `first_script.py`

```sh
mkdir test_python
cd test_python
touch first_script.py
```

### Download and Install VS Code

- Download from your [OS link](https://code.visualstudio.com/download) 
- Install with downloaded file
- Open VS Code for the first time
- If it won't work or can't open, try reading their [getting started guides](https://code.visualstudio.com/docs)

### Open your test project in VS Code

- `File` -> `Open Folder`
    - Select the `test_python` folder
    - If a "Trust this workspace" message pops up, hit agree / trust
    - Open the `first_script.py` file
        - Write something like `print('Hello There')` and save the file
- Go back to your terminal and run `python first_script.py`

### Install Extensions for Python

In VS Code, open the extensions menu on the left (or with `ctrl+shift+x`)
- Search for and install the following:
    - Python (Microsoft)
- Reload the window now (close and reopen VS Code) or install some more of the things below then reload (all are optional)

Some other nice extensions (not necessary off the bat)
- Python Specific
    - Python Docstring Generator (Nils Werner)
    - Even Better TOML (tamasfe)
- General VS Code
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
    - Edit the `CHANGEME:USERNAME` with your Windows user. (On Ubuntu based systems use `/home/username/miniconda3/bin/python`, similar for other Unix systems but with relevant user home directory)

*note*: you can instead use `ctrl+shift+p` and search "settings ui" (or use `ctrl+,`) and then search for each of the keynames below to explore what other settings you might like to try.

```json
{
    "python.pythonPath": "C:\\Users\\CHANGEME:USERNAME\\miniconda3\\python.exe",
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

## Learn More

Feel free to try out / research the following (Python related):

- Typing error-filled python code and see how flake8 warns you
- Start your `.py` document with `# %%` to make it a VS Code ["Python Interactive"](https://code.visualstudio.com/docs/python/jupyter-support-py) document (really awesome way to experiment with code blocks and debug small chunks)
- Use `alt+shift+f` or `ctrl+shift+p` and search 'Format Document' to format python according to `black` standard
- Text Editing and Searching [Guide](https://code.visualstudio.com/docs/editor/codebasics) including stuff like using multiple cursors, search and replace over multiple files, auto save (which is included in my `json` settings above)
- Make a new virtual environment for your project with `python -m venv venv` or look into using `conda` to manage your environments
- Look into VS Code's [live code sharing](https://visualstudio.microsoft.com/services/live-share/) and [git integrations](https://code.visualstudio.com/docs/editor/github) to collaborate better

Or expand your environment by setting up a few more tools (tangential to Python):

- Look into [Emmet](https://code.visualstudio.com/docs/editor/emmet) the auto completer for html files built into VS Code
- Install [Node](https://nodejs.org/en/) if you're going to be doing some web development or otherwise need `npm`
- Install [Docker](https://www.docker.com/resources/what-container) if you want to explore modern container based deployment
- Find some good [Python Reading](https://nostarch.com/catalog/python) (Ok one more Python recommendation; some of these are available for low-to-no cost from the authors)

