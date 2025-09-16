# INSTALL

## Install tools

```bash
brew install uv
brew install just
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

## Copy my justfille

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
