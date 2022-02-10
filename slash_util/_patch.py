from __future__ import annotations

import aiohttp
from discord import Embed, AllowedMentions, InvalidArgument, InteractionResponded, InteractionResponseType
from discord.ui import View
from discord.utils import MISSING, _to_json as to_json
from discord.http import Route
from discord.webhook.async_ import AsyncWebhookAdapter, ExecuteWebhookParameters, async_context

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Coroutine, TypeVar
    from discord import File
    
    R = TypeVar("R")
    Response = Coroutine[Any, Any, R]

def handle_message_parameters(
    content: str | None = MISSING,
    *,
    username: str = MISSING,
    avatar_url: Any = MISSING,
    tts: bool = False,
    ephemeral: bool = False,
    file: File = MISSING,
    files: list[File] = MISSING,
    embed: Embed = MISSING,
    embeds: list[Embed] = MISSING,
    view: View = MISSING,
    allowed_mentions: AllowedMentions = MISSING,
    previous_allowed_mentions: AllowedMentions | None = None,
    type: int = MISSING
) -> ExecuteWebhookParameters:
    if files is not MISSING and file is not MISSING:
        raise TypeError('Cannot mix file and files keyword arguments.')
    if embeds is not MISSING and embed is not MISSING:
        raise TypeError('Cannot mix embed and embeds keyword arguments.')

    payload = {}
    if embeds is not MISSING:
        if len(embeds) > 10:
            raise InvalidArgument('embeds has a maximum of 10 elements.')
        payload['embeds'] = [e.to_dict() for e in embeds]

    if embed is not MISSING:
        if embed is None:
            payload['embeds'] = []
        else:
            payload['embeds'] = [embed.to_dict()]

    if content is not MISSING:
        if content is not None:
            payload['content'] = str(content)
        else:
            payload['content'] = None

    if view is not MISSING:
        if view is not None:
            payload['components'] = view.to_components()
        else:
            payload['components'] = []

    payload['tts'] = tts
    if avatar_url:
        payload['avatar_url'] = str(avatar_url)
    if username:
        payload['username'] = username
    if ephemeral:
        payload['flags'] = 64

    if allowed_mentions:
        if previous_allowed_mentions is not None:
            payload['allowed_mentions'] = previous_allowed_mentions.merge(allowed_mentions).to_dict()
        else:
            payload['allowed_mentions'] = allowed_mentions.to_dict()
    elif previous_allowed_mentions is not None:
        payload['allowed_mentions'] = previous_allowed_mentions.to_dict()

    if type is not MISSING:
        payload = {'type': type, 'data': payload}

    multipart = []
    if file is not MISSING:
        files = [file]

    if files:
        multipart.append({'name': 'payload_json', 'value': to_json(payload)})
        payload = None
        if len(files) == 1:
            file = files[0]
            multipart.append(
                {
                    'name': 'file',
                    'value': file.fp,
                    'filename': file.filename,
                    'content_type': 'application/octet-stream',
                }
            )
        else:
            for index, file in enumerate(files):
                multipart.append(
                    {
                        'name': f'file{index}',
                        'value': file.fp,
                        'filename': file.filename,
                        'content_type': 'application/octet-stream',
                    }
                )

    return ExecuteWebhookParameters(payload=payload, multipart=multipart, files=files)

def create_interaction_response(
    self: AsyncWebhookAdapter,
    interaction_id: int,
    token: str,
    *,
    session: aiohttp.ClientSession,
    type: int,
    data: dict[str, Any] = MISSING,
    files: list[File] = MISSING
) -> Response[None]:
    route = Route(
        'POST',
        '/interactions/{webhook_id}/{webhook_token}/callback',
        webhook_id=interaction_id,
        webhook_token=token,
    )

    data = data or {}

    params = handle_message_parameters(
        **data,
        files=files,
        type=type
    )

    return self.request(route, session=session, payload=params.payload, files=params.files, multipart=params.multipart)

async def send_message(
    self,
    content: Any | None = None,
    *,
    embed: Embed = MISSING,
    embeds: list[Embed] = MISSING,
    file: File = MISSING,
    files: list[File] = MISSING,
    view: View = MISSING,
    tts: bool = False,
    ephemeral: bool = False,
) -> None:
    if self._responded:
        raise InteractionResponded(self._parent)

    payload: dict[str, Any] = {
        'tts': tts,
    }

    if embed is not MISSING and embeds is not MISSING:
        raise TypeError('cannot mix embed and embeds keyword arguments')

    if file is not MISSING and files is not MISSING:
        raise TypeError('cannot mix file and files keyword arguments')
    
    if file is not MISSING:
        files = [file]

    if embed is not MISSING:
        embeds = [embed]

    if embeds:
        if len(embeds) > 10:
            raise ValueError('embeds cannot exceed maximum of 10 elements')
        payload['embeds'] = [e.to_dict() for e in embeds]

    if content is not None:
        payload['content'] = str(content)

    if ephemeral:
        payload['flags'] = 64

    if view is not MISSING:
        payload['components'] = view.to_components()

    parent = self._parent

    adapter = async_context.get()
    await adapter.create_interaction_response(
        parent.id,
        parent.token,
        session=parent._session,
        type=InteractionResponseType.channel_message.value,
        data=payload,
        files=files  # type: ignore
    )

    if view is not MISSING:
        if ephemeral and view.timeout is None:
            view.timeout = 15 * 60.0

        self._parent._state.store_view(view)

    self._responded = True


def inject():
    from discord.webhook import async_
    from discord.interactions import InteractionResponse

    async_.handle_message_parameters = handle_message_parameters
    AsyncWebhookAdapter.create_interaction_response = create_interaction_response  # type: ignore
    InteractionResponse.send_message = send_message
