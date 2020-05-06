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
    STATE_ALARM_PENDING
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'securitas'

# COMPONENTS = {
#     'sensor': 'sensor',
#     'switch': 'switch',
# }

# RESOURCES = [
#     'armed_state_sensor',
#     'armed_away_switch',
#     'armed_home_switch',
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
    hass.helpers.discovery.load_platform('alarm_control_panel', DOMAIN, {}, config)

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
        self._last_updated = 0
        self._panel_type = ''
        self._target_state = STATE_ALARM_DISARMED
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
            self._state = STATE_ALARM_ARMED_AWAY
        elif result.json()[0]['PanelStatus'] == 2:
            self._state = STATE_ALARM_ARMED_HOME
        else:
            self._state = STATE_ALARM_DISARMED

        _LOGGER.debug("Get Securitas alarm state: %s", self._state)
        _LOGGER.debug("Target Securitas alarm state: %s", self._target_state)
        
        if self._state == self._target_state:
        	return self._state
        else:
        	return STATE_ALARM_PENDING

    def set_alarm_status(self, action):

        _LOGGER.debug("Setting Securitas alarm panel to %s", action)
        
        self._last_updated = time.time()

        self._target_state = action
        self._state = STATE_ALARM_PENDING

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
        return

    def update(self):
        _LOGGER.debug("Updated Securitas %s", self._name)
        diff = time.time() - self._last_updated
        
        if diff > 15:
            self.get_alarm_status()
            """
            if self.state == STATE_ALARM_ARMED_AWAY:
                self._set_as_armed_away()
            elif self.state == STATE_ALARM_ARMED_HOME:
                self._set_as_armed_home()
            else:
                self._set_as_disarmed()
			"""

	
    
    @property
    def target_state(self):
        return self._target_state

    """
    @state.setter
    def state(self, s):
    	#save prev state when state is changed
    	_LOGGER.debug("Changing Securitas alarm panel state to %s", s)
    	if self._prev_state != s:
        	_LOGGER.debug("Saving Securitas prev state as %s", self._state)
        	self._prev_state = self._state
        self._state = s
    """