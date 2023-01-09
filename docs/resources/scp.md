---
title: SCP
description: Steps to copy files securely between local and server or between servers.
---


## Transfer with SCP

SCP is the Secure Copy command.
It uses your SSH connection to transfer files.

```sh
scp sshUser1:/files/file.txt user2@host2.com:/files
```

## Compress and Uncompress

```sh
# Compress Directory Recursively 
zip -r backup.zip the_folder_name/
```
