# lost_crumbs

Notes and How To's breadcrumb trail

## Usage

```shell
# Base serve docs
mkdocs serve

# Convert notebooks to blogs
python ./scripts/convert_notebooks.py

docker-compose exec backend python3 scripts/convert_notebooks.py && python3 scripts/inject_titles.py

```

## Dependencies

Wouldn't be as easy without the following:

- Mkdocs
  - [Mkdocs Material](https://squidfunk.github.io/mkdocs-material/)
  - [Git revision plugin](https://github.com/timvink/mkdocs-git-revision-date-localized-plugin)
  - [Awesome Pages](https://github.com/lukasgeiter/mkdocs-awesome-pages-plugin)

## M1 Mac Homebrew

Social plugin requires cairo, which can be installed via homebrew.

m1 macs save homebrew library files to different location, symlink like so:

```sh
sudo ln -s /opt/homebrew/lib/libcairo.2.dylib /usr/local/lib
```
