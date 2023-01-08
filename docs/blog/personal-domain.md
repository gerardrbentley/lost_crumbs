---
title: Share a website to the world in less than a day (Free for Students!)
description: Using Google Domains, Gitlab Pages, and some basic HTML and CSS to make a fun public facing webpage.
categories:
  - deployment
tags: 
  - beginner
  - web-dev
  - deployment 
  - guide
date: 2020-03-28
---

# Share a website to the world in less than a day (Free for Students!)


## Why make your own website?

Your own digital footprint and learning coding building blocks!
Nowadays you can access a website from anywhere on pretty much any device, it can be simple, it can be personal, you can show your friends, you can show your family, you can show the internet.
It's a pretty cool feeling to see code you wrote on someone else's screen, and hopefully it'll encourage you to keep exploring.

If you don't mind having a slightly less custom domain then there are plenty of free options that will host your site as a 'subdomain'. In fact this site is accessible at [https://gerardrbentley.gitlab.io/](https://gerardrbentley.gitlab.io/), which is the way I set it up with [Gitlab Pages](https://docs.gitlab.com/ee/user/project/pages/#getting-started) where I host this project's [code](https://gitlab.com/gerardrbentley/gerardrbentley.gitlab.io).
If you happen to want to know a bit more about how domains actually work, [this site](https://whatismyipaddress.com/domain-name) has a decent introduction.

A custom domain (website) name goes for around $12 USD per year, but students can get 3! free domains with [The Github dev pack](https://education.github.com/pack) (highly recommended if you're eligible). 
I use [Google Domains](https://domains.google.com) for this domain ([gerardbentley.com](https://gerardbentley.com)) mostly because I trust they won't have any hidden fees, won't leak my credit card info, and will be reliable.
Feel free to use [GoDaddy](https://www.godaddy.com/) or [Namecheap](https://www.namecheap.com/domains/domain-name-search/) or any other domain name service you prefer.
Custom domains are limited to one owner, so don't be disappointed if someone else got what you wanted first (capitalism!).

**NOTE** Plenty of businesses these days probably pop up in your ads telling you how easy it is to build a site with them, but that's not what this guide is about. Wix, Squarespace, and Wordpress are valid tools on their own, but this method of building a site uses tools that will be useful in more general software development (HTML, JavaScript, Continuous Integration / Deployment tools).

## Project Repository

[Gitlab](https://gitlab.com) is where I prefer to keep the code for my projects (repositories).
It's open source with a free tier that is plenty decent for my use and because it supports the full lifecycle of your app in one place.
[Github](https://github.com) is also super popular, probably still more popular than Gitlab, and [Github Pages](https://pages.github.com/) is their hosting service, but I won't discuss that further.

For more on gitlab and some pointers on managing a project that you update over time or work on with others, see <nuxt-link to="gitlab-workflow">my post</nuxt-link> on Gitlab Workflow.
It also has a decent web editor if you haven't set one up on your machine, see <nuxt-link to="how-i-vs-code">my post</nuxt-link> on how I use VS Code if you want to improve the way you type.
