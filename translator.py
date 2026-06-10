import time
import asyncio
import aiohttp
import hashlib

from cache import LRU
from config import APP_ID, APP_KEY
from ollama import AsyncClient
from abc import ABC, abstractmethod
from customtkinter import StringVar
from listener import RenpyMemoryListener

class BaseTranslator(ABC):
    def __init__(self):
        self.alive = True
        self.running = False
        self.cache = LRU(128)
        self.listener = RenpyMemoryListener("LessonsInLove")

    def get_string(self) -> str:
        return self.listener.run_once()
        
    def switch(self):
        self.running = not self.running

    def paused(self):
        return not self.running

    def close(self):
        self.alive = False
        self.running = False

    def closed(self):
        return not self.alive

    @abstractmethod
    async def update(self, text_var: StringVar):
        pass

    def __call__(self, text_var: StringVar):
        asyncio.run(self.update(text_var))

class Translator(BaseTranslator):
    def __init__(self):
        super().__init__()

    async def translate(self, session: aiohttp.ClientSession, query: str) -> str:
        url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
        salt = str(int(time.time() * 1000))
        params = {
            "q":     query,
            "from":  "en",
            "to":    "zh",
            "appid": APP_ID,
            "salt":  salt,
            "sign":  hashlib.md5((APP_ID + query + salt + APP_KEY).encode()).hexdigest(),
        }

        try:
            async with session.get(url, params=params) as res:
                data = await res.json()
            return data["trans_result"][0]["dst"]
        except:
            return ""

    async def update(self, text_var: StringVar):
        async with aiohttp.ClientSession() as session:
            while self.alive:
                if self.running:
                    string = self.get_string()

                    if string:
                        trans = self.cache.get(string)

                        if not trans:
                            trans = await self.translate(session, string)
                            if trans:
                                self.cache.put(string, trans)

                        if trans and trans != text_var.get():
                            text_var.set(trans)

                await asyncio.sleep(0.5)

class AiTranslator(BaseTranslator):
    def __init__(self):
        super().__init__()
        self.model = "translategemma:4b"
        self.system_prompt = (
            "以汉化组水准将英文翻译成中文，只输出翻译结果，不添加多余内容。"
        )
        self.client = AsyncClient()

    async def translate_llm(self, text: str) -> str:
        response = await self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": text}
            ],
            options={
                "temperature": 0
            }
        )
        return response.message.content.strip()

    async def update(self, text_var: StringVar):
        while self.alive:
            if self.running:
                string = self.get_string()

                if string:
                    trans = self.cache.get(string)

                    if not trans:
                        trans = await self.translate_llm(string)
                        if trans:
                            self.cache.put(string, trans)
                            
                    if trans and trans != text_var.get():
                        text_var.set(trans)

            await asyncio.sleep(0.5)