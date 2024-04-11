import os

from openai import AsyncOpenAI

import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider


api_key = os.environ.get("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)

# Instrument the OpenAI client
cl.instrument_openai()


@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="gpt-4-turbo",
            markdown_description="The underlying LLM model is **GPT-4 turbo**.",
            icon="https://picsum.photos/200",
        ),
        cl.ChatProfile(
            name="gpt-4",
            markdown_description="The underlying LLM model is **GPT-4**.",
            icon="https://picsum.photos/200",
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


async def get_response(message_history, settings):
    response = await client.chat.completions.create(
        messages=message_history, **settings
    )
    return response


@cl.step
async def get_total_tokens(response):
    if response.usage:
        tokens_used = cl.user_session.get("tokens_used")
        tokens_used += response.usage.total_tokens
        cl.user_session.set("tokens_used", tokens_used)
        if tokens_used > 10000:
            await cl.Message(
                content=f"Tokens used so far: {tokens_used}. Consider starting a new chat."
            ).send()
        return f"Tokens used so far in this thread: {tokens_used}."
    return None


@cl.on_message
async def main(message: cl.Message):
    # display loader
    msg = cl.Message(content="")
    await msg.send()

    # get chat profile
    chat_profile = cl.user_session.get("chat_profile")
    model_settings = {"model": chat_profile}

    # update chat history
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    # get response
    response = await get_response(message_history, model_settings)

    # summarize tokens used
    await get_total_tokens(response)

    # update and save chat history
    response = response.choices[0].message.content
    message_history.append({"role": "assistant", "content": response})
    cl.user_session.set("message_history", message_history)

    # display answer
    await cl.Message(content=response, author="Answer").send()
