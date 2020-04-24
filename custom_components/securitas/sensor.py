import logging
import voluptuous as vol

from homeassistant.helpers.entity import Entity

import requests

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
)

_LOGGER = logging.getLogger(__name__)

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

    def _do_request(self, request_type, url, payload):
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
        
        #_LOGGER.info('Alarm status ' + str(result.json()[0]['PanelStatus']))

        if result.json()[0]['PanelStatus'] == 1:
            return STATE_ALARM_ARMED_AWAY
        elif result.json()[0]['PanelStatus'] == 2:
            return STATE_ALARM_ARMED_HOME
        else:
            return STATE_ALARM_DISARMED


CONF_NAME = 'name'
CONF_USERNAME = 'username'
CONF_PASSWORD = 'password'

def setup_platform(hass, config, add_devices, discovery_info=None):

    my_name = config.get(CONF_NAME)
    my_username = config.get(CONF_USERNAME)
    my_password = config.get(CONF_PASSWORD)
    add_devices([SecuritasSensor(my_name, my_username, my_password)])

class SecuritasSensor(Entity):

    def __init__(self, name, username, password):
        self._name = name
        self._state = None
        self._icon = 'mdi:lock-open-outline'
        self.client = SecuritasClientAPI(username, password)
        self.update()

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return self._icon

    def update(self):
        self._state = self.client.get_alarm_status()

        if self._state == "On":
            self._icon = 'mdi:lock'
        elif self._state == "Home":
            self._icon = 'mdi:account-lock'
        else:
            self._icon = 'mdi:lock-open-outline'