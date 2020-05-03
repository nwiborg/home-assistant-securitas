"""
Securitas platform that offers a control over alarm status.
"""
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

#from homeassistant.util import convert
from homeassistant.const import (STATE_OFF, STATE_ON, CONF_SWITCHES)
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, CONF_RESOURCES, CONF_NAME, CONF_SCAN_INTERVAL)
from homeassistant.helpers import discovery

import requests
import time

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'securitas'

# COMPONENTS = {
#     'sensor': 'sensor',
#     'switch': 'switch',
# }

# RESOURCES = [
#     'armed_state',
#     'armed_away',
#     'armed_home',
# ]

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        #vol.Optional(CONF_NAME, default={}): vol.Schema(
        #    {cv.slug: cv.string}),
        #vol.Optional(CONF_RESOURCES): vol.All(
        #    cv.ensure_list, [vol.In(RESOURCES)])
        vol.Optional(CONF_NAME, default="Home Alarm"): cv.string
    }),
}, extra=vol.ALLOW_EXTRA)

def setup(hass, config):

    username = config[DOMAIN].get(CONF_USERNAME)
    password = config[DOMAIN].get(CONF_PASSWORD)
    name = config[DOMAIN].get(CONF_NAME)

    client = SecuritasClientAPI(username, password)
	
    hass.data[DOMAIN] = {
        'client': client,
        'name': name
    }
    hass.helpers.discovery.load_platform('sensor', DOMAIN, {}, config)
    hass.helpers.discovery.load_platform('switch', DOMAIN, {}, config)

    return True

class SecuritasClientAPI(object):

    def __init__(self, username, password):
        self._base_url = 'https://sasswapi.intamac.com/service.svc/users/' + username + '/properties'
        self._headers = {
            'x-partnerkey': "5EC6313F-4E7A-4F68-B3ED-394A61126F11",
            'content-type': "text/xml",
            'cache-control': "no-cache"
            }
        self._username = username
        self._password = password
        self._property_id = 0
        self._panel_type = ''
        self._state = self.get_alarm_status()

    def _do_request(self, request_type, url, payload):
        #_LOGGER.debug("Securitas performing request: %s", payload)
        return requests.request(request_type, url, headers=self._headers, data=payload, auth=(self._username, self._password))

    def _set_property_id(self):
        url = self._base_url + '?format=json'
        result = self._do_request("GET", url, '')
        self._property_id = result.json()[0]['PropertyID']

    def _set_panel_type(self):

        if self._property_id == 0:
            self._set_property_id()

        url = self._base_url + '/' + self._property_id + '/devices/alarmpanels?format=json'
        result = self._do_request("GET", url, '')
        self._panel_type = result.json()[0]['__type']
        
    def get_alarm_status(self):

        if self._property_id == 0:
            self._set_property_id()

        url = self._base_url + '/' + self._property_id + '/devices/alarmpanels?format=json'
        result = self._do_request("GET", url, '')

        self._panel_type = result.json()[0]['__type']

        if result.json()[0]['PanelStatus'] == 1:
            return STATE_ALARM_ARMED_AWAY
        elif result.json()[0]['PanelStatus'] == 2:
            return STATE_ALARM_ARMED_HOME
        else:
            return STATE_ALARM_DISARMED

    def set_alarm_status(self, action):

        _LOGGER.debug("Setting Securitas alarm panel to %s", action)
        
        if action == STATE_ALARM_ARMED_AWAY:
            status_name = "ArmedAway"
        elif action == STATE_ALARM_ARMED_HOME:
            status_name = "ArmedHome"
        else:
            status_name = "Disarmed"

        if len(self._panel_type) == 0:
            self._set_panel_type()

        url = self._base_url + '/' + self._property_id + '/devices/alarmpanel'
        payload = "<?xml version='1.0' encoding='utf-8'?><AlarmPanel xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xsd='http://www.w3.org/2001/XMLSchema' xsi:type='" + self._panel_type + "'><PanelStatus>" + status_name + "</PanelStatus></AlarmPanel>"
        self._do_request("PUT", url, payload)
        self._state = STATE_ALARM_PENDING
        return

    @property
    def state(self):
        """Return the state of the device."""
        return self._state
