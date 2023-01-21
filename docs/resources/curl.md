---
title: curl
description: Notes on curl
tags:
    - curl
---

Curl is a CLI utility for making web (and other) requests.

## Level Up

Combine `curl` with `jq` to pretty print JSON from responses.

```sh
curl -v "http://localhost:5001/places?name=First" | jq '.'
```

## Install MacOS

```sh
brew install curl 
brew install jq
```
