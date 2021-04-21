
Publish on pypa
---------------

Follow the instructions on [this page](https://packaging.python.org/tutorials/packaging-projects).

    $ python setup.py sdist bdist_wheel
    $ twine upload dist/*
                          

Publish on anaconda
-------------------

Follow the instruction on [this page](https://docs.conda.io/projects/conda-build/en/latest/user-guide/tutorials/build-pkgs-skeleton.html).

    $ cd anaconda
    $ conda skeleton pypi treeconfigparser
    $ conda-build --python 3.9 treeconfigparser
    $ anaconda upload /path/to/the/built/package.tar.bz2

