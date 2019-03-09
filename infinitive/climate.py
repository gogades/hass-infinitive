import voluptuous as vol
import logging

from homeassistant.const import CONF_FILENAME, CONF_HOST, CONF_PORT, \
    TEMP_CELSIUS, TEMP_FAHRENHEIT, TEMPERATURE, ATTR_FRIENDLY_NAME
from . import ClimateDevice, PLATFORM_SCHEMA, \
    STATE_AUTO, STATE_COOL, STATE_HEAT, ATTR_CURRENT_TEMPERATURE, \
    ATTR_CURRENT_HUMIDITY, ATTR_HOLD_MODE, ATTR_FAN_MODE, ATTR_FAN_LIST, \
    ATTR_OPERATION_MODE, ATTR_TEMPERATURE, ATTR_TARGET_TEMP_HIGH, \
    ATTR_TARGET_TEMP_LOW, SUPPORT_TARGET_TEMPERATURE, \
    SUPPORT_TARGET_TEMPERATURE_HIGH, SUPPORT_TARGET_TEMPERATURE_LOW, \
    SUPPORT_FAN_MODE, SUPPORT_OPERATION_MODE, ATTR_OPERATION_LIST, \
    ATTR_HOLD_MODE, SUPPORT_HOLD_MODE
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['pyinfinitive']

_LOGGER = logging.getLogger(__name__)
DOMAIN = "infinitive"
SUPPORT_FLAGS = SUPPORT_FAN_MODE | \
    SUPPORT_OPERATION_MODE | SUPPORT_HOLD_MODE

