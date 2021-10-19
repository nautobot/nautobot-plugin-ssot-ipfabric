# Nautobot SSoT Plugin - IPFabric

This plugin was created to allow users to sync data from IP Fabric into Nautobot.

## Overview

Currently this plugin will provide the ability to sync the following IP Fabric models into Nautobot.

- Site -> Nautobot Site
- Device -> Nautobot Device
- Part Numbers -> Nautobot Manufacturer/Device Type/Platform
- Interfaces -> Nautobot Device Interfaces

## Installation & Configuration

The plugin is available as a Python package in pypi and can be installed with pip

```shell
pip install nautobot-ssot-ipfabric
```

> The plugin is compatible with Nautobot 1.1.0 and higher

To ensure Nautobot SSoT IPFabric is automatically re-installed during future upgrades, create a file named `local_requirements.txt` (if not already existing) in the Nautobot root directory (alongside `requirements.txt`) and list the `nautobot-ssot-ipfabric` package:

```no-highlight
# echo nautobot-ssot-ipfabric >> local_requirements.txt
```

Once installed, the plugin needs to be enabled in your `nautobot_config.py`

```python
# In your nautobot_config.py
PLUGINS = ["nautobot_ssot_ipfabric"]

# PLUGINS_CONFIG = {
#   "nautobot_ssot_ipfabric": {
#     ADD YOUR SETTINGS HERE
#   }
# }
```

Currently, there are no further settings that need to be configured within `nautobot_config.py` for the plugin to work.

## Usage

## API

## DiffSync Models

### IPFabric Site

### IPFabric Device
