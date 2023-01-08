---
title: SSH
description: Connect to other remote computers to deploy apps in the cloud.
links:
  - Prerequisites:
    - setup_vps
---

# SSH


For more, see github guides: [https://docs.github.com/en/authentication/connecting-to-github-with-ssh/about-ssh]()

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
