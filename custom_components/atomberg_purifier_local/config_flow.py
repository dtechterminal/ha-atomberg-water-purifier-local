"""Find a purifier, verify its local connection, and explain internet isolation."""
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow

from .client import CannotConnect, LocalClient, discover
from .const import DOMAIN


class PurifierConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    _host = ""

    async def async_step_user(self, user_input=None):
        if user_input is None:
            self._found = await discover()
        if user_input:
            if user_input["device"] == "manual":
                return await self.async_step_manual()
            self._host = self._found[user_input["device"]]
            return await self._verify()
        if not self._found:
            return await self.async_step_manual()
        choices = {key: f"Intellon — {host}" for key, host in self._found.items()}
        choices["manual"] = "Enter an IP address"
        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required("device", default=next(iter(choices))): vol.In(choices),
        }))

    async def async_step_manual(self, user_input=None):
        if user_input:
            self._host = user_input["host"].strip()
            return await self._verify()
        return self.async_show_form(step_id="manual", data_schema=vol.Schema({
            vol.Required("host", default=self._host): str,
        }))

    async def _verify(self):
        try:
            state = await LocalClient(self._host).read()
        except (CannotConnect, ValueError):
            return self.async_show_form(step_id="manual", data_schema=vol.Schema({
                vol.Required("host", default=self._host): str,
            }), errors={"base": "cannot_connect"})
        await self.async_set_unique_id(state.device_id)
        if self.source == "reconfigure":
            self._abort_if_unique_id_mismatch()
            return self.async_update_reload_and_abort(self._get_reconfigure_entry(),
                                                     data_updates={"host": self._host})
        self._abort_if_unique_id_configured(updates={"host": self._host})
        return await self.async_step_finish()

    async def async_step_finish(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Atomberg Water Purifier", data={"host": self._host})
        return self.async_show_form(step_id="finish", data_schema=vol.Schema({}),
                                    description_placeholders={"host": self._host})

    async def async_step_reconfigure(self, user_input=None):
        self._host = self._get_reconfigure_entry().data["host"]
        return await self.async_step_manual(user_input)
