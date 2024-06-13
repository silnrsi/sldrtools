# sldrtools

Tools for manipulating SLDR data

(the various utilities - entry point scripts - are located in lib/sldr/tools)

## Installation steps for Ubuntu or WSL2

You need to install these build dependencies first:

```bash
sudo apt install build-essential python3-dev pkg-config libicu-dev
```

We will use a virtual environment (virtualenv), update the toolchain and build the module and install the scripts inside:

```bash
python3 -m venv venv

source venv/bin/activate

pip install --upgrade pip setuptools setuptools-scm wheel build packaging

pip install .
```

Depending on your needs for any extras like cssutils or numpy (see pyproject.toml file) you can also type:

```bash
pip install .[css]
```

To exit the virtualenv when you are done, type:

```bash
deactivate
```

## Installation steps for Windows

We will use a virtual environment (virtualenv), update the toolchain and build the module and install the scripts inside:

```cmd
python -m venv venv

./venv/Scripts/activate

pip install --upgrade pip setuptools setuptools-scm wheel build packaging

pip install .
```

Depending on your needs for any extras like cssutils or numpy (see pyproject.toml file) you can also type:

```cmd
pip install .[css]
```

To exit the virtualenv when you are done, type:

```cmd
deactivate
```
