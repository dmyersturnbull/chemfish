# ChemFish

[![Version status](https://img.shields.io/pypi/status/chemfish)](https://pypi.org/project/chemfish/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/chemfish)](https://pypi.org/project/chemfish/)
[![Docker](https://img.shields.io/docker/v/dmyersturnbull/chemfish?color=green&label=DockerHub)](https://hub.docker.com/repository/docker/dmyersturnbull/chemfish)
[![GitHub release (latest SemVer including pre-releases)](https://img.shields.io/github/v/release/dmyersturnbull/chemfish?include_prereleases&label=GitHub)](https://github.com/dmyersturnbull/chemfish/releases)
[![Latest version on PyPi](https://badge.fury.io/py/chemfish.svg)](https://pypi.org/project/chemfish/)
[![Documentation status](https://readthedocs.org/projects/chemfish/badge/?version=latest&style=flat-square)](https://chemfish.readthedocs.io/en/stable/)
[![Build & test](https://github.com/dmyersturnbull/chemfish/workflows/Build%20&%20test/badge.svg)](https://github.com/dmyersturnbull/chemfish/actions)


**⚠ Please note:**
This is an unfinished fork of Chemfish (Kale) under development.
It is being heavily refactored, and most tests are missing. Do not use it.

To install, first install and configure [MariaDB](https://mariadb.org/).
Then run:

```bash
pip install chemfish
chemfish init
```

The second command will prompt you and configure Chemfish with a new database
or the database from the [OSF repository](https://osf.io/nyhpc/).
[See the docs](https://chemfish.readthedocs.io/en/stable/) for more help.

To build and test locally (with MariaDB installed):

```bash
git clone https://github.com/dmyersturnbull/chemfish.git
cd chemfish
pip install tox
tox
```

The `tox.ini` assumes that the root MariaDB password is `root`. Just modify this line if needed:

```ini
mysql -e 'SOURCE tests/resources/testdb.sql;' --host=127.0.0.1 --user=root --password=root
```

[New issues](https://github.com/dmyersturnbull/chemfish/issues) and pull requests are welcome.
Please refer to the [contributing guide](https://github.com/chemfish/blob/master/CONTRIBUTING.md).
Generated with [Tyrannosaurus](https://github.com/dmyersturnbull/tyrannosaurus).
