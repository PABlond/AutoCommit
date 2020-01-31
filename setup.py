import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="autocommit",  # Replace with your own username
    version="0.0.1",
    author="Pierre-Alexis Blond",
    author_email="pierre-alexis.blond@live.fr",
    description="A script to make commit/push easier",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PABlond/AutoCommit",
    py_modules=['autocommit'],
    entry_points={
        "console_scripts": [
            "autocommit=autocommit:main",
        ],
        "gui_scripts": [
            "autocommit=autocommit:main",
        ]
    },
    zip_safe=True
)
