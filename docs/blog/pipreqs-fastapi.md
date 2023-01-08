---
title: "Pipreqs FastAPI Server + Github Bot"
description: Spreading pinned dependencies one repo at a time.
categories: 
    - libraries
    - deployment
tags:
    - python
    - intermediate
    - fastapi
links:
  - Prerequisites:
    - setups/python.md
date: 2022-04-21
---

# Pipreqs FastAPI Server + Github Bot



## Python Pipreqs API + Github Bot

tl;dr: [repo link](https://github.com/gerardrbentley/pipreqs-api)

<blockquote class="twitter-tweet" data-theme="dark"><p lang="en" dir="ltr">Turned my <a href="https://twitter.com/hashtag/Python?src=hash&amp;ref_src=twsrc%5Etfw">#Python</a> requirements API into a <a href="https://twitter.com/github?ref_src=twsrc%5Etfw">@github</a> <a href="https://twitter.com/hashtag/bot?src=hash&amp;ref_src=twsrc%5Etfw">#bot</a> that reminds me when I forget to update dependencies! 🤖<br><br>I used httpx and gidgethub, deployed with the existing <a href="https://twitter.com/FastAPI?ref_src=twsrc%5Etfw">@FastAPI</a> server on <a href="https://twitter.com/heroku?ref_src=twsrc%5Etfw">@heroku</a> <br><br>Followed a great guide by <a href="https://twitter.com/mariatta?ref_src=twsrc%5Etfw">@mariatta</a> -&gt; <a href="https://t.co/3GthR5urKe">https://t.co/3GthR5urKe</a> <a href="https://t.co/ARQw007LEQ">https://t.co/ARQw007LEQ</a> <a href="https://t.co/WRbuxvF3qA">pic.twitter.com/WRbuxvF3qA</a></p>&mdash; @gar@gerardbentley.com (@GarsBar35Plus) <a href="https://twitter.com/GarsBar35Plus/status/1520075920853274625?ref_src=twsrc%5Etfw">April 29, 2022</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

Powered by [FastAPI](https://github.com/tiangolo/fastapi), [pipreqs](https://github.com/bndr/pipreqs), and [gidgethub](https://gidgethub.readthedocs.io/en/latest/index.html).
Specifically, FastAPI runs the API server for receiving requests, pipreqs does the code requirements assessing, and gidgethub handles routing requests from Github Webhooks.

Basic API to power bots / helpers to rid the world of Python projects without correct requirements!
Simple bot to open an issue if `requirements.txt` doesn't match the output of `pipreqs`.

Attempts to shallow `git clone` a given repo then run `pipreqs` on the codebase.
Returns the resulting `requirements.txt` contents!

## How to Use

- Use the [pyscript frontend on github pages](https://gerardrbentley.github.io/pipreqs-api/)
- Use the [Streamlit frontend](https://share.streamlit.io/gerardrbentley/pipreqs-api/streamlit_deploy/streamlit_app/streamlit_app.py) 🎈
- Use the fastapi generated [swagger docs](https://pipreqs-api.herokuapp.com/docs#/default/pipreqs_endpoint_pipreqs_get)
- Use `curl` or other http client

```sh
curl "https://pipreqs-api.herokuapp.com/pipreqs?code_url=https://github.com/gerardrbentley/pipreqs-api"
```

Response

```txt
cachetools==5.0.0
fastapi==0.75.2
gidgethub==5.1.0
httpx==0.22.0
pydantic==1.9.0
pytest==7.1.2
streamlit==1.8.1
uvicorn==0.17.6
```

## Background

Python is a popular language, but it lacks a standard build & dependency management tool.
The official docs recommend the third party [pipenv](https://packaging.python.org/en/latest/tutorials/managing-dependencies/), and others such as [poetry](https://python-poetry.org/) and [pants](https://www.pantsbuild.org/) are available for other preferences.
Even [conda](https://anaconda.org/) can provide environment and dependency management!

Slowing things down, the basic way of installing Python packages is with [`pip`](https://pip.pypa.io/en/stable/) and a file called `requirements.txt` (which is a list of packages like the one above!)

Common guides will recommend running something like:

```sh
pip install -r requirements.txt
```

Or maybe this to make sure the active Python environment's pip gets used:

```sh
python -m pip install -r requirements.txt
```

### Deployments

This project had the goal of reducing headaches from the following loop:

- Write code for a Python / Streamlit app
- Push the code to a github repo
- Connect the repo to Streamlit Cloud
- Wait for deploy on Streamlit Cloud
- Get `"No module named"` or other error from not having up-to-date requirements

So why is this the way it is?

I could say it's because "Python lacks a standard build & dependency management tool", but I know that a simple build script / [Dockerfile](https://docs.docker.com/engine/reference/builder/) and something like [pre-commit](https://pre-commit.com/) can prevent these headaches before pushing code.

So then the answer is a combination of laziness and a desire to not bloat every repo with many tools and scripts.
Part of the beauty of managed application hosts such as [Heroku](https://heroku.com/) and [Streamlit Cloud](https://streamlit.io/cloud) is the minimal amount of setup needed to launch your app.

A truly minimal Streamlit Cloud repo just needs the `.py` file that holds the `streamlit` calls.
Once your app needs more third party Python packages than `streamlit`, some kind of dependency file is needed for the Platform to know how to install and run your app.

## Manual Method

The essence of this API and bot can be boiled down to 2 CLI calls:

- `git clone --depth 1`
- `pipreqs --print`

The clone command will download a copy of the repository that we want to check for requirements.
The `--depth 1` flag is important to limit how many files get downloaded (we don't need the whole repo history, just the latest).

[pipreqs](https://github.com/bndr/pipreqs) is a tool that analyzes a directory containing Python files and aims to produce a `requirements.txt` file with every third party package that is imported in the project directory.
The `--print` flag will tell pipreqs not to produce a file, but just to print out the file contents to stdout.

You can try this on your own!

```sh
git clone --depth 1 https://github.com/gerardrbentley/pipreqs-api test_dir
python -m pip install pipreqs
pipreqs --print test_dir

# clean up
rm -r test_dir
```

## Python Method

From Python we can either use a library such as [gitpython](https://gitpython.readthedocs.io/en/stable/reference.html?highlight=clone#git.repo.base.Repo.clone), or make the system call to `git` with the [subprocess](https://docs.python.org/3/library/subprocess.html) standard library module.

Here is a basic example (using `.split()` to avoid using [shell execution](https://docs.python.org/3/library/subprocess.html#frequently-used-arguments))

```py
import subprocess
subprocess.run('git clone --depth 1 https://github.com/gerardrbentley/pipreqs-api test_dir'.split())
```

Since `pipreqs` uses [`docopt`](http://docopt.org/) to [parse CLI arguments](https://github.com/bndr/pipreqs/blob/a593d27e3d9fcdecc0fbf385ef43116cccad71ec/pipreqs/pipreqs.py#L483), I figured it would be easy enough to repeat the `subprocess` pattern and be sure to capture the stdout output (the requirements!)

## API Endpoint

For users to access our function over the internet (and for bots 🤖 to access it!) we'll serve it up in a REST API.
Python has plenty of [web framework libraries](https://www.techempower.com/benchmarks/#section=data-r20&hw=ph&test=composite&l=zijzen-sf), pretty much any of them would handle this fine.

For version 1 of this system I've chosen to have a single endpoint that responds to HTTP GET requests and requires a query argument called `code_url`.
All it will respond with is plain text containing the `requirements.txt` contents and a `200` status code.

Here's what that looks like in my FastAPI app:

```py
@router.get("/pipreqs", response_class=PlainTextResponse)
async def pipreqs_endpoint(code_url: str):
    ... # Clone the repo from code_url
    ... # Run pipreqs on the cloned repo
    return requirements
```

## Async Python

This method so far works fine for a single user, but imagine the system with multiple users / bots making requests at once.
Each `git clone` and `pipreqs` call would have to complete for a single user before the next in the queue can be processed.

`git clone` relies on the I/O speed of our server to write files, the remote git server to read the files, and the network speed to get them to our server.
`pipreqs` includes synchronous `requests` calls to [pypi](https://pypi.org/), so it relies on the response speed of the pypi server and the I/O speed of our server to loop over project files and run `ast.parse` (from [standard library](https://docs.python.org/3/library/ast.html#ast.parse)) on the `.py` files.

WSGI frameworks such as [Flask](https://flask.palletsprojects.com/en/2.1.x/) and [Bottle](https://bottlepy.org/) rely on threading tricks such as gevent *greenlets* (read more [from Bottle](https://bottlepy.org/docs/dev/async.html)) to handle many connections in a single process.
ASGI frameworks such as FastAPI (built on [Starlette](https://www.starlette.io/)) instead rely on a single-threaded event loop and async coroutines to handle many connections.

Above we defined the `/pipreqs` route handler with `async def` function.
In FastAPI our function will already be running in the event loop so we can use `await` in our code to utilize other `async` functions!

Speaking of other `async` functions, we can swap out the synchronous `subprocess.run()` with another standard library function `asyncio.create_subprocess_exec()` (see the [asyncio subprocess docs](https://docs.python.org/3/library/asyncio-subprocess.html#subprocesses)).
This will ensure that our program can let `git clone` and `pipreqs` run without hanging up our server process when there's no work to check on.

A general asynchronous run function using exec needs a try block (using `create_subprocess_shell` will return the errors in `stderr` without raising).

```py
import asyncio
from typing import Tuple

async def _run(cmd: str) -> Tuple[str, str, int]:
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd.split(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except Exception as e:
        log.exception(e, stack_info=True)
        return "", str(e), 1
    stdout, stderr = await proc.communicate()

    return stdout.decode(), stderr.decode(), proc.returncode
```

## Primary Function

Above in the endpoint code we glossed over the most important details:

- Clone the repo from `code_url`
- Run `pipreqs` on the cloned repo

When we clone a repo we don't need to store its contents forever.
That would take a lot of storage space and each repo will get new commits that invalidate the old downloads anyway.
Making a temporary directory, cloning into it, running `pipreqs` on it, then deleting it will work just fine.

*PRE-NOTE:* We'll continue to use `async` functions

```py
import tempfile

async def pipreqs_from_url(code_url: str) -> Tuple[str, str]:
    with tempfile.TemporaryDirectory() as dir_path:
        old_requirements = await fetch_code(code_url, dir_path)
        pipreqs_output = await run_pipreqs(code_url, dir_path)
    return pipreqs_output, old_requirements
```

*NOTE:* We're adding a bit of complexity to prepare for a bot use-case, which is comparing existing `requirements.txt` to `pipreqs` result.

To clone the repo and check the contents of `requirements.txt`, we can do something like this:

```py
async def fetch_code(
    code_url: str, destination_dir: str, requirements_path: str = "requirements.txt"
) -> str:
    clone_cmd = f"git clone --depth 1 {code_url!r} {destination_dir!r}"
    stdout, stderr, returncode = await _run(clone_cmd)

    if returncode != 0:
        message = f"Could not clone the code from {code_url!r}!"
        log.exception(message, stack_info=True)
        raise HTTPException(status_code=400, detail=message)

    old_requirements = Path(destination_dir) / requirements_path
    if old_requirements.is_file():
        return old_requirements.read_text()
    else:
        return ""
```

And to run pipreqs on the directory we just cloned:

```py
async def run_pipreqs(code_url: str, dir_path: str) -> str:
    clone_cmd = f"pipreqs --print {dir_path}"
    stdout, stderr, returncode = await _run(clone_cmd)
    if returncode != 0:
        message = f"Could not run pipreqs on the code from {code_url!r}!"
        log.exception(message, stack_info=True)
        raise HTTPException(status_code=500, detail=message)
    return stdout
```

*POST-NOTE:* using HTTPException from FastAPI couples the logic of our program to the API component. I'm fine with this for now, but a more specific error to the function would allow it to be re-used more easily in another app.

## Caching

If you've written a bot that makes requests to an external API then you might see making unlimited `git clone` and `pipreqs` calls as a potential problem.

One strategy to prevent (some) repeated requests to external APIs is by caching results for your server to reference when the same user request comes in.
The Python standard library has `functools.lru_cache`, but in this case I want the results to expire if the cache becomes too large and also if more than 5 minutes has passed.

I used `cachetools` library for a tested TTLCache implementation, but to get it to work with an asynchronous function we have to get a little creative.

```py
from cachetools import TTLCache

class RequirementsCache(TTLCache):
    def __missing__(self, code_url):
        future = asyncio.create_task(pipreqs_from_url(code_url))
        self[code_url] = future
        return future
```

Since `cachetools` caches act much like a Dictionary, we can overwrite the dunder method that gets called when we try to access a key that doesn't exist!
Here we create a future / task, which is to run the `pipreqs_from_url` function.

Then we assign that future as the value for the `code_url` key (so that future checks will access that instead of going to `__missing__`)

Finally we return the bare future so that we don't lock up the program while executing `pipreqs_from_url` immediately and synchronously.

### Singular Cache

`functools.lru_cache` does come in handy for creating an object that serves as a singleton in Python.
We can treat the `RequirementsCache` for our program this way and make a small, cached wrapper function that returns it once and only once.

```py
@functools.lru_cache(maxsize=1)
def get_requirements_cache() -> RequirementsCache:
    requirements_cache = RequirementsCache(1024, 300)
    return requirements_cache
```

### Using the cache

Now we can fill in the API endpoint code!

The wrapper function to fetch the cache is synchronous so we don't need to await `get_requirements_cache()`.
Then we use Dictionary bracket notation to ask the cache for the *future*, which we must `await` to get the actual returned value from `pipreqs_from_url`

The `__missing__` function we wrote above will get called when a given `code_url` isn't in the Cache.
Otherwise the cache can return the same future that was stored earlier in `__missing__`!

```py
@router.get("/pipreqs", response_class=PlainTextResponse)
async def pipreqs_endpoint(code_url: str):
    requirements_cache = get_requirements_cache()
    requirements, old_requirements = await requirements_cache[code_url]
    return requirements
```

For this endpoint the `old_requirements` isn't useful, so we just return the `pipreqs` generated requirements.

## Github Bot

I followed [this guide](https://github-bot-tutorial.readthedocs.io/en/latest/index.html) by Python Core developer and Github Bot builder Mariatta, but adapted it to fit in FastAPI.

The main concept of our bot interaction goes as follows:

- Whenever there is a push to my repository the bot should be notified with at least the url and whoever made the push
- The bot should then run our `pipreqs_from_url` function on the repository url and this time compare the generated `requirements.txt` to any existing `requirements.txt`
- If there's a difference between the files then the bot should open an Issue on the repository to note the differences

Maybe it seems simple in concept but there's a few technical and non-technical aspects to highlight.

### Webhooks

Github (among other git hosting services) allows you to set up webhooks on your repositories.
This is the technology that will notify our bot whenever someone pushes a commit.

Webhooks prevent our bot service from having to constantly ping the repository to check for changes.
So long as we trust Github's servers are running correctly, we can be confident that our bot will be notified whenever a push happens.

We can set one up manually in a repo with a secret key to ensure no attacker sends bogus data.
To expand this idea to other users, a Github app or adapting to PubSub might be necessary to ease the creation and access of webhooks.

Check out the webhook [events and payloads documentation](https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#push) for more on what Github will send to our bot.
Which brings us to the next step, what exactly is the bot?

### Gidgethub Endpoint (the bot)

Our bot is actually another FastAPI endpoint!
It's barely a robot at all!

Since we already have a FastAPI server that will be running (to host the main endpoint), it makes sense to me to include our bot as an additional endpoint.
Another strategy would be to utilze a new web server hosted somewhere else to listen for Github's webhook events.

The guide [linked above](https://github-bot-tutorial.readthedocs.io/en/latest/gidgethub-for-webhooks.html#) utilizes aiohttp as both the server and the http client for interacting with Github **after** receiving a webhook event (since we'll open an Issue in some cases).
Another option is to use a "serverless" technology such as [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html) as your bot host, which might reduce your server costs if it is idling a lot.

Here's what the endpoint looks like FastAPI / Starlette.
Gidgethub is doing the heavy lifting, we simply pass along request headers and body to the library in order to validate and parse them.

```py
from fastapi import APIRouter, Request, Response
from gidgethub import routing, sansio

router = APIRouter()
gh_router = routing.Router()


@router.post("/", response_class=Response)
async def main(request: Request):
    body = await request.body()
    secret = os.environ.get("GITHUB_SECRET")
    oauth_token = os.environ.get("GITHUB_TOKEN")
    event = sansio.Event.from_http(request.headers, body, secret=secret)
    async with httpx.AsyncClient() as client:
        gh = gidgethub.httpx.GitHubAPI(
            client, "gerardrbentley", oauth_token=oauth_token
        )
        await gh_router.dispatch(event, gh)
    return Response(status_code=200)
```

### Automatically Opening an Issue

I considered 3 ways to alert the repo owner (myself in this case) of a potential dependency mismatch:

- Send an email
- Open a Pull Request with new `requirements.txt`
- Open an Issue with new and old `requirements.txt`

Reasons in favor of opening an Issue:

- There may be Python modules that aren't used in deployment that trigger extra dependencies in pipreqs
- A specific older vesion of a package might be required (pipreqs grabs latest version)
- Allows the user to set email preferences for alerts

The main reasons against opening a Pull Request:

- Thinking about scaling this bot into a scraper of sorts for other people's projects, it's not always courteous to open a Pull Request without alerting the maintainer in an Issue
- Some projects prefer `environment.yml` or `pyproject.toml` for dependencies

Utilizing `gidgethub`, we can write a function that responds to any `push` events to the repository:

```py
@gh_router.register("push")
async def push_to_repo_event(event, gh, *args, **kwargs):
    """
    Whenever a push is made, check the requirements matches pipreqs output; else open an issue.
    """
    url = event.data["repository"]["url"]
    pusher = event.data["pusher"]["name"]

    log.info(
        f"Recent push by @{pusher} to {url}! Checking if requirements.txt is in line."
    )
    ...
```

Next, we can utilize our `requirements_cache` the same way as in the API endpoint to fetch the requirements and old_requirements (if present) for the repo.
If our pipreqs requirements match what is in the repo, then there's nothing to do for the bot.
Otherwise, we'll grab the provided url for interacting with Issues in the repo:

```py
    requirements_cache = get_requirements_cache()
    requirements, old_requirements = await requirements_cache[url]
    if requirements == old_requirements:
        log.debug(f"Requirements satisfied in repo {url}")
    else:
        issues_url = event.data["repository"]["issues_url"]
```

Finally, we'll write a short message and use the `gh` http client to make the POST request to alert the repository owner and whoever submitted the push!

```py
        payload = {
            "title": "Check dependencies",
            "body": f"""\
⚠️ Warning! Please confirm dependencies are satisfied.
Requirements generated by pipreqs:

```txt
{requirements}
```""",
            "assignees": [pusher],
        }
        await gh.post(issues_url, data=payload)
```

## Testing

We can use `pytest` and a handful of its helpers to make testing the API and subprocess calls a bit easier:

```txt
pytest==7.1.1
pytest-asyncio==0.18.3
pytest-cov==3.0.0
pytest-mock==3.7.0
```

By using a `conftest.py` we can prepare a Starlette test client for testing the API endpoints:

```py
# conftest.py
import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import create_application


def get_settings_override():
    return Settings(testing=1)


@pytest.fixture(scope="module")
def test_app():
    app = create_application()
    app.dependency_overrides[get_settings] = get_settings_override
    with TestClient(app) as test_client:
        yield test_client
```

Then in our `test_pipreqsapi.py` we need to make sure to cue `pytest-asyncio` and clear the cache after each test in order to validate call counts:

```py
@pytest.mark.asyncio
class TestPipreqsApi:
    """Test backend logic that handles cloning repos and running pipreqs"""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        yield
        cache = get_requirements_cache()
        cache.clear()
```

From there we can test each function, building up to the main endpoint.
We'll include general tests on whether things succeed when given good inputs or mocks and whether they fail with the intended errors when bad things happen.

Testing our async subprocess run is a good example.
Here we use known command `ls` and broken command `lz` to verify our function responds as we expect.

```py
    async def test_async_run_succeeds(self):
        stdout, stderr, resultcode = await _run("ls")
        assert resultcode == 0

    async def test_async_run_fails_bad_command(self):
        stdout, stderr, resultcode = await _run("lz")
        assert resultcode == 1
        assert stderr == "[Errno 2] No such file or directory: 'lz'"
```

(I don't include git clone here since it needs to go out to an external server without other setup / guarantees.
It's definitely worth an end to end test though at some point.)

We can use monkeypatching to fake an expected result now that we've verified our `_run` function works.
This next test assumes we cloned the repo and that it didn't have an existing `requirements.txt`:

```py
    async def test_fetch_code_succeeds(self, monkeypatch):
        async def fake_run_success(*args):
            return None, None, 0

        monkeypatch.setattr(pipreqsapi, "_run", fake_run_success)
        res = await fetch_code("good_clone_url", "none")
        assert res == ""
```

To simulate the case where there is a `requirements.txt` we could set up a dummy repo with one or use mocking to pretend that any Path from pathlib can find it and read it:

```py
MOCK_REQS = """fastapi==0.75.1
gunicorn==20.1.0
pipreqs==0.4.11
uvicorn==0.17.6"""
...

    async def test_fetch_code_returns_requirements(self, monkeypatch, mocker):
        async def fake_run_success(*args):
            return None, None, 0

        monkeypatch.setattr(pipreqsapi, "_run", fake_run_success)
        mocker.patch.object(Path, "is_file", return_value=True)
        mocker.patch.object(Path, "read_text", return_value=MOCK_REQS)

        res = await fetch_code("good_clone_url", "none")
        assert res == MOCK_REQS
```

We can also use mocking to keep track of how many times a function gets called.
This is useful for validating that our cache will not call the same function twice when it has the value cached already.

```py
    async def test_requirements_cache_caches(self, mocker):
        mock_pipreqs_from_url = mocker.patch(
            "app.pipreqsapi.pipreqs_from_url", return_value=MOCK_REQS
        )
        cache = get_requirements_cache()
        result = await cache["good_clone_url"]
        second_result = await cache["good_clone_url"]
        assert result == MOCK_REQS
        mock_pipreqs_from_url.assert_called_once_with("good_clone_url")
        assert second_result == MOCK_REQS
        mock_pipreqs_from_url.assert_called_once_with("good_clone_url")
```

Finally for the endpoints we'll need to rely on the `test_app` established in `conftest.py`.
We can assert things about the status and any expected errors:

```py
    async def test_pipreqs_endpoint_succeeds(self, test_app, monkeypatch):
        async def fake_pipreqs_from_url_success(*args):
            return (MOCK_REQS, "")

        monkeypatch.setattr(
            pipreqsapi, "pipreqs_from_url", fake_pipreqs_from_url_success
        )
        response = test_app.get("/pipreqs", params={"code_url": "good_clone_url"})
        assert response.status_code == 200
        assert response.text == MOCK_REQS

    async def test_pipreqs_endpoint_fails_bad_repo(self, test_app):
        response = test_app.get("/pipreqs", params={"code_url": "bad_clone_url"})
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Could not clone the code from 'bad_clone_url'!"
        )
```

## Next Steps

Overall this was a fun project for creating a FastAPI server with caching and async distributed transactions.

It also got me to think about github bots a bit and how we might clean up Python repos going forward.

### Bot

This server works for exposing the pipreqs functionality via API, but the bot leaves some steps to be desired.
As of now the `gidgethub` handling relies on my own github account's access token and the webhooks are validated based on the secret established for my particular repo.

The bot might be better applied as a Github App to allow users to more easily click a button and get the functionality.

### API

Adding features already available in pipreqs would be straightforward with further optional query params:

- min / compatible version options
- using non-pypi package host

Adding features not already in pipreqs would be more involved or hacky:

- Convert from `requirements.txt` to `pyproject.toml` / `environment.yml`
- Async parsing and fetching package info

Another idea is on-demand Issue / Pull requests on a given repo (for helping out others without putting too much effor in yourself)