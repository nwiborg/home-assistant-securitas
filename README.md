# home-assistant-securitas
A custom component for Home Assistant for Securitas Home Alarm

The platform contains:
* Switch for arming Securitas Home Alarm in Away Mode
* Switch for arming Home mode
* Sensor to detect the status of the Home Alarm

### Legal Disclaimer
This software is not affiliated with Securitas and the developers take no legal responsibility for the functionality or security of your Securitas Alarms and devices.

# Installation

* Install repository through HACS

- OR -

* Create a "custom_components" folder where the configuration.yaml file is located, and sub folders equivalent to the structure in this repository.

* Update your configuration.yaml file according to the example file provided.
* Restart home assistant

# Example configuration.yaml

```yaml
securitas:
    # Name for components
    name: "Home Alarm"
    # Username - your username to Securitas
    username: !secret securitas_user
    # Password - your password to Securitas
    password: !secret securitas_pw
``