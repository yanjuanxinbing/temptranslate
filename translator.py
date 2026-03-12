import re
import time
import asyncio
import aiohttp

from cache import LRU
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

    def get_time(self):
        return int(time.time() * 1000)

    async def translate(self, session: aiohttp.ClientSession, query: str):
        url = "https://fanyi.baidu.com/ait/text/translate"

        data = {
            "needNewlineCombine": False,
            "isAi": False,
            "sseStartTime": self.get_time(),
            "query": query,
            "from": "en",
            "to": "zh",
            "reference": "",
            "corpusIds": [],
            "needPhonetic": True,
            "domain": "common",
            "detectLang": "",
            "isIncognitoAI": False,
            "milliTimestamp": self.get_time()
        }

        headers = {
            "Acs-Token": f"{data['sseStartTime']}_{data['milliTimestamp']}"
        }

        try:
            async with session.post(url, json=data, headers=headers, timeout=1) as res:
                text = await res.text()
                result = re.findall(r'"dst":"(.*?)"', text)
        except:
            return ""

        return result[0] if result else ""

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

                        if trans:
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
                "temperature": 0,
                "num_predict": 96,
                "num_ctx": 2048
            }
        )
        return response["message"]["content"].strip()

    async def update(self, text_var: StringVar):
        while self.alive:
            if self.running:
                string = self.get_string()

                if string:
                    trans = self.cache.get(string)

                    if not trans:
                        trans = await self.translate_llm(string)
                        self.cache.put(string, trans)
                            
                    if trans:
                        text_var.set(trans)

            await asyncio.sleep(0.5)