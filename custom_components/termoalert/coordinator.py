"""DataUpdateCoordinator for TermoAlert București."""
from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from datetime import datetime, timedelta
from typing import Any

from bs4 import BeautifulSoup

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CMTEB_URL,
    CONF_SCAN_INTERVAL,
    CONF_SEARCH_TERM,
    CONF_SECTOR,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """Normalize text by stripping diacritics, lowercase and expanding abbreviations."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    
    replacements = [
        (r"\bstrada\b", "str"),
        (r"\bbulevardul\b", "bld"),
        (r"\bbd\b", "bld"),
        (r"\bsoseaua\b", "sos"),
        (r"\baleea\b", "ale"),
        (r"\bcalea\b", "cal"),
        (r"\bintrarea\b", "int"),
        (r"\bpiata\b", "pta"),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)
        
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_thermal_zones(cell) -> list[dict[str, Any]]:
    """Parse cell content into thermal points and affected street lists."""
    raw_html = cell.decode_contents() if hasattr(cell, "decode_contents") else str(cell)
    parts = re.split(r"(?i)punct\s+termic\s*:", raw_html)
    pts = []
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        soup = BeautifulSoup(part, "html.parser")
        lines = [line.strip() for line in soup.get_text("\n").split("\n") if line.strip()]
        if not lines:
            continue
        header = lines[0]
        streets = [l.lstrip("•").strip() for l in lines[1:] if l.strip()]
        pts.append({
            "header": header,
            "streets": streets,
        })
    return pts


def parse_cmteb_html(html: str, target_sector: int, search_term: str) -> dict[str, Any]:
    """Parse CMTEB HTML table to find outages for a given sector and search term."""
    soup = BeautifulSoup(html, "html.parser")
    tab_id = f"S{target_sector}" if target_sector else "ST"
    tab = soup.find("div", id=tab_id)
    if not tab:
        tab = soup.find("div", id="ST")

    if not tab:
        raise ValueError("Tabelul de avarii nu a fost găsit în pagina CMTEB.")

    normalized_search = normalize_text(search_term) if search_term else ""
    all_sector_outages = []
    matched_outages = []

    rows = tab.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        try:
            sector = int(cols[0].get_text().strip())
        except ValueError:
            continue

        if target_sector and sector != target_sector:
            continue

        agent_type = cols[2].get_text().strip()
        cause = cols[3].get_text().strip()
        estimated_restoration = cols[4].get_text().strip()
        pts = parse_thermal_zones(cols[1])

        row_matched = False
        matched_pt_name = None
        matched_street = None

        if normalized_search:
            for pt in pts:
                if normalized_search in normalize_text(pt["header"]):
                    row_matched = True
                    matched_pt_name = pt["header"]
                    break
                for st in pt["streets"]:
                    if normalized_search in normalize_text(st):
                        row_matched = True
                        matched_pt_name = pt["header"]
                        matched_street = st
                        break
                if row_matched:
                    break

        outage_entry = {
            "sector": sector,
            "thermal_points": [p["header"] for p in pts],
            "agent_type": agent_type,
            "cause": cause,
            "estimated_restoration": estimated_restoration,
            "matched": row_matched,
            "matched_pt": matched_pt_name,
            "matched_street": matched_street,
            "all_affected": [s for p in pts for s in p["streets"]],
        }

        all_sector_outages.append(outage_entry)
        if row_matched:
            matched_outages.append(outage_entry)

    active_outage = matched_outages[0] if matched_outages else None

    return {
        "sector": target_sector,
        "search_term": search_term,
        "total_sector_outages": len(all_sector_outages),
        "is_affected": len(matched_outages) > 0,
        "active_outage": active_outage,
        "matched_count": len(matched_outages),
        "last_update": datetime.now().isoformat(),
    }


class TermoAlertCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching TermoAlert data from CMTEB."""

    def __init__(
        self,
        hass: HomeAssistant,
        sector: int,
        search_term: str,
        scan_interval_minutes: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        self.sector = sector
        self.search_term = search_term
        self.session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_s{sector}_{search_term}",
            update_interval=timedelta(minutes=scan_interval_minutes),
        )

    def update_config(self, sector: int, search_term: str, scan_interval_minutes: int) -> None:
        """Update coordinator runtime parameters."""
        self.sector = sector
        self.search_term = search_term
        self.update_interval = timedelta(minutes=scan_interval_minutes)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and parse data from CMTEB."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        try:
            async with asyncio.timeout(20):
                async with self.session.get(CMTEB_URL, headers=headers) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"Serverul CMTEB a returnat codul HTTP {resp.status}")
                    html = await resp.text()

        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout la conectarea cu cmteb.ro") from err
        except Exception as err:
            raise UpdateFailed(f"Eroare la descărcarea datelor de la CMTEB: {err}") from err

        try:
            return await self.hass.async_add_executor_job(
                parse_cmteb_html, html, self.sector, self.search_term
            )
        except Exception as err:
            raise UpdateFailed(f"Eroare la parsarea paginii de avarii CMTEB: {err}") from err
