---
title: VPS
description: Renting a server for running web services and other programs in the cloud.
links:
  - Prerequisites:
    - setup_terminal
---

# VPS


## Cloud Providers

Most cloud hosts have a basic VPS option.

A small (1 cpu, 1 gb ram) shared machine should be around `$5` a month.

- Amazon AWS
- Google GCP
- Microsoft Azure
- Linode
- DigitalOcean
- Vultr

## Operating System

Since it's a server, choose an OS lightweight and configurable enough for your needs.

Debian is usually a dependable choice of Linux distribution.

## Security

Be sure to learn some aspects of how and why bots try to get into your server.

Common hardening practices:

- Don't allow `root` login remotely
- Use a user with `sudo` priviliges if needed
- Don't allow remote logins with password (only SSH key)
- Use a system such as Universal Firewall `ufw` to block connections on all ports other than those necessary 
  - Usually 80 for HTTP webserver traffic
  - Usually 443 for HTTPS webserver traffic
  - Usually 22 for SSH connections
    - Many bots will check 22, so this can be configured
- Use a system such as `fail2ban` to block repeated attempts from certain IP addresses

See guides from:

- [Linode](https://www.linode.com/docs/guides/set-up-and-secure/)
- [Digital Ocean](https://www.digitalocean.com/community/tutorials/how-to-harden-openssh-on-ubuntu-20-04)