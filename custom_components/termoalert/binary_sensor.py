"""Binary sensor platform for TermoAlert București."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CMTEB_URL, DOMAIN, MANUFACTURER, MODEL
from .coordinator import TermoAlertCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TermoAlert binary sensor from a config entry."""
    coordinator: TermoAlertCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TermoAlertOutageBinarySensor(coordinator, entry)])


class TermoAlertOutageBinarySensor(CoordinatorEntity[TermoAlertCoordinator], BinarySensorEntity):
    """Representation of a TermoAlert outage binary sensor."""

    _attr_has_entity_name = True
    _attr_translation_key = "outage"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(
        self,
        coordinator: TermoAlertCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_outage"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"TermoAlert {self._entry.title}",
            manufacturer=MANUFACTURER,
            model=MODEL,
            configuration_url=CMTEB_URL,
        )

    @property
    def is_on(self) -> bool:
        """Return True if there is an active outage or deficiency for the configured address."""
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get("is_affected", False))

    @property
    def icon(self) -> str:
        """Return dynamic icon based on state."""
        return "mdi:water-boiler-off" if self.is_on else "mdi:water-boiler"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed outage attributes."""
        if not self.coordinator.data:
            return {}

        data = self.coordinator.data
        active = data.get("active_outage") or {}

        return {
            "is_affected": data.get("is_affected", False),
            "punct_termic": active.get("matched_pt"),
            "agent_afectat": active.get("agent_type"),
            "cauza": active.get("cause"),
            "estimare_punere_in_functiune": active.get("estimated_restoration"),
            "adresa_identificata": active.get("matched_street"),
            "total_avarii_sector": data.get("total_sector_outages", 0),
            "sector": data.get("sector"),
            "termen_cautat": data.get("search_term"),
            "ultima_actualizare_cmteb": data.get("last_update"),
        }
