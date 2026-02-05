"""
Module for interacting with OpenAI's GPT API.
"""
from openai import OpenAI
import httpx
from telegram.ext import ContextTypes


class ChatGPTService:
    """
    Service for managing chat interactions with OpenAI's ChatGPT.
    """
    def __init__(self, token):
        """
        Initializes the ChatGPTService with an OpenAI API token and a proxy.
        """
        self.client = OpenAI(
            http_client=httpx.Client(proxy="http://18.199.183.77:49232"),
            api_key=token
        )

    def _get_user_history(self, context: ContextTypes.DEFAULT_TYPE) -> list:
        """
        Retrieves the conversation history for a specific user from the context.
        """
        if "gpt_history" not in context.user_data:
            context.user_data["gpt_history"] = []
        return context.user_data["gpt_history"]

    async def send_message_list(self, messages: list) -> str:
        """
        Sends the message list to OpenAI and returns the AI's response.
        """
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=3000,
            temperature=0.9
        )
        response_message = completion.choices[0].message
        return response_message.content

    def set_prompt(self, context: ContextTypes.DEFAULT_TYPE, prompt_text: str) -> None:
        """
        Sets the system prompt for the conversation, clearing previous history.
        """
        history = self._get_user_history(context)
        history.clear()
        history.append({"role": "system", "content": prompt_text})

    async def add_message(self, context: ContextTypes.DEFAULT_TYPE, message_text: str) -> str:
        """
        Adds a user message to the conversation and gets the AI response.
        """
        history = self._get_user_history(context)
        history.append({"role": "user", "content": message_text})
        
        response = await self.send_message_list(history)
        history.append({"role": "assistant", "content": response})
        return response

    async def send_question(self, prompt_text: str, message_text: str) -> str:
        """
        Sends a single question with a specific system prompt, without affecting history.
        """
        messages = [
            {"role": "system", "content": prompt_text},
            {"role": "user", "content": message_text}
        ]
        return await self.send_message_list(messages)
