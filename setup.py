import setuptools

with open("requirements.txt") as reqs:
    install_requires = reqs.read().splitlines()

try:
    long_desc = open("README.md").read()
except IOError:
    long_desc = "Failed to read README.md"

setuptools.setup(
    name="maunium-stickerpicker",
    version="0.1.0",
    url="https://github.com/maunium/stickerpicker",

    author="Tulir Asokan",
    author_email="tulir@maunium.net",

    description="A fast and simple Matrix sticker picker widget",
    long_description=long_desc,
    long_description_content_type="text/markdown",

    packages=setuptools.find_packages(),

    install_requires=install_requires,
    python_requires="~=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Framework :: AsyncIO",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    entry_points={"console_scripts": [
        "sticker-import=sticker.import:cmd",
        "sticker-pack=sticker.pack:cmd",
    ]},
)
