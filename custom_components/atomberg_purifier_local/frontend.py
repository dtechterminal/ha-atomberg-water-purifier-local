"""Serve the bundled dashboard card and keep its dashboard resource current."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "atomberg-purifier-card.js"
CARD_URL = f"/{DOMAIN}/{CARD_FILENAME}"
CARD_PATH = Path(__file__).parent / "www" / CARD_FILENAME


async def async_register_card(hass: HomeAssistant) -> None:
    """Serve the card from the integration and register it as a dashboard resource."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_PATH), cache_headers=True)]
    )
    version = (await async_get_integration(hass, DOMAIN)).version
    url = f"{CARD_URL}?v={version}"

    if (resources := await _async_storage_resources(hass)) is None:
        _LOGGER.warning(
            "Dashboard resources are managed in YAML; add %s as a JavaScript module "
            "resource to use the Atomberg Purifier card",
            url,
        )
        return

    first, *duplicates = _card_resources(resources) or [None]
    if first is None:
        await resources.async_create_item({"res_type": "module", "url": url})
    elif first["url"] != url or first.get("type") != "module":
        await resources.async_update_item(first["id"], {"res_type": "module", "url": url})
    for item in duplicates:
        await resources.async_delete_item(item["id"])


async def async_unregister_card(hass: HomeAssistant) -> None:
    """Remove the card's dashboard resource."""
    if (resources := await _async_storage_resources(hass)) is None:
        return
    for item in _card_resources(resources):
        await resources.async_delete_item(item["id"])


async def _async_storage_resources(hass: HomeAssistant) -> ResourceStorageCollection | None:
    """Return the editable dashboard resources, or None in YAML mode."""
    if (lovelace := hass.data.get(LOVELACE_DATA)) is None:
        return None
    resources = lovelace.resources
    if not isinstance(resources, ResourceStorageCollection):
        return None
    if not resources.loaded:
        await resources.async_load()
        resources.loaded = True
    return resources


def _card_resources(resources: ResourceStorageCollection) -> list[dict]:
    """Return resources registered for this integration's card URL."""
    return [item for item in resources.async_items() if item["url"].split("?")[0] == CARD_URL]
