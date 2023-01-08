---
title: Git
description: Essential tool for code management in solo and team projects.
categories: 
  - workflow
tags:
  - git
  - beginner
links:
  - Prerequisites:
    - setups/git.md
date: 2023-01-03
---

# Git


### Cloning and Branching:

### Fixing your local Repo:

#### Reset my local Repo to whatever is online

If people have made many changes and you haven't caught up, it's sometimes easiest to just reset your local folder to whatever is on the server.

For more nuance, see this [stack overflow post](https://stackoverflow.com/questions/1628088/reset-local-repository-branch-to-be-just-like-remote-repository-head)

```
git fetch origin
git reset --hard origin/master
```

#### git push origin master FAILS

If someone else changed `Master` and you haven't received those, you may get an error (probably in red and yellow) that resembles the following:

```
error: failed to push some refs to 'git@pom-itb-gitlab01.campus.pomona.edu:web-lab/web-resources.git'
hint: Updates were rejected because the remote contains work that you do
hint: not have locally. This is usually caused by another repository pushing
hint: to the same ref. You may want to first integrate the remote changes
hint: (e.g., 'git pull ...') before pushing again.
```

##### SOLUTION 1:
Try a simple git pull. If you didn't change the same files that others did then you should receive their changes painlessly.

``` bash
git pull origin master
```

This may get you into the land of Vim, a text editor that lives entirely in the terminal, it's ok to be confused, it happens to [most people trying to exit vim](https://www.reddit.com/r/ProgrammerHumor/comments/8poep0/a_vim_joke/).

To escape vim and save the merge, type the follow key cominations: `escape` then `shift+;` (a colon) then `w` then `q` then `enter`

##### SOLUTION 2:

If the git pull origin master command fails, you may get an error like the following:

``` bash
remote: Total 3 (delta 2), reused 1 (delta 0)
Unpacking objects: 100% (3/3), done.
From gitlab.com:username/web-resources
 * branch            master     -> FETCH_HEAD
   f62b1f8..118f52e  master     -> origin/master
Auto-merging index.html
CONFLICT (content): Merge conflict in index.html
Automatic merge failed; fix conflicts and then commit the result.
```

This means that you tried to edit the same file that someone has already updated on the master branch of the server.

Opening up your <nuxt-link to="how-i-vs-code">code editor</nuxt-link> and opening the conflicting files you're trying to merge should give you several options:
- Keep only the work that the others added and discard your changes (probably not what you want)
- Keep only the work that you added and discard others' changes (also probably not the goal)
- Keep both (may need to add more lines, but often we want to collaborate, not clobber)
- Keep some of each (some work is mutually exclusive and needs to pick one or the other)


### Broken / Wrong Origin link:

### Hard reset all files (fetch other's work)

### Fixing the remote Repo:

#### Pushed wrong files to Gitlab.

Sometimes you have temporary files / images locally that you don't need to push to everyone via Gitlab.
Sometimes those images / large files end up in the repo but others don't want to download them when they clone it, so we'll remove them

##### SOLUTION:

Files and folders listed in .gitignore will not be tracked by git (i.e. you can use `git add .` and it won't wrongfully add gitignored files). Learn more on gitignore syntax (https://www.atlassian.com/git/tutorials/saving-changes/gitignore)[here].

After updating .gitignore to list the files you want to remove from remote gitlab,

``` bash
git rm -r --cached .
git add .
git commit -m "Removed large files from repo..."
git push origin CURRENT-BRANCH-NAME
```

This assumes there are files you need to `re-ignore` in folders throughout the project. If it's a single folder (`./VERY_FULL_FOLDER/`) or file (`./path/to/one_file_to_remove.py`) then you should replace the `.` in the first command to that path (i.e. `./VERY_FULL_FOLDER`) and only the files in that folder will be searched.
