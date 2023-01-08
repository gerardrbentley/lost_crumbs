---
title: macOS
description: Returning to brew after a few years without a macbook.
---

# macOS


Developer Setup

*NOTE:* at some point you will be prompted to install the “Command Line Developer Tools” for Xcode.
This is a large download.
Be prepared.

### Python

Mac still ships with python 2, but [one day maybe it won’t…](https://www.macrumors.com/2022/01/28/apple-removing-python-2-in-macos-12-3/#:~:text=Apple%20will%20no%20longer%20bundle,security%20patches%2C%20or%20other%20changes.)

I prefer using [conda](https://docs.conda.io/en/latest/miniconda.html) to manage python anyway, so [my install notes](https://tech.gerardbentley.com/python/beginner/2022/01/29/install-python.html) works just fine for me.

```sh
# Note, this uses macOS Apple M1 installer. Use apple menu -> About This Mac to check if “Chip” is Apple M1

# Download
curl https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh -o conda_installer.sh

# Install with human prompts, agree to license and conda init
bash conda_installer.sh

# Cleanup your computer
rm conda_installer.sh


# (if needed for script) Silent Install
bash conda_installer.sh -b
source miniconda3/bin/activate && conda init zsh 
```

In a new Terminal, update python version to desired 3.9 or 3.10 or [what have you](https://endoflife.date/python)

```sh
conda install python=3.10
```

Add packages you might want for development and testing.
(This is where I had to install Xcode developer tools in order to build python packages)

```sh
pip install black flake8 isort pep8-naming pytest-cov
```

Optionally install tools from the [Project Jupyter](https://jupyter.org/) ecosystem:

```sh
# Just jupyter notebook server
pip install notebook 
# Jupyterlab capability
pip install jupyterlab
```

### VS Code

- Download the [Mac installer](https://code.visualstudio.com/download) (it should choose the correct version for your system)
- Unzip it from your browser downloads or Finder -> Downloads
- Move the “Visual Studio Code” Application to Applications if desired
- Delete the Installer zip if desired

*NOTE:* I couldn’t find the correct link to download with curl

#### Extensions

- Dracula (theme)
- Python Specific
  - Python (Microsoft official)
  - Python Docstring Generator (Nils Werner)
  - Even Better TOML (tamasfe)
- General VS Code
  - indent-rainbow (oderwat): Visualize deeply indented blocks more easily
  - GitLens (Eric Amodio): Quickly check git history of files, branches, lines, etc.
- Various File Types
  - Markdown All in One (Yu Zhang)
  - Markdown navigation (AlanWalk)
  - markdownlint (David Anson)
  - Paste Image (mushan)
  - Markdown Preview Github Styling (Matt Bierner)
  - Markdown Emoji (Matt Bierner)
  - Docker (Microsoft)
  - YAML (Red Hat)
  - XML (Red Hat)
  - SQL Formatter (adpyke)

#### Settings

I tend to put these in the VS Code settings (`cmd + shift + p` then type "settings JSON" for one way to get there).

A lot of these are Python experience and specific to using `flake8`, `black`, and `isort`.
These are the first several up to and including the "autoDocstring" entry.

That said, there's some that are useful for general editing, searching large code bases, and working with the integrated terminal.
Shoutout to [Harald Kirschner's tips](https://gist.github.com/digitarald/f19acbe2bfdefa4d282b3196bde3fff7) (and [presentation](https://www.youtube.com/watch?v=fyg9Uw3CLUU)).

```json
{
    "python.condaPath": "~/miniconda3/bin/conda",
    "python.defaultInterpreterPath": "~/miniconda3/bin/python",
    "python.formatting.provider": "black",
    "python.linting.flake8Enabled": true,
    "python.linting.enabled": true,
    "python.testing.pytestEnabled": true,
    "python.sortImports.path": "isort",
    "python.sortImports.args": [
        "--profile black"
    ],
    "python.terminal.executeInFileDir": true,
    "jupyter.askForKernelRestart": false,
    "terminal.integrated.inheritEnv": false,
    "autoDocstring.startOnNewLine": true,
    "workbench.colorTheme": "Dracula Soft",
    "telemetry.telemetryLevel": "off",
    "security.workspace.trust.untrustedFiles": "open",
    "files.autoSave": "onFocusChange",
    "terminal.integrated.allowChords": false,
    "search.mode": "reuseEditor",
    "search.searchEditor.doubleClickBehaviour": "openLocationToSide",
    "files.defaultLanguage": "${activeEditorLanguage}",
    "workbench.editor.pinnedTabSizing": "shrink",
    "editor.minimap.enabled": false,
    "diffEditor.ignoreTrimWhitespace": false,
}
```

#### Keybindings

Some things are worth changing for productivity and matching other tools.

- Jump to beginning of text in the line: `ctrl + a`
- Jump to top / bottom of file: `shift + cmd + ,` and `shift + cmd + /`
  - From Emacs muscle memory trying to get something similar

```json
[
    {
        "key": "ctrl+a",
        "command": "cursorHome"
    },
    {
        "key": "shift+cmd+,",
        "command": "cursorTop",
        "when": "textInputFocus"
    },
    {
        "key": "shift+cmd+/",
        "command": "cursorBottom",
        "when": "textInputFocus"
    },
    {
        "key": "shift+cmd+,",
        "command": "-editor.action.inPlaceReplace.up",
        "when": "editorTextFocus && !editorReadonly"
    }
]
```

### Docker

For running applications and mocking linux filesystems.

Docker recommends installing Rosetta 2 when running [on Apple Silicon](https://docs.docker.com/desktop/mac/apple-silicon/).
This will install it to translate from Intel to M1:

```sh
softwareupdate --install-rosetta
```

- Download the `.dmg` 
- Open and `.dmg` then drag the Docker Application into Applications
- Search or open Docker from spotlight
- Accept terms and conditions
- Try to run the hello world application

```sh
docker run -rm hello-world
```

### Github

I use SSH keys to connect to github / gitlab / etc. for convenience and making the connection work out of the box from tools like VS Code.

#### Set Default Git User

Set your preferences so tools like VS Code will use these on your commits by default.

```sh
git config --global user.name "Your Name Here" 
git config --global user.email "your_email@your_domain.com"
```

#### Create SSH Key

It's best to create new keys for new machines as opposed to copying an old key from one machine to another.
Use a password if other people have access to your machine, otherwise feel free to leave blank.

```sh
ssh-keygen -t ed25519 -f ~/.ssh/github_key
```

#### Add Github to SSH Config

To make sure this key gets used when we try to authenticate to Github, we'll add the following entry to `~/.ssh/config`:

```txt
Host github.com
    PreferredAuthentications publickey
    IdentityFile ~/.ssh/github_key
```

To do this with a terminal editor use one of the following:

```sh
nano ~/.ssh/config
vim ~/.ssh/config
ed ~/.ssh/config
```

To do this with a GUI editor, you have to make sure the file exists first:

```sh
touch ~/.ssh/config
open ~/.ssh/config
```

#### Add Public Key to Github

Copy your public key to the clipboard with the following:

```sh
pbcopy < ~/.ssh/github_key.pub
```

Alternatively you can paste it out and copy by hand:

```sh
cat ~/.ssh/github_key.pub
```

*NOTE:* be sure you are copying your `.pub` Public key, and not the Private key

- Navigate to your github Account -> Settings -> SSH and GPG keys (under "Access", or [this link](https://github.com/settings/keys))
- Select `New SSH Key`

![Github SSH and GPG keys page](/images/ssh/2022-02-19-11-29-30.png)

- Enter a nickname for your machine
- Paste the Public key into the main text area

![Github add SSH key page](/images/ssh/2022-02-19-11-32-12.png)

#### Test Authentication

This command should spit out a message like `Hi {username}! You've successfully authenticated` if successful.

```sh
ssh -T git@github.com
```

### Homebrew

See [main site](https://brew.sh/): “Installs the stuff you need that Apple didn’t”

```sh
# Grab and install homebrew from latest GitHub release
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# Add to PATH
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> /Users/gar/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### Amethyst

Window Tiling Manager for macOS 10.12+ by [ianyh](https://ianyh.com/amethyst/).
For splitting windows left and right, full screen, quarters, etc.

```sh
brew install --cask amethyst
```

Open application and grant Accessibility Privacy permissions in Security & Privacy System Preferences
