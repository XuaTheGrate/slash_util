from __future__ import annotations

import aiohttp
from discord import Embed, AllowedMentions, InvalidArgument, InteractionResponded, InteractionResponseType, InteractionType, Attachment
from discord import InteractionResponse as DpyInteractionResponse
from discord.ui import View
from discord.utils import MISSING, _to_json as to_json
from discord.http import Route
from discord.webhook.async_ import AsyncWebhookAdapter, ExecuteWebhookParameters, async_context

from .modal import Modal

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
    embed: Embed | None = MISSING,
    embeds: list[Embed] = MISSING,
    view: View | None = MISSING,
    allowed_mentions: AllowedMentions = MISSING,
    previous_allowed_mentions: AllowedMentions | None = None,
    type: int = MISSING,
    attachments: list[Attachment] = MISSING,
    modal: Modal = MISSING
) -> ExecuteWebhookParameters:
    if modal is not MISSING:
        return ExecuteWebhookParameters(payload={"type": 9, "data": modal.to_dict()}, multipart=None, files=None)

    if files is not MISSING and file is not MISSING:
        raise TypeError('Cannot mix file and files keyword arguments.')

    if (file is not MISSING or files is not MISSING) and attachments is not MISSING:
        raise TypeError('Cannot mix file/files and attachments arguments.')

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

    if attachments is not MISSING:
        payload['attachments'] = [a.to_dict() for a in attachments]

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
    data: ExecuteWebhookParameters
) -> Response[None]:
    route = Route(
        'POST',
        '/interactions/{webhook_id}/{webhook_token}/callback',
        webhook_id=interaction_id,
        webhook_token=token,
    )

    return self.request(route, session=session, payload=data.payload, files=data.files, multipart=data.multipart)

class InteractionResponse(DpyInteractionResponse):
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
        allowed_mentions: AllowedMentions = MISSING
    ) -> None:
        if self._responded:
            raise InteractionResponded(self._parent)

        parent = self._parent

        payload = handle_message_parameters(
            content=content,
            tts=tts,
            ephemeral=ephemeral,
            type=InteractionResponseType.channel_message.value,
            embed=embed,
            embeds=embeds,
            view=view,
            file=file,
            files=files,
            allowed_mentions=allowed_mentions
        )

        adapter = async_context.get()
        await adapter.create_interaction_response(parent.id, parent.token, session=parent._session, data=payload)  # type: ignore

        if view is not MISSING:
            if ephemeral and view.timeout is None:
                view.timeout = 15 * 60.0

            self._parent._state.store_view(view)

        self._responded = True

    async def defer(self, *, ephemeral: bool = False) -> None:
        if self._responded:
            raise InteractionResponded(self._parent)

        defer_type: int = 0

        parent = self._parent
        if parent.type is InteractionType.component:
            defer_type = InteractionResponseType.deferred_message_update.value
        elif parent.type is InteractionType.application_command:
            defer_type = InteractionResponseType.deferred_channel_message.value

        payload = handle_message_parameters(type = defer_type or MISSING, ephemeral=ephemeral)

        if defer_type:
            adapter = async_context.get()
            await adapter.create_interaction_response(
                parent.id, parent.token, session=parent._session, data=payload
            )  # type: ignore
            self._responded = True

    async def pong(self) -> None:
        if self._responded:
            raise InteractionResponded(self._parent)

        parent = self._parent
        if parent.type is InteractionType.ping:
            adapter = async_context.get()
            data = handle_message_parameters(type = InteractionResponseType.pong.value)
            await adapter.create_interaction_response(
                parent.id, parent.token, session=parent._session, data=data
            )  # type: ignore
            self._responded = True

    async def edit_message(
        self,
        *,
        content: Any | None = MISSING,
        embed: Embed | None = MISSING,
        embeds: list[Embed] = MISSING,
        attachments: list[Attachment] = MISSING,
        view: View | None = MISSING,
    ) -> None:
        if self._responded:
            raise InteractionResponded(self._parent)

        parent = self._parent
        msg = parent.message
        state = parent._state
        message_id = msg.id if msg else None

        if parent.type is not InteractionType.component:
            return

        payload = handle_message_parameters(
            content=content,
            embed=embed,
            embeds=embeds,
            attachments=attachments,
            view=view,
            type=InteractionResponseType.message_update.value
        )
        Attachment.to_dict

        adapter = async_context.get()
        await adapter.create_interaction_response(
            parent.id,
            parent.token,
            session=parent._session,
            data=payload,
        )  # type: ignore
        if view and not view.is_finished():
            state.store_view(view, message_id)
        self._responded = True

    async def send_modal(self, modal: Modal) -> None:
        if not hasattr(self._parent._state, "_modals"):
            self._parent._state._modals = {}  # type: ignore
        self._parent._state._modals[modal.custom_id] = modal  # type: ignore

        parent = self._parent
        if self._responded:
            raise InteractionResponded(self._parent)
        
        payload = handle_message_parameters(modal=modal)
        adapter = async_context.get()
        await adapter.create_interaction_response(parent.id, parent.token, session=parent._session, data=payload)  # type: ignore
        self._responded = True

def inject():
    import discord
    from discord.webhook import async_

    discord.interactions.InteractionResponse = InteractionResponse

    async_.handle_message_parameters = handle_message_parameters
    AsyncWebhookAdapter.create_interaction_response = create_interaction_response  # type: ignore
    
