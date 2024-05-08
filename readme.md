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

## Create launch.json for VS Code

Create a `launch.json` file in the `.vscode` directory for Visual Studio Code debugging. You can use the following example:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python Debugger: Current File",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "args": ["--username", "florian.deutsch@linkfish.eu", "--encrypted_password", "/zCWZNwyfIvYqBFxVKuC7w==", "--day", "2024-05-07", "--kilometers", "8"]
        }
    ]
}
```

Make sure to replace the args as needed.
`encrypted_password` is a blowfish encrypted string. Get an encrypted string using the `BlowfishEncryption.encrypt_text` function.

## Test it!

Finally, test your setup to ensure everything is working as expected.