CONF_TEMP_UNITS = 'TempUnits'
CONF_TEMP_MIN_SPREAD = 'tempminspread'
"""
tempminspread (Temperature Minimum Spread) refers to the minimum allowed
range between high and low temperatures.  For instance, if tempminspread is 4
and the high temp is 72F the low temp can be no warmer than 68F.
"""
ATTR_STAGE = 'stage'
ATTR_BLOWER_RPM = 'blower_rpm'
ATTR_AIRFLOW_CFM = 'arflow_cfm'
ATTR_FAN_LIST = ['auto', 'low', 'med', 'high']
ATTR_OPERATION_LIST = ['auto', 'cool', 'heat']
"""
The override duration refers to a deviation from the current schedule.
The HVAC unit has a set schedule that it abides by.  Any manual change
is a deviation from that schedule and results in an override.
Currently there is no way to programmatically set the schedule and requires
a physical thermostat.

The default override time is 120 minutes.
"""
ATTR_OVERRIDE_DURATION = 'override_duration'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_PORT, default=8080): cv.positive_int,
    vol.Optional(ATTR_FRIENDLY_NAME): cv.string,
    vol.Optional(CONF_TEMP_UNITS, default=TEMP_FAHRENHEIT): cv.string,
    vol.Optional(CONF_TEMP_MIN_SPREAD, default=2): cv.positive_int
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Infinitive climate platform."""
    _LOGGER.debug("importing pyinfinitive")
    import pyinfinitive

    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)
    name = config.get(ATTR_FRIENDLY_NAME)
    temp_units = config.get(CONF_TEMP_UNITS)
    temp_min_spread = config.get(CONF_TEMP_MIN_SPREAD)

    inf_device = pyinfinitive.infinitive_device(
        host,
        port,
        temp_units)

    _LOGGER.debug("Adding Infinitive device")
    add_entities([InfinitiveDevice(inf_device, name, temp_min_spread)])


class InfinitiveDevice(ClimateDevice):
    """Representation of an Infinitive Device."""

    def __init__(self, inf_device, name, temp_min_spread):
        """Initialize Infinitive device instance."""
        self._inf_device = inf_device
        self._status = self._inf_device.get_status()
        self._name = name
        self._support_flags = SUPPORT_FLAGS
        self._unit_of_measurement = TEMP_FAHRENHEIT
        self._temp_min_spread = temp_min_spread
        self._target_temperature = None
        self._target_temperature_high = None
        self._target_temperature_low = None
        self._current_temperature = None
        self._current_humidity = None
        self._blower_rpm = None
        self._fan_mode = None
        self._operation_mode = None
        self._stage = None
        self._override_duration = None
        self._is_on = None
        self._hold_mode = None
        self._airflow_cfm = None
        self.update()

    @property
    def supported_features(self):
        """Return list of supported features."""
        # _LOGGER.debug("Support Flags: " + str(SUPPORT_FLAGS))
        if self._operation_mode == 'cool' or self._operation_mode == 'heat':
            self._support_flags = self._support_flags | \
                SUPPORT_TARGET_TEMPERATURE
        else:
            self._support_flags = self._support_flags | \
                SUPPORT_TARGET_TEMPERATURE_HIGH | \
                SUPPORT_TARGET_TEMPERATURE_LOW
        return self._support_flags

    @property
    def name(self):
        """Return the name of the infinitive device."""
        return self._name

    @property
    def current_temperature(self):
        """Return the current temperature."""
        # _LOGGER.debug("Current Temp: " + str(self._current_temperature))
        return self._current_temperature

    @property
    def target_temperature_high(self):
        """Return the target high temp(cool setpoint)."""
        # _LOGGER.debug("Target High Temp: " +
        #               str(self._target_temperature_high))
        return self._target_temperature_high

    @property
    def target_temperature_low(self):
        """Return the target low temp(heat setpoint)."""
        # _LOGGER.debug("Target Low Temp: " +
        #               str(self._target_temperature_low))
        return self._target_temperature_low

    @property
    def target_temperature(self):
        """Return the target temp based on operation mode."""
        _LOGGER.debug("Target Temp: " +
                      str(self._target_temperature))
        return self._target_temperature

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        # _LOGGER.debug("Unit of measurement:" +
        # str(self._unit_of_measurement))
        return self._unit_of_measurement

    @property
    def current_fan_mode(self):
        """Return the current fan mode."""
        # _LOGGER.debug("Fan Mode: " + str(self._fan_mode))
        return self._fan_mode

    @property
    def fan_list(self):
        """Return fan mode options."""
        # _LOGGER.debug("ATTR_FAN_LIST: " + str(ATTR_FAN_LIST))
        return ATTR_FAN_LIST

    @property
    def current_operation(self):
        """Return current oprating mode."""
        # _LOGGER.debug("Operation mode: " + str(self._operation_mode))
        return self._operation_mode

    @property
    def operation_list(self):
        """Return operation mode options."""
        # _LOGGER.debug("ATTR_FAN_LIST: " + str(ATTR_OPERATION_LIST))
        return ATTR_OPERATION_LIST

    @property
    def current_hold_mode(self):
        """Return current hold mode status."""
        # _LOGGER.debug("Hold Mode: " + str(self._hold_mode))
        return self._hold_mode

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_CURRENT_HUMIDITY: self._current_humidity,
            ATTR_BLOWER_RPM: self._blower_rpm,
            ATTR_STAGE: self._stage,
            ATTR_OVERRIDE_DURATION: self._override_duration,
            ATTR_AIRFLOW_CFM: self._airflow_cfm
        }

    def update(self):
        """Update current status from infinitive device."""
        _LOGGER.debug("Updating Infinitive status")
        self._status = self._inf_device.get_status()
        self._operation_mode = self._status['mode']
        self._target_temperature_high = self._status['coolSetpoint']
        self._target_temperature_low = self._status['heatSetpoint']
        if self._operation_mode == 'cool':
            self._target_temperature = self._target_temperature_high
        elif self._operation_mode == 'heat':
            self._target_temperature = self._target_temperature_low
        self._current_temperature = self._status['currentTemp']
        self._current_humidity = self._status['currentHumidity']
        self._blower_rpm = self._status['blowerRPM']
        self._fan_mode = self._status['fanMode']
        self._stage = self._status['stage']
        self._override_duration = self._status['holdDurationMins']
        self._hold_mode = self._status['hold']
        self._airflow_cfm = self._status['airFlowCFM']
        # _LOGGER.debug(self._status)

    def _set_temperature_high(self, cool_setpoint):
        """Set new coolpoint target temperature."""
        _LOGGER.debug("Setting High Temp :" + str(cool_setpoint))
        self._inf_device.set_temp(int(cool_setpoint), 'cool')

    def _set_temperature_low(self, heat_setpoint):
        """Set new heatpoint target temperature."""
        _LOGGER.debug("Setting Low Temp :" + str(heat_setpoint))
        self._inf_device.set_temp(int(heat_setpoint), 'heat')

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        _LOGGER.debug("TempMinSpread: " + str(self._temp_min_spread))
        _LOGGER.debug("Setting new target temperature: " +
                      str(kwargs.get(ATTR_TARGET_TEMP_HIGH)) + ", " +
                      str(kwargs.get(ATTR_TARGET_TEMP_LOW)) + ", " +
                      str(kwargs.get(ATTR_TEMPERATURE))
                      )
        temperature_high = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        temperature_low = kwargs.get(ATTR_TARGET_TEMP_LOW)
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature_high is not None and temperature_low is not None:
            if self._operation_mode == 'auto':
                if temperature_high - temperature_low < self._temp_min_spread:
                    temperature_low = temperature_high - self._temp_min_spread
                self._set_temperature_high(temperature_high)
                self._set_temperature_low(temperature_low)
        elif temperature is not None:
            if self._operation_mode == 'cool':
                self._set_temperature_high(temperature)
            elif self._operation_mode == 'heat':
                self._set_temperature_low(temperature)
        _LOGGER.debug("Setting new target temperature: " +
                      str(kwargs.get(ATTR_TARGET_TEMP_HIGH)) + ", " +
                      str(kwargs.get(ATTR_TARGET_TEMP_LOW)) + ", " +
                      str(kwargs.get(ATTR_TEMPERATURE))
                      )

    def set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        _LOGGER.debug("Setting fan mode: " + str(fan_mode))
        if fan_mode is None:
            return
        self._inf_device.set_fanmode(fan_mode)

    def set_operation_mode(self, operation_mode):
        """Set new operation mode."""
        _LOGGER.debug("Setting operation mode: " + str(operation_mode))
        if operation_mode is None:
            return
        self._inf_device.set_mode(operation_mode)

    def set_hold_mode(self, hold_mode):
        """Set hold mode."""
        _LOGGER.debug("Setting hold mode: " + str(hold_mode))
        if hold_mode is None:
            return
        self._inf_device.set_hold(hold_mode)
