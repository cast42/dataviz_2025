# INSTALL

## Install tools uv package manager and just task runner

```bash
brew install uv
brew install just
```

## Install Astral typechecker ty globally

```bash
uv tool install ty@latest
```

## Create a new local repo

```bash
uv init --python 3.13 myproj
cd my_proj
git init
git add .
git commit -m "Initial commit"
```

## Create a new project on gihub

Go to [https://github.com/new](https://github.com/new), choose a name (e.g. myproj), description, public/private, and click Create repository.

## Link your local repo to GitHub

```bash
git remote add origin git@github.com:your-username/myproj.git
# or for HTTPS
git remote add origin https://github.com/your-username/myproj.git
```

## Push your code

```bash
git branch -M main
git push -u origin main
```

## Copy my justfile

```bash
curl -L -O https://raw.githubusercontent.com/cast42/dataviz_2025/main/justfile
```

Run the following command

```bash
just install
```

or

```bash
uv sync
```

To lint files, run

```bash
just check
```

To perform type checking, run

```bash
just typing *.py
```

# Marimo notebooks

## Install marimo

```bash
uv add marimo
```

## Run marimo

```bash
uv run marimo edit my_notebook.py
```
