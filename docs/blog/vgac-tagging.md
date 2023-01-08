---
title: Custom Data Tagging with Python OpenCV
description: Overview of different iterations of tools I made for tagging images in the VGAC.
categories:
  - computer-vision
tags: 
  - projects 
  - vgac
  - opencv
  - python
  - web-dev
date: 2020-04-02
---

# Custom Data Tagging with Python OpenCV


## Original

The screen capture above is the first tool used for tagging images for the Videogame Affordances Corpus (VGAC).
It was based on the python gui package [TKinter](https://www.datacamp.com/community/tutorials/gui-tkinter-python), with a simple button and keyboard interface (`q-w-e`, `a-s-d`, `z-x-c`).
It works by splitting a given image into a grid, labelling any grid tiles that are the same or very similar to 'known' tiles (i.e. tagged before).
Then the user can toggle each affordance for the unkown tiles, effectively labelling the whole image.
It also featured rudimentary sprite matching to find game characters in the images.
This turned out to be a difficult template matching task to generalize, so I tried out matching in several color and edge detection spaces (rgb, gray, sobel and laplace transformed images).
'Research-grade' Code can be found at [this gitlab repo](https://gitlab.com/gerardrbentley/original-vgac-tagging).

![Tkinter grid tagging interface](/images/vgac-tagging/tagging_interface.png)

## First Web Version

Eventually that project ran into problems with Mac OS compatibility, so the tagging tool turned to [flask](https://flask.palletsprojects.com/en/1.1.x/) a python web microframework used by many developers who like using python and want to deploy code to the web.
This got things moving forward, adding a database and the ability to have multiple people tagging images. This implementation can be found in the vgac_tagging folder at [https://pom-itb-gitlab01.campus.pomona.edu/faim-lab/vgac_tagging]
While this version is a bit dated, the closest derivative can be found at [http://pom-itb-cs1.campus.pomona.edu/tagging/expert]

## Expert Tagger

Since Flask is intended to not be asynchronous and some of our services need time to process images, the current implementation of the main tagging tool and api are built with [klein](https://klein.readthedocs.io/en/latest/), a [twisted](https://twistedmatrix.com/documents/17.5.0/core/howto/basics.html) flask (ha).
The current setup can be found at [https://pom-itb-gitlab01.campus.pomona.edu/faim-lab/vgac-webservices], including all web apps, html and js files, and server config

## Notes

## Web Services

Web App is a general term for an internet enabled browser application, be it mobile or desktop.

They don't need to be the most intricate or need too many parts. Simple apps we make consist of an html file and a Javascript file for the main functionality. 

For making it look pretty, they also utilize a css stylesheet. 

And for interacting with our videogame screenshot data they can utilize the DBAPI and / or make an additional API to process data

These are all the components of the VGAC Web Services in brief detail. For our purposes our `front-end` is mostly the html, js, css (files in the static folder), our `back-end` is the python api files, and the `server` is handled with Docker and Nginx

## Contribute a new page

In our site any file named MYPAGE in the /static/html/ folder of the production branch will generate a link at [http://pom-itb-cs1.campus.pomona.edu/html/MYPAGE.html] and [http://pom-itb-cs1.campus.pomona.edu/tagging/MYPAGE]

The intention here is that your file name is simple and relevant to the tagging topic (this may be expanded as we add more types of services / apps).

For example, the first app we added to the site was the `expert.html` page, which is at [http://pom-itb-cs1.campus.pomona.edu/tagging/expert]

Reference the [Gitlab Workflow](/blog/gitlab-workflow) page for a refresher on checking out a feature branch and adding a `To Do` Issue to the boards.

When you're happy with your $MYPAGE or at least want to see the skeleton of it live, make sure it is in the /static/html/ folder of your cloned repository

```
vgac_web
|   README.org
|   .gitlab-ci.yml
|   docker-compose.yml
|
|___OTHER_FOLDERS
|   |
|
|___static
|   |___html   
|   |   |   expert.html
|   |   |   MYPAGE.html
|   |
|   |___css   
|   |   |   style.css
|   |
|   |___js   
|   |   |   expert.js
|   |   |   OTHER_SCRIPTS.js
|   |
|   |___images 
|   |   |   examples.png
```

Then push your changes and merge them into the Master branch. 

This triggers a pipeline to deploy your page to the staging server, so it should be available at [http://pom-itb-cs1.campus.pomona.edu/staging/html/MYPAGE.html] (note the /staging/ prefix)

Once you've confirmed it seems to be working you can open a merge request from Master to Production (It is set up so you cannot push changes directly to production)

Merging Master into Production triggers the same pipeline but for the live apps, so your page should be easily accessible at [http://pom-itb-cs1.campus.pomona.edu/html/MYPAGE.html]!

## Web App Components

### HTML

The structure and content of your web page, things like titles, paragraphs, images.

For a brief intro to html and css, see [this intro](https://internetingishard.com/html-and-css/introduction/)

### CSS

A Cascading Style Sheet: defines formatting (colors, sizes, resizing, font) for different sections of the html

Generally intended to be reused on many html pages so they all have the same look and feel, but feel free to make and test your own ideas!

Some helpful starter links for resizing / formatting: 

- [https://hackernoon.com/the-ultimate-css-battle-grid-vs-flexbox-d40da0449faf]()
- [https://webdesign.tutsplus.com/articles/flexbox-vs-css-grid-which-should-you-use--cms-30184]()

In our site any css file $MYSTYLE in the static folder like so `/static/css/$MYSTYLE.css` can be reached at the pom-itb-CS1 url /css/$MYSTYLE.css

This means that in your html, you can use a line like the following to link your stylesheet and use its contents

```
<link href="/css/$MYSTLE.css" rel="stylesheet">
```

## Javascript

Code that enables interaction, changing content, and many data fetching operations (api calls)

Very popular these days, front end web design (how sites and apps look and behave) in many companies relies on front end JS frameworks such as Vue, React, and angular to make sites like Netflix and Facebook

Like css and html files, any $NEWSCRIPT.js file you add to /static/js/$NEWSCRIPT.js can be reached at pom-itb-cs1.campus.pomona.edu/js/$NEWSCRIPT.js

Similar to css, this means you can link the js code into your html file with a line like the following

```
<script src="/js/$NEWSCRIPT.js"></script>
```

If you haven't worked with Javascript at all the plethora of functions may be confusing, see [here](http://jqfundamentals.com/chapter/javascript-basics) for some crash course basics on the language

You don't need to be an expert to work with Javascript, but referencing the basics is important if you're not used to the language.

### Jquery

One of the most commonly used pieces of code on the web, [jquery](https://jquery.com/) is a library built with Javascript that gives you easier access to html elements and data, the ability to add more html from the js code, and add event loops to get data and update the page

[AJAX](http://jqfundamentals.com/chapter/ajax-deferreds) is useful for fetching data without refreshing or changing pages

If you want to use it you should follow the [jqfundamentals](http://jqfundamentals.com/chapter/jquery-basics) pages for implementing. For linking it, in your html (either in Header or the line before your own script tag) add the line

```
<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"></script>
```

This adds the code for jquery (fetched from google's server) to our html page. Then, in our NEWSCRIPT.js file we can add a line like the following to cast JQuery to `$`

```
var $ = window.jQuery;
```

### Fetch and Promise
If you don't want to bother with JQuery, the [Fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch) API with [Promises](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise) has been gaining popularity and is used by many JS frameworks.

Promises are critical to Asynchronous operations, which help parallelize work and get the user their webpage faster. The catch to async operations is that they might succeed, but they also might fail. See this [guide](https://codelabs.developers.google.com/codelabs/pwa-promises/index.html?index=..%2F..dev-pwa-training#2) for some basic examples, the next link is a follow up to this.

For relatively in-depth intro to using fetch (with modern JS coding style and practices), see [google codelabs](https://codelabs.developers.google.com/codelabs/pwa-fetch/index.html?index=..%2F..dev-pwa-training#0)

## API

An Application Programming Interface: the way Javascript in the browser asks for data. In other words, how the front end App connects to the back end server.

An API `Call` involves an internet client (browser, phone, terminal) making a `Request` to a URL (ex. http://pom-itb-cs1.campus.pomona.edu/api/test) and receiving a `Response` with data in it

If you have cURL installed in your Terminal you can ping our database api and receive a test message back with the following line

```
curl http://pom-itb-cs1.campus.pomona.edu/api/test
```

[What is An API in English](https://www.freecodecamp.org/news/what-is-an-api-in-english-please-b880a3214a82/)

In our case, and in many cases, the API lets us access data from the database in a form that is useful.

For example [[http://pom-itb-cs1.campus.pomona.edu/api/screenshot]] will provide the image data and some other meta data about a random Videogame screenshot in our database

Not all web pages need to access an API, as many pages are just text. 

One API (even one API endpoint) can be used to supply data for multiple pages. See [most called apis](https://rapidapi.com/blog/most-popular-api/) by developers and companies for some ideas on what kinds of data an API can / should provide.

## Database

We use [PostgreSQL](https://en.m.wikipedia.org/wiki/PostgreSQL)

Data is stored in tables and organized into rows. Our current database has tables for Screenshots, Tiles, Screenshot Affordance Labels and Tile Affordance Labels (with tables for Sprites to come soon probably)

Get data from here using SQL commands (well postgres is slightly different, but both have a similar syntax).

The most friendly introduction I've found is at [https://www.postgresqltutorial.com/](). Looking at examples of SELECT, FROM, and WHERE statements will get you pretty far.

## Reverse Proxy Server

Makes it easier to add and scale web apps. Accepts all internet requests to one service that decides how to handle it. 

This lets us use [Docker](https://www.docker.com/) to containerize our apps and let them communicate securely without being directly accessible by the outside world.

See [https://en.m.wikipedia.org/wiki/Reverse_proxy]() for more.

## Staging server

Having errors in live user-facing code is always bad for business. 

!!! note ""
  
    "Everybody has a testing environment. Some people are lucky enough enough to have a totally separate environment to run production in." - [tweet](https://twitter.com/stahnma/status/634849376343429120)


A Staging server let's us test out pages and catch bugs without showing them to the whole world. 

We also get a very easy `reset` point if anything goes catastrophically wrong in production

We don't have access to another domain or subdomain, so adding /staging/ at the beginning of the url will target the staging code (master branch).
Another valid strategy involves using sub domains (ex. `staging.app.com`)
