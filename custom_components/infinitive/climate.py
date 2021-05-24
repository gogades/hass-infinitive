"""
Infinitive support for Home Assistant.

This component utilizes the Infinitive APIs offered for the
Carrier/Bryant HVAC units that run the Carrier Infinity protocol.

Infinitive Project - https://github.com/Will1604/infinitive
HA Infinitive Component - https://github.com/mww012/ha_customcomponents
"""
import voluptuous as vol
import logging

from voluptuous.schema_builder import _iterate_mapping_candidates

import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_FILENAME,
    CONF_HOST,
    CONF_PORT,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    ATTR_FRIENDLY_NAME,
)
from homeassistant.components.climate import (
    ClimateEntity,
    PLATFORM_SCHEMA,
    ATTR_TEMPERATURE,
)

from homeassistant.components.climate.const import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_CURRENT_HUMIDITY,
    ATTR_FAN_MODE,
    ATTR_FAN_MODES,
    ATTR_HVAC_MODE,
    ATTR_HVAC_MODES,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    HVAC_MODES,
    PRESET_HOME,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
)

_LOGGER = logging.getLogger(__name__)
DOMAIN = "infinitive"
SUPPORT_FLAGS_BASE = SUPPORT_FAN_MODE | SUPPORT_PRESET_MODE
CONF_TEMP_UNITS = "TempUnits"
CONF_TEMP_MIN_SPREAD = "tempminspread"
"""
tempminspread (Temperature Minimum Spread) refers to the minimum allowed
range between high and low temperatures.  For instance, if tempminspread is 4
and the high temp is 72F the low temp can be no warmer than 68F.
"""
ATTR_STAGE = "stage"
ATTR_BLOWER_RPM = "blower_rpm"
ATTR_AIRFLOW_CFM = "airflow_cfm"
ATTR_FAN_MODES = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
FAN_MODE_MAP = {"auto": FAN_AUTO, "low": FAN_LOW, "med": FAN_MEDIUM, "high": FAN_HIGH}
# ATTR_OPERATION_LIST = ['auto', 'cool', 'heat', 'off']
"""
The override duration refers to a deviation from the current schedule.
The HVAC unit has a set schedule that it abides by.  Any manual change
is a deviation from that schedule and results in an override.
Currently there is no way to programmatically set the schedule and requires
a physical thermostat.

The default override time is 120 minutes.
"""
ATTR_OVERRIDE_DURATION = "override_duration"
ATTR_OUTDOOR_TEMP = "outdoor_temp"
ATTR_AUX_HEAT = "aux_heat"
ATTR_HEATPUMP_COIL_TEMP = "heatpump_coil_temp"
ATTR_HEATPUMP_OUTSIDE_TEMP = "heatpump_outside_temp"
ATTR_HEATPUMP_STAGE = "heatpump_stage"
ATTR_TARGET_HUMIDITY = "target_humidity"
PRESET_HOLD = "Hold"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=8080): cv.positive_int,
        vol.Optional(ATTR_FRIENDLY_NAME, default="Infinitive"): cv.string,
        vol.Optional(CONF_TEMP_UNITS, default=TEMP_FAHRENHEIT): cv.string,
        vol.Optional(CONF_TEMP_MIN_SPREAD, default=2): cv.positive_int,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Infinitive climate platform."""
    _LOGGER.debug("importing pyinfinitive")
    import pyinfinitive

    host = config[CONF_HOST]
    port = config[CONF_PORT]
    name = config[ATTR_FRIENDLY_NAME]
    uniqueid = config[CONF_HOST] + ":" + str(config[CONF_PORT])
    temp_units = config[CONF_TEMP_UNITS]
    temp_min_spread = config[CONF_TEMP_MIN_SPREAD]

    inf_device = pyinfinitive.infinitive_device(host, port, temp_units)

    _LOGGER.debug("Adding Infinitive device")
    add_entities([InfinitiveDevice(inf_device, name, temp_min_spread, uniqueid)])


class InfinitiveDevice(ClimateEntity):
    """Representation of an Infinitive Device."""

    def __init__(self, inf_device, name, temp_min_spread, uniqueid):
        """Initialize Infinitive device instance."""
        _LOGGER.debug("Initializing infinitive class instance")
        self._inf_device = inf_device
        self._status = self._inf_device.get_status()
        self._name = name or "Infinitive Thermostat"
        self._support_flags = SUPPORT_FLAGS_BASE
        self._unit_of_measurement = TEMP_FAHRENHEIT
        self._temp_min_spread = temp_min_spread
        self._target_temperature_high = None
        self._target_temperature_low = None
        self._target_temperature = None
        self._target_humidity = None
        self._current_temperature = None
        self._current_humidity = None
        self._blower_rpm = None
        self._fan_mode = None
        self._hvac_mode = None
        self._preset_mode = None
        self._stage = None
        self._override_duration = None
        self._is_on = None
        self._airflow_cfm = None
        self._outdoor_temp = None
        self._aux_heat = None
        self._heatpump_coil_temp = None
        self._heatpump_outside_temp = None
        self._heatpump_stage = None
        self._hvac_action = None
        self._unique_id = uniqueid

        self.update()

    @property
    def supported_features(self):
        """Return list of supported features."""
        if self._hvac_mode == "cool" or self._hvac_mode == "heat":
            self._support_flags = SUPPORT_FLAGS_BASE | SUPPORT_TARGET_TEMPERATURE
            _LOGGER.debug("Support Flags: " + str(self._support_flags))
        else:
            self._support_flags = SUPPORT_FLAGS_BASE | SUPPORT_TARGET_TEMPERATURE_RANGE
            _LOGGER.debug("Support Flags: " + str(self._support_flags))
        return self._support_flags

    @property
    def unique_id(self):
        """Return the unique id of this alarm control panel."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the infinitive device."""
        return self._name

    @property
    def current_temperature(self):
        """Return the current temperature."""
        _LOGGER.debug("Current Temp: " + str(self._current_temperature))
        return self._current_temperature

    @property
    def target_temperature_high(self):
        """Return the target high temp(cool setpoint)."""
        _LOGGER.debug("Target High Temp: " + str(self._target_temperature_high))
        return self._target_temperature_high

    @property
    def target_temperature_low(self):
        """Return the target low temp(heat setpoint)."""
        _LOGGER.debug("Target Low Temp: " + str(self._target_temperature_low))
        return self._target_temperature_low

    @property
    def target_temperature(self):
        """Return the target low temp(heat setpoint)."""
        _LOGGER.debug("Target Temp: " + str(self._target_temperature))
        return self._target_temperature

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        # _LOGGER.debug("Unit of measurement:" +
        #   str(self._unit_of_measurement))
        return self._unit_of_measurement

    @property
    def fan_mode(self):
        """Return the current fan mode."""
        # _LOGGER.debug("Fan Mode: " + str(self._fan_mode))
        return self._fan_mode

    @property
    def fan_modes(self):
        """Return fan mode options."""
        _LOGGER.debug("ATTR_FAN_LIST: " + str(ATTR_FAN_MODES))
        return ATTR_FAN_MODES

    # @property
    # def operation_list(self):
    #     """Return operation mode options."""
    #     # _LOGGER.debug("ATTR_OPERATION_LIST: " + str(ATTR_OPERATION_LIST))
    #     return ATTR_OPERATION_LIST

    @property
    def preset_mode(self):
        """Return current preset mode."""
        if self._status["hold"] is True:
            return PRESET_HOLD
        else:
            return PRESET_HOME

    @property
    def preset_modes(self):
        """Return supported preset modes."""
        _LOGGER.debug("Preset Mode: " + str(self.preset_mode))
        return [PRESET_HOME, PRESET_HOLD]

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_CURRENT_HUMIDITY: self._current_humidity,
            ATTR_TARGET_HUMIDITY: self._target_humidity,
            ATTR_BLOWER_RPM: self._blower_rpm,
            ATTR_STAGE: self._stage,
            ATTR_OVERRIDE_DURATION: self._override_duration,
            ATTR_AIRFLOW_CFM: self._airflow_cfm,
            ATTR_OUTDOOR_TEMP: self._outdoor_temp,
            ATTR_AUX_HEAT: self._aux_heat,
            ATTR_HEATPUMP_COIL_TEMP: self._heatpump_coil_temp,
            ATTR_HEATPUMP_OUTSIDE_TEMP: self._heatpump_outside_temp,
            ATTR_HEATPUMP_STAGE: self._heatpump_stage,
        }

    @property
    def hvac_mode(self):
        """Return current hvac mode."""
        _LOGGER.debug("Getting HVAC Mode: " + str(self._status["mode"]))
        if self._status["mode"] == "cool":
            return HVAC_MODES[2]
        elif self._status["mode"] == "heat":
            return HVAC_MODES[1]
        elif self._status["mode"] == "auto":
            return HVAC_MODES[3]

    @property
    def hvac_modes(self):
        """Return supported HVAC modes (heat, cool, heat_cool)."""
        return [HVAC_MODES[1], HVAC_MODES[2], HVAC_MODES[3]]

    @property
    def hvac_action(self):
        """Return current HVAC action."""
        return self._hvac_action

    def update(self):
        """Update current status from infinitive device."""
        _LOGGER.debug("Updating Infinitive status")
        status = self._inf_device.get_status()
        if "mode" in status.keys():
            self._status = status
        try:
            self._hvac_mode = self._status["mode"]
            self._target_temperature_high = self._status["coolSetpoint"]
            self._target_temperature_low = self._status["heatSetpoint"]
            if self._hvac_mode == "cool":
                self._target_temperature = self._target_temperature_high
            elif self._hvac_mode == "heat":
                self._target_temperature = self._target_temperature_low
            self._target_humidity = self._status["targetHumidity"]
            self._current_temperature = self._status["currentTemp"]
            self._current_humidity = self._status["currentHumidity"]
            self._blower_rpm = self._status["blowerRPM"]
            self._fan_mode = FAN_MODE_MAP[self._status["fanMode"]]
            if self._status["hold"] is True:
                self._preset_mode == PRESET_HOLD
            else:
                self._preset_mode == PRESET_HOME
            self._stage = self._status["stage"]
            self._override_duration = self._status["holdDurationMins"]
            self._airflow_cfm = self._status["airFlowCFM"]
            self._outdoor_temp = self._status["outdoorTemp"]
            self._aux_heat = self._status["auxHeat"]
            self._heatpump_coil_temp = self._status["heatpump_coilTemp"]
            self._heatpump_outside_temp = self._status["heatpump_outsideTemp"]
            self._heatpump_stage = self._status["heatpump_stage"]
            if self._hvac_mode == "cool" and self._stage > 0:
                self._hvac_action = CURRENT_HVAC_COOL
            elif self._hvac_mode == "heat" and self._stage > 0:
                self._hvac_action = CURRENT_HVAC_HEAT
            else:
                self._hvac_action = CURRENT_HVAC_IDLE
        except Exception as e:
            _LOGGER.debug(f"Status update error: {e}")

    def _set_temperature_high(self, cool_setpoint):
        """Set new coolpoint target temperature."""
        _LOGGER.debug("Setting High Temp :" + str(cool_setpoint))
        self._inf_device.set_temp(int(cool_setpoint), "cool")

    def _set_temperature_low(self, heat_setpoint):
        """Set new heatpoint target temperature."""
        _LOGGER.debug("Setting Low Temp :" + str(heat_setpoint))
        self._inf_device.set_temp(int(heat_setpoint), "heat")

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        _LOGGER.debug("TempMinSpread: " + str(self._temp_min_spread))
        if self._hvac_mode == "auto":
            temperature_high = kwargs.get(ATTR_TARGET_TEMP_HIGH)
            temperature_low = kwargs.get(ATTR_TARGET_TEMP_LOW)
            if temperature_high - temperature_low < self._temp_min_spread:
                temperature_low = temperature_high - self._temp_min_spread
            self._set_temperature_high(temperature_high)
            self._set_temperature_low(temperature_low)
            _LOGGER.debug(
                "Setting new target temperature: "
                + str(temperature_high)
                + " "
                + str(temperature_low)
            )
        else:
            temperature = kwargs.get(ATTR_TEMPERATURE)
            if self._hvac_mode == "cool":
                self._set_temperature_high(temperature)
            elif self._hvac_mode == "heat":
                self._set_temperature_low(temperature)
            _LOGGER.debug("Setting new target temperature: " + str(temperature))

    def set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        _LOGGER.debug("Setting fan mode: " + str(fan_mode))
        if fan_mode is None:
            return
        if fan_mode == FAN_MEDIUM:
            self._inf_device.set_fanmode("med")
        else:
            self._inf_device.set_fanmode(fan_mode)

    def set_hvac_mode(self, hvac_mode):
        """Set new operation mode."""
        _LOGGER.debug("Setting HVAC mode: " + str(hvac_mode))
        if hvac_mode is None:
            return
        elif hvac_mode == HVAC_MODES[3]:
            self._inf_device.set_mode("auto")
            self._support_flags = SUPPORT_FLAGS_BASE | SUPPORT_TARGET_TEMPERATURE_RANGE
        else:
            self._inf_device.set_mode(hvac_mode)
            self._support_flags = SUPPORT_FLAGS_BASE | SUPPORT_TARGET_TEMPERATURE

    def set_preset_mode(self, mode):
        """Set new preset mode."""
        if mode == "hold":
            self._inf_device.set_hold(True)
        elif mode == "home":
            self._inf_device.set_hold(False)
