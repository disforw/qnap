"""Config flow to configure qnap component."""
import logging

from qnapstats import QNAPStats
from requests.exceptions import ConnectTimeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import dhcp
from homeassistant.components.persistent_notification import create as notify_create
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.helpers import config_validation as cv

from .const import DEFAULT_PORT, DEFAULT_TIMEOUT, DOMAIN

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SSL, default=False): cv.boolean,
        vol.Optional(CONF_VERIFY_SSL, default=True): cv.boolean,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    }
)

_LOGGER = logging.getLogger(__name__)


class QnapConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Qnap configuration flow."""

    _discovered_mac: str | None = None
    _discovered_url: str | None = None
    
    VERSION = 1

    def __init__(self):
        """Initialize."""
        self.is_imported = False

    async def async_step_import(self, import_info):
        """Set the config entry up from yaml."""
        self.is_imported = True
        return await self.async_step_user(import_info)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            protocol = "https" if user_input.get(CONF_SSL, False) else "http"
            api = QNAPStats(
                host=f"{protocol}://{host}",
                port=user_input.get(CONF_PORT, DEFAULT_PORT),
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                verify_ssl=user_input.get(CONF_VERIFY_SSL, True),
                timeout=DEFAULT_TIMEOUT,
            )
            try:
                stats = await self.hass.async_add_executor_job(api.get_system_stats)
            except ConnectTimeout:
                errors["base"] = "cannot_connect"
            except TypeError:
                errors["base"] = "invalid_auth"
            except Exception as error:  # pylint: disable=broad-except
                _LOGGER.error(error)
                errors["base"] = "unknown"
            else:
                unique_id = stats["system"]["serial_number"]
                await self.async_set_unique_id(unique_id, raise_on_progress=False)
                self._abort_if_unique_id_configured()
                title = stats["system"]["name"].capitalize()
                if self.is_imported:
                    _LOGGER.warning(
                        "The import of the QNAP configuration was successful. \
                        Please remove the platform from the YAML configuration file"
                    )
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
    
    async def async_step_dhcp(self, discovery_info: dhcp.DhcpServiceInfo) -> FlowResult:
        """Handle DHCP discovery."""
        self._discovered_url = f"http://{discovery_info.ip}"
        self._discovered_mac = discovery_info.macaddress

        _LOGGER.debug("DHCP discovery detected QNAP: %s", self._discovered_mac)

        mac = format_mac(self._discovered_mac)
        options = ConnectionOptions(self._discovered_url, "", "")
        qsw = QnapQswApi(aiohttp_client.async_get_clientsession(self.hass), options)

        try:
            await qsw.get_live()
        except QswError as err:
            raise AbortFlow("cannot_connect") from err

        await self.async_set_unique_id(format_mac(mac))
        self._abort_if_unique_id_configured()

        return await self.async_step_discovered_connection()

    async def async_step_discovered_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        errors = {}
        assert self._discovered_url is not None

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            qsw = QnapQswApi(
                aiohttp_client.async_get_clientsession(self.hass),
                ConnectionOptions(self._discovered_url, username, password),
            )

            try:
                system_board = await qsw.validate()
            except LoginError:
                errors[CONF_PASSWORD] = "invalid_auth"
            except QswError:
                errors[CONF_URL] = "cannot_connect"
            else:
                title = f"QNAP {system_board.get_product()} {self._discovered_mac}"
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="discovered_connection",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
