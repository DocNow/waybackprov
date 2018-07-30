from setuptools import setup

with open("README.md") as f:
    long_description = f.read()

if __name__ == "__main__":
    setup(
        name='waybackprov',
        version='0.0.7',
        url='https://github.com/edsu/waybackprov',
        author='Ed Summers',
        author_email='ehs@pobox.com',
        py_modules=['waybackprov', ],
        description='Checks the provenance of a URL in the Wayback machine',
        long_description=long_description,
        long_description_content_type="text/markdown",
        python_requires='>=3.0',
        entry_points={'console_scripts': ['waybackprov = waybackprov:main']}
    )
