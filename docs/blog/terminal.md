---
title: The Terminal (/ Shell / Command Line / Console)
description: Some basics of Terminal usage, hopefully demistifying some things in the way.
categories: 
  - workflow
tags:
  - beginner
links:
  - Prerequisites:
    - setups/terminal.md
date: 2020-04-03
---

# The Terminal (/ Shell / Command Line / Console)


## What's a Terminal

The Terminal, which you might also hear called shell, console, or command line (with a fair bit of [nuance](<(https://askubuntu.com/questions/506510/what-is-the-difference-between-terminal-console-shell-and-command-line)>)) is a program that lets you enter commands for the computer to run.
In different computers the program will vary (Terminal, Powershell, bash, etc.), but the idea of interacting with the computer using text commands one line at a time is present in all of them.

## Why Keyboard Over Mouse?


So the Terminal lets you access apps and files and execute programs without using a mouse or other windows, but why would you want to abandon your mouse?
All of the work we do in a Terminal is both plain text and can be automated much more easily than mouse movements and clicks.

Using a shell also usually gives you access to the Kernel of your OS, the software in control of basically all your applications, so you can take back your technological freedom.

Finally, Graphical (GUI) interfaces aren't available for all programs, especially a lot of the older software.
It's generally easier to develop a program that takes a few Command Line arguments than a full blown GUI Application.

## 3 Navigation Commands

When you open Terminal.app (on many linux distros use `super+spacebar`, on mac you use `command+spacebar` then search `Terminal`) all you get is a blank command line prompt, probably ending with `$`

The terminal works like a filesystem/Finder window in that you need to navigate 'up' and 'down' into different folders to find particular files.
When you open a new Terminal it is most likely located at your account's Home folder (also referred to as `~`).

**NOTE:** On Mac the `~` can be replaced with `/Users/YOUR-USERNAME/` for an "absolute" path ([absolute vs relative](https://www.linuxnix.com/abslute-path-vs-relative-path-in-linuxunix/) explanation).
Ubuntu based distros `~` == `/home/YOUR-USERNAME/`.
And Windows is different... `~` == `C:\Users\YOUR-USERNAME`.
For reference, your Desktop folder is located at ~/Desktop, your Documents at ~/Documents

Now for the 3 Basic commands that will help you navigate around (type these in the command line and hit `enter`):

### PWD

```bash
pwd
```

`Print Working Directory`: Tells you where in the filesystem the command line is currently pointed.
On a fresh Terminal window it should show `/Users/YOUR-USERNAME/`

### LS

```bash
ls
```

`List`: Lists out all the files and directories in the current directory you're pointed at.
Also helps you know where in the filesystem you are and what files you have easy access to.

### CD

```bash
cd
```

`Change Directory`: Actually moves where the command line is pointed to a different directory / folder.

The common uses of `cd` and `ls`:

## Go to your project folder

On my personal computer I try to keep all my coding projects under a folder called `research` (in their own individual folders) which is in my Home folder (`~/research` or `/Users/Gerard/research`)

So to get to my project I open terminal and enter

```bash
cd research/my-project-folder
```

**NOTE**: This works because the Terminal is already pointed at my `~/` directory and `research` is in that directory.
You can use `ls` to see if `research` is present in your Home directory

If you don't remember the project-folder name you can do the following

```bash
cd research
ls
```

This will show you all the files and folders in `research`, then you can `cd` directly into it without the `research/` part

```bash
cd project-folder-i-remember-now
```

## Go back one or more directories

Just like `~/` is a shorthand symbol for "Home Directory", `./` is a symbol for the current working directory (`pwd`)

By this I mean that `.` represents the current working directory, where the terminal command line is pointed.

So the same command from before works the same like this (from a fresh Terminal located at `~/`)

```bash
cd ./research/my-project-folder
```

After executing that command, `pwd` will tell you the Terminal is at `/Users/Gerard/research/my-project-folder`, which we want because we just `cd`d into that directory

If we wanted to switch projects (to a different folder in `research`), we need to go 'up' a folder. To do this we use `..` to represent the folder 'above' the current folder

```bash
cd ..
```

This brings us back to `research`, so `pwd` will say `/Users/Gerard/research/`

Now we can cd into a different folder

```bash
cd my-other-project-folder
```

If we wanted to switch to a different project directly in one command we can use

```bash
cd ../third-folder
```

I think of this as 'going to third-folder, which is in the folder above the current one'

## Going Further

`ls` and `cd` should get you far enough to run Python scripts (also using `python` as a command!).

Making your own or finding a terminal commands [cheatsheet](https://www.git-tower.com/blog/command-line-cheat-sheet/) online can be extremely helpful when first starting out.
Repetition is key to becoming comfortable with and memorizing these things.
Nobody memorizes them after the first use!