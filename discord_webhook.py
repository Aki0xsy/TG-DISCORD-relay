import asyncio
import io
import json
import logging
import mimetypes
import aiohttp

log = logging.getLogger(__name__)
MAX_CONTENT = 1900


def split_message(text: str, limit: int = MAX_CONTENT) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    rest = text
    while rest:
        if len(rest) <= limit:
            chunks.append(rest)
            break
        cut = rest.rfind("\n", 0, limit)
        if cut <= limit // 2:
            cut = limit
        chunk = rest[:cut].strip()
        if chunk:
            chunks.append(chunk)
        rest = rest[cut:].lstrip()
    return chunks


class DiscordWebhook:
    def __init__(self, url: str):
        self.url = url
        self.session = aiohttp.ClientSession()

    async def close(self):
        await self.session.close()

    def _payload(self, content: str, username: str | None) -> dict:
        payload = {
            "content": content,
            # Запрещает @everyone/@here пинги из пересылаемого текста
            "allowed_mentions": {"parse": []},
        }
        if username:
            payload["username"] = username[:80]
        return payload

    async def _post_json(self, payload: dict) -> bool:
        for attempt in range(5):
            try:
                async with self.session.post(self.url, json=payload) as resp:
                    if resp.status in (200, 204):
                        return True
                    if resp.status == 429:
                        wait = 1.0
                        try:
                            data = await resp.json()
                            wait = float(data.get("retry_after", wait))
                        except Exception:
                            pass
                        await asyncio.sleep(min(wait, 10))
                        continue
                    if resp.status >= 500:
                        await asyncio.sleep(1 + attempt)
                        continue
                    text = await resp.text()
                    log.warning("Discord webhook error %s: %s", resp.status, text[:500])
                    return False
            except Exception:
                log.exception("Discord webhook request failed")
                await asyncio.sleep(1 + attempt)
        return False

    async def send_text(self, content: str, username: str | None = None) -> bool:
        ok = True
        for chunk in split_message(content):
            if not await self._post_json(self._payload(chunk, username)):
                ok = False
        return ok

    async def send_file(self, data: bytes, filename: str, content: str, username: str | None = None) -> bool:
        payload = self._payload(content[:MAX_CONTENT], username)
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        for attempt in range(5):
            form = aiohttp.FormData()
            form.add_field("payload_json", json.dumps(payload, ensure_ascii=False), content_type="application/json")
            form.add_field("file", io.BytesIO(data), filename=filename, content_type=content_type)
            try:
                async with self.session.post(self.url, data=form) as resp:
                    if resp.status in (200, 204):
                        return True
                    if resp.status == 429:
                        wait = 1.0
                        try:
                            j = await resp.json()
                            wait = float(j.get("retry_after", wait))
                        except Exception:
                            pass
                        await asyncio.sleep(min(wait, 10))
                        continue
                    if resp.status >= 500:
                        await asyncio.sleep(1 + attempt)
                        continue
                    text = await resp.text()
                    log.warning("Discord webhook file error %s: %s", resp.status, text[:500])
                    return False
            except Exception:
                log.exception("Discord webhook file request failed")
                await asyncio.sleep(1 + attempt)
        return False
