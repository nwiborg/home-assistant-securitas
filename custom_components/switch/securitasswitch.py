"""
Securitas platform that offers a control over alarm status.
"""
import logging
import voluptuous as vol

from homeassistant.util import convert
from homeassistant.components.switch import (SwitchDevice)
from homeassistant.const import (STATE_OFF, STATE_ON, CONF_NAME, CONF_SWITCHES)

import requests
import json

_LOGGER = logging.getLogger(__name__)

class SecuritasClientAPI(object):

    def __init__(self, username, password):
        self._base_url = 'https://' + username + ':' + password + '@sasswapi.intamac.com/service.svc/users/' + username + '/properties'
        self._headers = {
            'x-partnerkey': "5EC6313F-4E7A-4F68-B3ED-394A61126F11",
            'content-type': "text/xml",
            'cache-control': "no-cache"
            }
        self._property_id = 0
        self._panel_type = ''

    def _set_property_id(self):
        url = self._base_url + '?format=json'
        result = requests.request("GET", url, headers=self._headers)
        self._property_id = result.json()[0]['PropertyID']

    def _set_panel_type(self):

        if self._property_id == 0:
            self._set_property_id()

        url = self._base_url + '/' + self._property_id + '/devices/alarmpanels?format=json'
        result = requests.request("GET", url, headers=self._headers)
        self._panel_type = result.json()[0]['__type']
        
    def get_alarm_status(self):

        if self._property_id == 0:
            self._set_property_id()

        url = self._base_url + '/' + self._property_id + '/devices/alarmpanels?format=json'
        result = requests.request("GET", url, headers=self._headers)
        self._panel_type = result.json()[0]['__type']

        if result.json()[0]['PanelStatus'] == 1:
            return True
        else:
            return False

    def set_alarm_status(self, action):
        
        if action == 1:
            status_name = "ArmedAway"
        else:
            status_name = "Disarmed"

        if len(self._panel_type) == 0:
            self._set_panel_type

        url = self._base_url + '/' + self._property_id + '/devices/alarmpanel'
        payload = "<?xml version='1.0' encoding='utf-8'?><AlarmPanel xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xsd='http://www.w3.org/2001/XMLSchema' xsi:type='" + self._panel_type + "'><PanelStatus>" + status_name + "</PanelStatus></AlarmPanel>"
        requests.request("PUT", url, data=payload, headers=self._headers)
        return


""" key's expected from user configuration"""
CONF_NAME = 'name'
CONF_USERNAME = 'username'
CONF_PASSWORD = 'password'

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Find and return Sensibo data"""
    my_name = config.get(CONF_NAME)
    my_username = config.get(CONF_USERNAME)
    my_password = config.get(CONF_PASSWORD)
    add_devices([SecuritasSwitch(my_name, my_username, my_password)])


class SecuritasSwitch(SwitchDevice):

    def __init__(self, name, username, password):
        _LOGGER.info("Initialized Securitas SWITCH %s", name)
        self._name = name
        self._armed = False
        self.client = SecuritasClientAPI(username, password)
        self.update()

    def turn_on(self, **kwargs):
        """Turn device on."""
        _LOGGER.debug("Update Securitas SWITCH to on")
        self.client.set_alarm_status(1)
        self._armed = True
        

    def turn_off(self, **kwargs):
        """Turn device off."""
        _LOGGER.debug("Update Securitas SWITCH to off")
        self.client.set_alarm_status(0)
        self._armed = False

    def update(self):
        self._armed = self.client.get_alarm_status()

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._armed

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def should_poll(self):
        """Polling is needed."""
        return True