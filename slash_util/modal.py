from __future__ import annotations
import asyncio

import os
from typing import Any, TYPE_CHECKING

from discord import Interaction
from discord.utils import MISSING

from .enums import TextInputStyle

__all__ = ['TextInput', 'Modal']

class TextInput:
    def __init__(self, *,
        label: str,
        style: TextInputStyle,
        custom_id: str = MISSING,
        min_length: int | None = None,
        max_length: int | None = None,
        required: bool = True,
        default_value: str | None = None,
        placeholder: str | None = None
    ) -> None:
        if custom_id is MISSING:
            custom_id = os.urandom(16).hex()
        
        if min_length is not None and min_length < 0:
            raise ValueError("min_length must be greater or equal to 0")
        
        if max_length is not None and (max_length > 4000 or max_length < 1):
            raise ValueError("max_length must be lower or equal to 4000 and greater or equal to 1")

        self.style = style
        self.custom_id = custom_id
        self.label = label
        self.required = required
        self.default_value = default_value
        self.placeholder = placeholder
        self.min_length = min_length
        self.max_length = max_length

    def to_dict(self) -> dict[str, Any]:
        data = {
            "type": 4,
            "style": self.style.value,
            "custom_id": self.custom_id,
            "label": self.label,
            "required": self.required
        }

        if self.placeholder is not None:
            data['placeholder'] = self.placeholder
        if self.default_value is not None:
            data['value'] = self.default_value
        if self.min_length is not None:
            data['min_length'] = self.min_length
        if self.max_length is not None:
            data['max_length'] = self.max_length

        return data

class Modal:
    def __init__(self, *, title: str, custom_id: str = MISSING, items: list[TextInput] = MISSING):
        self.custom_id = os.urandom(16).hex() if custom_id is MISSING else custom_id
        self.title = title

        self._items: dict[str, TextInput] = {} if items is MISSING else {item.custom_id: item for item in items}

        self._response: asyncio.Future[Interaction] = asyncio.Future()

    @staticmethod
    def parse_interaction(interaction: Interaction) -> dict[str, str]:
        return dict(
            (d['components'][0]['custom_id'], d['components'][0]['value'])
            for d in interaction.data['components']  # type: ignore
        )

    def add_item(self, item: TextInput) -> None:
        self._items[item.custom_id] = item

    def remove_item(self, item: TextInput) -> None:
        self._items.pop(item.custom_id, None)

    def get_item(self, custom_id: str) -> TextInput | None:
        return self._items.get(custom_id)

    def is_done(self) -> bool:
        return self._response.done()

    def reset(self) -> None:
        if not self._response.done():
            self._response.set_exception(asyncio.CancelledError())
        self._response = asyncio.Future()

    @property
    def response(self) -> dict[str, str]:
        if not self._response.done():
            raise RuntimeError("Modal has not received a response.")
        return self.parse_interaction(self._response.result())

    @property
    def result(self) -> Interaction:
        return self._response.result()

    async def wait(self, timeout: float = 180.0) -> Interaction:
        if self.is_done():
            return self.result
        
        return await asyncio.wait_for(self._response, timeout=timeout)

    def to_dict(self) -> dict[str, Any]:
        data = {
            "custom_id": self.custom_id,
            "title": self.title,
            "components": []
        }
        for item in self._items.values():
            data["components"].append({
                "type": 1,
                "components": [item.to_dict()]
            })
        
        return data
