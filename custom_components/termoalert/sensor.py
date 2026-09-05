"""Sensor platform for TermoAlert București."""
from __future__ import annotations

import unicodedata
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
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
    """Set up TermoAlert sensor entities from a config entry."""
    coordinator: TermoAlertCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            TermoAlertOutageTextSensor(coordinator, entry),
            TermoAlertStatusSensor(coordinator, entry),
            TermoAlertRestorationSensor(coordinator, entry),
            TermoAlertCountdownSensor(coordinator, entry),
            TermoAlertSectorOutagesSensor(coordinator, entry),
        ]
    )


class TermoAlertBaseSensor(CoordinatorEntity[TermoAlertCoordinator], SensorEntity):
    """Base class for TermoAlert sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TermoAlertCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the base sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"

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


def format_agent_status(raw: str) -> str:
    """Format CMTEB technical agent abbreviation into concise Romanian text."""
    if not raw:
        return "Avarie activă"

    # Normalize diacritics to ASCII uppercase for robust matching
    nfkd = unicodedata.normalize("NFKD", raw)
    s = "".join(c for c in nfkd if not unicodedata.combining(c)).upper()

    has_acc = "ACC" in s or "APA CALDA" in s
    has_inc = "INC" in s or "INCALZIRE" in s
    is_deficient = "DEFICIENT" in s
    is_oprire = "OPRIRE" in s or "SISTARE" in s or "INTRERUP" in s

    if is_deficient:
        if has_acc and has_inc:
            return "Deficiență apă & căldură"
        elif has_acc:
            return "Deficiență apă caldă"
        elif has_inc:
            return "Deficiență încălzire"
        return "Deficiență agent termic"
    elif is_oprire:
        if has_acc and has_inc:
            return "Oprire apă & căldură"
        elif has_acc:
            return "Oprire apă caldă"
        elif has_inc:
            return "Oprire încălzire"
        return "Oprire agent termic"
    else:
        if has_acc and has_inc:
            return "Avarie apă & căldură"
        elif has_acc:
            return "Avarie apă caldă"
        elif has_inc:
            return "Avarie încălzire"

    return raw


class TermoAlertOutageTextSensor(TermoAlertBaseSensor):
    """Sensor showing outage indicator directly as Romanian text (Problemă / OK)."""

    _attr_translation_key = "outage_status"

    def __init__(self, coordinator: TermoAlertCoordinator, entry: ConfigEntry) -> None:
        """Initialize outage text sensor."""
        super().__init__(coordinator, entry, "outage_status")

    @property
    def native_value(self) -> str:
        """Return Problemă when affected, OK when normal."""
        if not self.coordinator.data:
            return "Necunoscut"
        if self.coordinator.data.get("is_affected", False):
            return "Problemă"
        return "OK"

    @property
    def icon(self) -> str:
        """Return dynamic icon."""
        if self.coordinator.data and self.coordinator.data.get("is_affected", False):
            return "mdi:alert-circle"
        return "mdi:check-circle"


class TermoAlertStatusSensor(TermoAlertBaseSensor):
    """Sensor showing current service status."""

    _attr_translation_key = "service_status"

    def __init__(self, coordinator: TermoAlertCoordinator, entry: ConfigEntry) -> None:
        """Initialize status sensor."""
        super().__init__(coordinator, entry, "service_status")

    @property
    def native_value(self) -> str:
        """Return the current service status."""
        if not self.coordinator.data:
            return "Necunoscut"

        data = self.coordinator.data
        if not data.get("is_affected", False):
            return "Normal"

        active = data.get("active_outage") or {}
        raw = active.get("agent_type", "Avarie activă")
        return format_agent_status(raw)

    @property
    def icon(self) -> str:
        """Return dynamic icon."""
        if self.coordinator.data and self.coordinator.data.get("is_affected", False):
            return "mdi:alert-decagram"
        return "mdi:check-decagram"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        if not self.coordinator.data:
            return {}
        active = self.coordinator.data.get("active_outage") or {}
        return {
            "agent_afectat_raw": active.get("agent_type"),
            "cauza": active.get("cause"),
            "punct_termic": active.get("matched_pt"),
            "adresa": active.get("matched_street"),
        }


class TermoAlertRestorationSensor(TermoAlertBaseSensor):
    """Sensor showing estimated restoration time."""

    _attr_translation_key = "estimated_restoration"
    _attr_icon = "mdi:clock-alert-outline"

    def __init__(self, coordinator: TermoAlertCoordinator, entry: ConfigEntry) -> None:
        """Initialize restoration time sensor."""
        super().__init__(coordinator, entry, "estimated_restoration")

    @property
    def native_value(self) -> str:
        """Return estimated restoration date and time."""
        if not self.coordinator.data:
            return "Necunoscut"

        data = self.coordinator.data
        if not data.get("is_affected", False):
            return "Nicio avarie"

        active = data.get("active_outage") or {}
        return active.get("estimated_restoration", "Fără estimare")


class TermoAlertSectorOutagesSensor(TermoAlertBaseSensor):
    """Sensor showing total number of active outages in the configured sector."""

    _attr_translation_key = "sector_outages"
    _attr_icon = "mdi:city-variant-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "avarii"

    def __init__(self, coordinator: TermoAlertCoordinator, entry: ConfigEntry) -> None:
        """Initialize sector outages sensor."""
        super().__init__(coordinator, entry, "sector_outages")

    @property
    def native_value(self) -> int:
        """Return total active outages in this sector."""
        if not self.coordinator.data:
            return 0
        return int(self.coordinator.data.get("total_sector_outages", 0))


class TermoAlertCountdownSensor(TermoAlertBaseSensor):
    """Sensor showing countdown (days & hours) until restoration."""

    _attr_translation_key = "time_remaining"
    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator: TermoAlertCoordinator, entry: ConfigEntry) -> None:
        """Initialize countdown sensor."""
        super().__init__(coordinator, entry, "time_remaining")

    @property
    def native_value(self) -> str:
        """Return countdown string in Romanian."""
        if not self.coordinator.data or not self.coordinator.data.get("is_affected", False):
            return "Fără avarie"

        active = self.coordinator.data.get("active_outage") or {}
        raw = active.get("estimated_restoration")
        if not raw:
            return "Fără estimare"

        try:
            dt = datetime.strptime(raw.strip(), "%d.%m.%Y %H:%M")
            now = datetime.now()
            diff_seconds = int((dt - now).total_seconds())

            if diff_seconds <= 0:
                return "Termen depășit"

            days = diff_seconds // 86400
            hours = (diff_seconds % 86400) // 3600

            if days > 0 and hours > 0:
                return f"{days} zile și {hours} ore"
            elif days > 0:
                return f"{days} zile"
            elif hours > 0:
                return f"{hours} ore"
            else:
                mins = (diff_seconds % 3600) // 60
                return f"{mins} minute"
        except Exception:
            return "Format necunoscut"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return countdown calculation details."""
        if not self.coordinator.data or not self.coordinator.data.get("is_affected", False):
            return {}

        active = self.coordinator.data.get("active_outage") or {}
        raw = active.get("estimated_restoration")
        if not raw:
            return {}

        try:
            dt = datetime.strptime(raw.strip(), "%d.%m.%Y %H:%M")
            now = datetime.now()
            diff_seconds = int((dt - now).total_seconds())

            return {
                "zile_ramase": max(0, diff_seconds // 86400),
                "ore_ramase": max(0, (diff_seconds % 86400) // 3600),
                "minute_ramase": max(0, (diff_seconds % 3600) // 60),
                "total_secunde": max(0, diff_seconds),
                "termen_depasit": diff_seconds <= 0,
                "termen_estimat": raw.strip(),
            }
        except Exception:
            return {}

