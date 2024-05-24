# Description

Simple Python Script to enter bike rides in the "Mit dem Rad zur Arbeit (MdRzA)" portal.

# Usage

## Create a new virtual environment

First, create a new virtual environment using `virtualenv`. If you haven't installed `virtualenv` yet, you can do so with pip:

```bash
pip install virtualenv
```

Then, create a new virtual environment. For example:

```bash
virtualenv mdrza
```

Enable the virtual environment:
```bash
.\mdrza\Scripts\activate
```

## Install dependencies

Next, install the required dependencies using pip:

```bash
pip install -r requirements.txt
```

## Create .env file

Create a `.env` file using the provided example. Modify the ENCRYPTION_KEY as needed for your application.

Example `.env` file:
```makefile
ENCRYPTION_KEY=YourSecretKeyHere
```

## Test it!

Finally, test your setup to ensure everything is working as expected.

```bash
python synchronize_mdrza.py
```