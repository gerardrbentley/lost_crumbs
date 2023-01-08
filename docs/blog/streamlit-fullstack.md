---
title: "Streamlit Full Stack Part 1: Python Web App in One File"
description: Exploring Streamlit + SQLite for the littlest Full Stack app.
categories: 
    - libraries
tags:
    - streamlit
    - python
    - beginner
links:
  - Prerequisites:
    - setups/python.md
date: 2022-02-10
---

# Streamlit Full Stack Part 1: Python Web App in One File



[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/gerardrbentley/streamlit-fullstack/app.py)

A Frontend, Backend, and Data Store in one Python file!

Create, Read, Update, and Delete from a feed of 140 character markdown notes!

ex:
![view of app with system generated note](/images/streamlit_fullstack/2022-03-02-22-55-24.png)


## The Littlest Full Stack App

The idea for this was starting with built-in [sqlite](https://www.sqlite.org/index.html) [module](https://docs.python.org/3/library/sqlite3.html) and [streamlit](https://docs.streamlit.io/) to build a full stack application in a single Python file:

- Streamlit
  - Frontend
- Python w/ SQLite3
  - Backend
- SQLite
  - Data Store

Obviously this takes some liberties with the definition of "[Full Stack App](https://www.reddit.com/r/ProgrammerHumor/comments/dzgyf6/fullstack_developer_means/)", for my purposes I take it to mean "a [web application](https://en.wikipedia.org/wiki/Web_application) with a [frontend](https://en.wikipedia.org/wiki/Frontend_and_backend) that receives data from some a [backend](https://en.wikipedia.org/wiki/Frontend_and_backend) and that data is persisted in some [data store](https://en.wikipedia.org/wiki/Data_store)"

For the first swing at this I also went with classic [CRUD Operations](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) that drive requirements for so many Full-Stack applications:

- Create
- Read
- Update
- Delete

### Data Store

Using SQLite is straightforward if you understand how to set up and query other SQL flavors.
(For a more in depth guide on SQL databases, I'd recommend the [SQLModel docs](https://sqlmodel.tiangolo.com/tutorial/create-db-and-table-with-db-browser/) and [Intro to Databases](https://sqlmodel.tiangolo.com/databases/) for a more beginner friednly intro than reading SQLite documentation...)

I say it's straightforward because we don't need to download or run any external database server.
SQLite is a C library that works within an application to store data to disk or memory without an external server.
It will let us connect with a database using just two lines of python!

```python
import sqlite3
connection = sqlite3.connect(':memory:')
```

This gets us a `Connection` object for interacting with an in-memory SQL database!

For the purposes of using it as a more persistant store, it can be configured to write to a local file (conventionally ending with `.db`).

It also defaults to only being accessible by a single thread, so we'll need to turn this off for multiple users hitting the application in the same thread.

```python
connection = sqlite3.connect('notes.db', check_same_thread=False)
```

### Backend

This is all in one file, but the idea of a "[Service](https://en.wikipedia.org/wiki/Service_(systems_architecture))" that provides reading and writing to the data store is useful to keep track of our goals.
This can be captured in a class as a namespace, using staticmethods to indicate they don't need an instance:

```python
class NoteService:
    """Namespace for Database Related Note Operations"""

    @staticmethod        
    def list_all_notes(
        connection: sqlite3.Connection,
    ) -> List[sqlite3.Row]:
        """Returns rows from all notes. Ordered in reverse creation order"""
        read_notes_query = f"""SELECT rowid, created_timestamp, updated_timestamp, username, body
        FROM notes ORDER BY rowid DESC;"""
        note_rows = execute_query(connection, read_notes_query)
        return note_rows
    @staticmethod    
    def create_note(connection: sqlite3.Connection, note: BaseNote) -> None:
        """Create a Note in the database"""
        create_note_query = f"""INSERT into notes(created_timestamp, updated_timestamp, username, body)
    VALUES(:created_timestamp, :updated_timestamp, :username, :body);"""
        execute_query(connection, create_note_query, asdict(note))
    @staticmethod
    def update_note(connection: sqlite3.Connection, note: Note) -> None:
        """Replace a Note in the database"""
        update_note_query = f"""UPDATE notes SET updated_timestamp=:updated_timestamp, username=:username, body=:body WHERE rowid=:rowid;"""
        execute_query(connection, update_note_query, asdict(note))
    @staticmethod
    def delete_note(connection: sqlite3.Connection, note: Note) -> None:
        """Delete a Note in the database"""
        delete_note_query = f"""DELETE from notes WHERE rowid = :rowid;"""
        execute_query(connection, delete_note_query, {"rowid": note.rowid})
```

*NOTE:* You could definitely initialize the class with a connection and not pass it to functions.
Or in another module.
[Or both](https://en.wikipedia.org/wiki/There%27s_more_than_one_way_to_do_it)!

### Frontend

Streamlit provides all the frontend [components](https://docs.streamlit.io/library/api-reference/widgets) we need, supported underneath by [React](https://reactjs.org/) components such as those from [Base Web / UI](https://baseweb.design/).

I chose to use a Selectbox in the Sidebar to act as page navigation.
This organizes things similarly to other Streamlit multi page examples (Such as this awesome [US Data Explorer](https://share.streamlit.io/arup-group/social-data/run.py?page=Data+Explorer) from arup).

The main entrypoint looks like this:

```python

def main() -> None:
    """Main Streamlit App Entry"""
    connection = get_connection(DATABASE_URI)
    init_db(connection)

    st.header(f"The Littlest Fullstack App!")
    render_sidebar(connection)


def render_sidebar(connection: sqlite3.Connection) -> None:
    """Provides Selectbox Drop Down for which view to render"""
    views = {
        "Read Note Feed": render_read,  # Read first for display default
        "Create a Note": render_create,
        "Update a Note": render_update,
        "Delete a Note": render_delete,
        "About": render_about,
    }
    choice = st.sidebar.selectbox("Menu", views.keys())
    render_func = views.get(choice)
    render_func(connection)
```

Each of those `render_xyz` functions will use `st.` functions to display in the main body of the page when it is chosen in the SelectBox / drop down.

This is the `render_read` for example:

```python
def render_note(note: Note) -> None:
    """Show a note with streamlit display functions"""
    st.subheader(f"By {note.username} at {display_timestamp(note.created_timestamp)}")
    st.caption(
        f"Note #{note.rowid} -- Updated at {display_timestamp(note.updated_timestamp)}"
    )
    st.write(note.body)


def render_read(connection: sqlite3.Connection) -> None:
    """Show all of the notes in the database in a feed"""
    st.success("Reading Note Feed")
    note_rows = NoteService.list_all_notes(connection)
    with st.expander("Raw Note Table Data"):
        st.table(note_rows)

    notes = [Note(**row) for row in note_rows]
    for note in notes:
        render_note(note)
```

For more on the forms for Creating, Updating and Deleting, check out the [source code](https://github.com/gerardrbentley/streamlit-fullstack/blob/7443b0d4d2e59e76ceeefb169520a987a720ee6c/app.py#L174) on github.

### Gluing It All Together

- SQLite can run with the Python process, so we're good to deploy it wherever the Streamlit app runs
- Frontend and Backend are in one server, so there's no [HTTP](https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol) or [Websocket](https://en.wikipedia.org/wiki/WebSocket) communication going between App services

Python `dataclasses.dataclass` provides a nice way of modeling simple entities like this Note example.
It lacks all of the features of [`pydantic`](https://pydantic-docs.helpmanual.io/usage/models/) and [`attrs`](https://www.attrs.org/en/stable/why.html), but it does give us a free `__init__` with typed kwargs and the `dataclasses.asdict` method.

After the rows are read from the database, the data is passed into this `dataclass` Note model.
The model provides some level of validation on the data types and a Python object with known attributes for type-hinting and checking.

```python
@dataclass
class BaseNote:
    """Note Entity for Creation / Handling without database ID"""

    created_timestamp: int
    updated_timestamp: int
    username: str
    body: str


@dataclass
class Note(BaseNote):
    """Note Entity to model database entry"""

    rowid: int
```

## Conclusion

That's the basic app!

It's not perfect, in fact there's no error handling or testing or linting of any sort.

Also building things in one file is generally unsustainable, but I wanted to push the limits on this.
One of the great python web frameworks, [bottle](https://bottlepy.org/docs/dev/), is a single (~4000 line) [file](https://github.com/bottlepy/bottle/blob/master/bottle.py)!

But those sorts of things can be addressed after getting something working.
In the next post we'll replace SQLite with Postgres as the Data Store layer.
When doing that, it's my preference to start using Docker, specifically the Docker-Compose tool.
It makes sure things are easy to setup, run, then destroy without worrying about installing things to my user / filesystem directly.