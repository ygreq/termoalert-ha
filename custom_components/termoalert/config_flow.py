"""Config flow for TermoAlert București integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CMTEB_URL,
    CONF_SCAN_INTERVAL,
    CONF_SEARCH_TERM,
    CONF_SECTOR,
    DEFAULT_HEADERS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import normalize_text

_LOGGER = logging.getLogger(__name__)

SECTOR_OPTIONS = {
    1: "Sector 1",
    2: "Sector 2",
    3: "Sector 3",
    4: "Sector 4",
    5: "Sector 5",
    6: "Sector 6",
}


class TermoAlertConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TermoAlert București."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            sector = user_input[CONF_SECTOR]
            search_term = user_input[CONF_SEARCH_TERM].strip()

            if len(search_term) < 3:
                errors[CONF_SEARCH_TERM] = "search_term_too_short"
            else:
                # Generate unique ID based on sector and normalized search term
                unique_id = f"{DOMAIN}_s{sector}_{normalize_text(search_term)}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                # Verify connectivity to CMTEB
                session = async_get_clientsession(self.hass)
                try:
                    async with asyncio.timeout(15):
                        async with session.get(CMTEB_URL, headers=DEFAULT_HEADERS) as resp:
                            if resp.status != 200:
                                errors["base"] = "cannot_connect"
                except Exception:
                    errors["base"] = "cannot_connect"

                if not errors:
                    title = f"Sector {sector} - {search_term}"
                    return self.async_create_entry(title=title, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_SECTOR, default=1): vol.In(SECTOR_OPTIONS),
                vol.Required(CONF_SEARCH_TERM): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=120)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return TermoAlertOptionsFlowHandler(config_entry)


class TermoAlertOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for TermoAlert București."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_sector = self.config_entry.options.get(
            CONF_SECTOR, self.config_entry.data.get(CONF_SECTOR, 1)
        )
        current_search = self.config_entry.options.get(
            CONF_SEARCH_TERM, self.config_entry.data.get(CONF_SEARCH_TERM, "")
        )
        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_SECTOR, default=current_sector): vol.In(SECTOR_OPTIONS),
                vol.Required(CONF_SEARCH_TERM, default=current_search): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=5, max=120)
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
