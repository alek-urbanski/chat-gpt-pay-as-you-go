import os

from openai import AsyncOpenAI

import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider


api_key = os.environ.get("OPENAI_API_KEY")
client = AsyncOpenAI(api_key)

# Instrument the OpenAI client
cl.instrument_openai()


@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="gpt-4-turbo",
            markdown_description="The underlying LLM model is **GPT-4 turbo**.",
            icon="https://picsum.photos/200?random=1",
        ),
        cl.ChatProfile(
            name="gpt-4",
            markdown_description="The underlying LLM model is **GPT-4**.",
            icon="https://picsum.photos/200?random=2",
        ),
        cl.ChatProfile(
            name="gpt-3.5-turbo",
            markdown_description="The underlying LLM model is **GPT-3.5 turbo**.",
            icon="https://picsum.photos/200?random=3",
        ),
    ]


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set(
        "message_history",
        [
            {
                "role": "system",
                "content": "You are a helpful assistant, you always reply in English",
            }
        ],
    )
    cl.user_session.set("tokens_used", 0)


@cl.on_message
async def main(message: cl.Message):
    # display loader
    msg = cl.Message(content="")
    await msg.send()

    # get chat profile
    chat_profile = cl.user_session.get("chat_profile")
    model_settings = {"model": chat_profile, "stream": True}

    # add the user question to the chat history
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    # get and print response token by token
    stream = await client.chat.completions.create(
        messages=message_history, **model_settings
    )
    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    # add the response to the chat history
    response = msg.content
    message_history.append({"role": "assistant", "content": response})
    await msg.update()
