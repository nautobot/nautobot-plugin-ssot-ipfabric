# Nautobot SSoT IPFabric

An [SSoT](https://blog.networktocode.com/post/nautobot-ssot-plugin/) plugin providing a simple way to synchronize data between [IPFabric](https://ipfabric.io/) and [Nautobot](https://github.com/nautobot/nautobot). Ensure data stays consistent between the two platforms by leveraging [DiffSync](https://github.com/networktocode/diffsync) capabilities and allowing users to take full advantage of both platforms with up-to-date, synchronized data.

## Version Matrix

Here is a compatibility matrix and the minimum versions required to run this plugin:

| IP Fabric | Python | Nautobot | ssot | ssot-ipfabric | [python-ipfabric](https://github.com/community-fabric/python-ipfabric) | [python-ipfabric-diagrams](https://github.com/community-fabric/python-ipfabric-diagrams) |
|-----------|--------|----------|---------|------------------|------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| 4.4       | 3.7.1  | 1.1.0    | 1.0.1   | 0.10.0            | 0.11.0                                                                 | 1.2.7                                                                                    |
| 5.0.1     | 3.7.1  | 1.2.0    | 1.0.1   | 1.0.0            | 5.0.11                                                                  | 5.0.2                                                                                    |

## Build Status

| Branch      | Status                                                                                                                                              |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **main**    | ![Build Status](https://github.com/nautobot/nautobot-plugin-ssot-ipfabric/actions/workflows/nautobot-ssot-ipfabric-ci.yml/badge.svg?branch=main)    |
| **develop** | ![Build Status](https://github.com/nautobot/nautobot-plugin-ssot-ipfabric/actions/workflows/nautobot-ssot-ipfabric-ci.yml/badge.svg?branch=develop) |

## Documentation

Documentation is hosted with Github Pages at [Nautobot SSoT IP Fabric Documentation](https://nautobot.github.io/nautobot-plugin-ssot-ipfabric/)

## Installation

To install the plugin from Pypi

```shell
pip install nautobot-ssot-ipfabric
```

To install the plugin manually from repository code

```shell
git clone git@github.com:nautobot/nautobot-plugin-ssot-ipfabric.git
```

```bash
cd nautobot-plugin-ssot-ipfabric
```

```shell
pip install .
```

For additional detailed instructions on how to install Nautobot Plugins, checkout the [official documentation](https://nautobot.readthedocs.io/en/latest/plugins/#installing-plugins)

### Environment Variables

This plugin relies on user provided environment variables to interact with IP Fabric.

- `ipfabric_api_token` - API Token for IP Fabric
- `ipfabric_host` - IP Fabric URL
- `nautobot_host` - Nautobot URL (This is used to generate url links for chatops)
- `ipfabric_ssl_verify`- IP Fabric API SSL verification
- `ipfabric_timeout`- IP Fabric API timeout

Example `PLUGINS_CONFIG` to be updated in `nautobot_config.py` after successful installation. The chatops configuration is optional, but if you'd like to have the
ability to call the sync job through chatops, you will be required to configure it.

```python
PLUGINS_CONFIG = {
    "nautobot_chatops": {
        "enable_slack": True,
        "slack_api_token": os.environ.get("SLACK_API_TOKEN"),
        "slack_signing_secret": os.environ.get("SLACK_SIGNING_SECRET"),
        "session_cache_timeout": 3600,
    },
    "nautobot_ssot_ipfabric": {
        "ipfabric_api_token": os.environ.get("IPFABRIC_API_TOKEN"),
        "ipfabric_host": os.environ.get("IPFABRIC_HOST"),
        "nautobot_host": os.environ.get("NAUTOBOT_HOST"),
        "ipfabric_ssl_verify": os.environ.get("IPFABRIC_SSL_VERIFY"),
        "ipfabric_timeout": os.environ.get("IPFABRIC_TIMEOUT"),
    },
    "nautobot_ssot": {"hide_example_jobs": True},
    "nautobot_chatops_ipfabric": {
        "IPFABRIC_API_TOKEN": os.environ.get("IPFABRIC_API_TOKEN"),
        "IPFABRIC_HOST": os.environ.get("IPFABRIC_HOST"),
    },
}
```

## ChatOps

As part of the SSoT synchronization capabilities with IP Fabric, this plugin extends the [Nautobot Plugin Chatops IPFabric](https://github.com/nautobot/nautobot-plugin-chatops-ipfabric) by providing users with the ability to begin the sync job from a chatops command (Slack).

![ssot-chatops-sync](docs/images/chatops-ssot-ipfabric.png)

## Contributing

Pull requests are welcomed and automatically built and tested against multiple versions of Python and multiple version of Nautobot through Github Actions.

The project is packaged with a light development environment based on `docker-compose` to help with the local development of the project and to run the tests within Github Actions.

The project is following Network to Code software development guideline and is leveraging:

- Black, Pylint, Bandit and pydocstyle for Python linting and formatting.
- Django unit test to ensure the plugin is working properly.

### Development Environment

The development environment can be used in 2 ways. First, with a local poetry environment if you wish to develop outside of Docker with the caveat of using external services provided by Docker for PostgresQL and Redis. Second, all services are spun up using Docker and a local mount so you can develop locally, but Nautobot is spun up within the Docker container.

Below is a quick start guide if you're already familiar with the development environment provided, but if you're not familiar, please read the [Getting Started Guide](GETTING_STARTED.md).

#### Invoke

The [PyInvoke](http://www.pyinvoke.org/) library is used to provide some helper commands based on the environment. There are a few configuration parameters which can be passed to PyInvoke to override the default configuration:

- `nautobot_ver`: the version of Nautobot to use as a base for any built docker containers (default: 1.1.4)
- `project_name`: the default docker compose project name (default: nautobot_ssot_ipfabric)
- `python_ver`: the version of Python to use as a base for any built docker containers (default: 3.7)
- `local`: a boolean flag indicating if invoke tasks should be run on the host or inside the docker containers (default: False, commands will be run in docker containers)
- `compose_dir`: the full path to a directory containing the project compose files
- `compose_files`: a list of compose files applied in order (see [Multiple Compose files](https://docs.docker.com/compose/extends/#multiple-compose-files) for more information)

Using **PyInvoke** these configuration options can be overridden using [several methods](http://docs.pyinvoke.org/en/stable/concepts/configuration.html). Perhaps the simplest is simply setting an environment variable `INVOKE_NAUTOBOT_SSOT_IPFABRIC_VARIABLE_NAME` where `VARIABLE_NAME` is the variable you are trying to override. The only exception is `compose_files`, because it is a list it must be overridden in a yaml file. There is an example `invoke.yml` (`invoke.example.yml`) in this directory which can be used as a starting point.

#### Local Poetry Development Environment

1. Copy `development/creds.example.env` to `development/creds.env` (This file will be ignored by Git and Docker)
2. Uncomment the `POSTGRES_HOST`, `REDIS_HOST`, and `NAUTOBOT_ROOT` variables in `development/creds.env`
3. Create an `invoke.yml` file with the following contents at the root of the repo (you can also `cp invoke.example.yml invoke.yml` and edit as necessary):

```yaml
---
nautobot_ssot_ipfabric:
  local: true
  compose_files:
    - "docker-compose.requirements.yml"
```

4. Run the following commands:

```shell
poetry shell
poetry install --extras nautobot
export $(cat development/dev.env | xargs)
export $(cat development/creds.env | xargs)
invoke start && sleep 5
nautobot-server migrate
```

> If you want to develop on the latest develop branch of Nautobot, run the following command: `poetry add --optional git+https://github.com/nautobot/nautobot@develop`. After the `@` symbol must match either a branch or a tag.

4. You can now run nautobot-server commands as you would from the [Nautobot documentation](https://nautobot.readthedocs.io/en/latest/) for example to start the development server:

```shell
nautobot-server runserver 0.0.0.0:8080 --insecure
```

Nautobot server can now be accessed at [http://localhost:8080](http://localhost:8080).

It is typically recommended to launch the Nautobot **runserver** command in a separate shell so you can keep developing and manage the webserver separately.

#### Docker Development Environment

This project is managed by [Python Poetry](https://python-poetry.org/) and has a few requirements to setup your development environment:

1. Install Poetry, see the [Poetry Documentation](https://python-poetry.org/docs/#installation) for your operating system.
2. Install Docker, see the [Docker documentation](https://docs.docker.com/get-docker/) for your operating system.

Once you have Poetry and Docker installed you can run the following commands to install all other development dependencies in an isolated python virtual environment:

```shell
poetry shell
poetry install
invoke start
```

Nautobot server can now be accessed at [http://localhost:8080](http://localhost:8080).

To either stop or destroy the development environment use the following options.

- **invoke stop** - Stop the containers, but keep all underlying systems intact
- **invoke destroy** - Stop and remove all containers, volumes, etc. (This results in data loss due to the volume being deleted)

### CLI Helper Commands

The project is coming with a CLI helper based on [invoke](http://www.pyinvoke.org/) to help setup the development environment. The commands are listed below in 3 categories `dev environment`, `utility` and `testing`.

Each command can be executed with `invoke <command>`. Environment variables `INVOKE_NAUTOBOT_SSOT_IPFABRIC_PYTHON_VER` and `INVOKE_NAUTOBOT_SSOT_IPFABRIC_NAUTOBOT_VER` may be specified to override the default versions. Each command also has its own help `invoke <command> --help`

#### Docker dev environment

```no-highlight
  build            Build all docker images.
  debug            Start Nautobot and its dependencies in debug mode.
  destroy          Destroy all containers and volumes.
  restart          Restart Nautobot and its dependencies.
  start            Start Nautobot and its dependencies in detached mode.
  stop             Stop Nautobot and its dependencies.
```

#### Utility

```no-highlight
  cli              Launch a bash shell inside the running Nautobot container.
  create-user      Create a new user in django (default: admin), will prompt for password.
  makemigrations   Run Make Migration in Django.
  nbshell          Launch a nbshell session.
  shell-plus       Launch a shell_plus session, which uses iPython and automatically imports all models.
```

#### Testing

```no-highlight
  bandit           Run bandit to validate basic static code security analysis.
  black            Run black to check that Python files adhere to its style standards.
  flake8           This will run flake8 for the specified name and Python version.
  pydocstyle       Run pydocstyle to validate docstring formatting adheres to NTC defined standards.
  pylint           Run pylint code analysis.
  tests            Run all tests for this plugin.
  unittest         Run Django unit tests for the plugin.
```

### Project Documentation

Documentation is auto-generated with Sphinx, myst-paerser and sphinx-autoapi. The latest code in the `main` branch is providing the documentation with Github Pages. To build documentation locally as you are developing, perform the following commands.

```shell
sphinx-build -vvv -b html ./docs docs/public
cd docs/public
python -m http.server
```

Now you can access the documentation locally at `http://localhost:8000/` or the IP of the server hosting the development environment.

## Questions

For any questions or comments, please check the [FAQ](FAQ.md) first and feel free to swing by the [Network to Code slack channel](https://networktocode.slack.com/) (channel #networktocode).
Sign up [here](http://slack.networktocode.com/)

## Screenshots

Main SSoT IP Fabric Dashboard
![Dashboard](docs/images/dashboard.png)

Sync Details
![Dashboard](docs/images/sync_details.png)
