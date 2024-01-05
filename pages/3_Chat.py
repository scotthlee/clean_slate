import streamlit as st
import openai
import json
import os

from tools import strml
from tools.strml import update_settings, keep, reset_gpt


def clear_chat():
    st.session_state.old_messages = st.session_state.messages
    st.session_state.messages = []
    return


def load_chat():
    st.session_state.messages = st.session_state.old_messages
    return


def compile_chat():
    chat_out = [m['role'].capitalize() + ':\n' + m['content'] + '\n\n'
                for m in st.session_state.messages]
    chat_out = ''.join(chat_out)
    return chat_out


# Setting up the OpenAI API
strml.load_openai_settings()

# Adding the page title and icon
st.set_page_config(page_title='Chat', page_icon='😺')

# Creating a prompt with the current draft content
draft_message = "Here's a draft of some web content I'm working on. "
draft_message += "Please keep this in mind as content for our conversation "
draft_message += "while we chat. \n Draft:\n" + st.session_state.saved_text
draft_prompt = [{"role": "user", "content": draft_message}]

if not st.session_state.authentication_status:
    st.error('Please log in at the Welcome Page to continue.')
else:
    with st.sidebar:
        st.write('Settings')
        draft_toggle = st.toggle(label='Chat about Draft',
                                 key='_draft_chat',
                                 disabled=True,
                                 value=st.session_state.draft_chat,
                                 kwargs={'keys': ['draft_chat']},
                                 on_change=update_settings)
        with st.expander('Chat Controls', expanded=True):
            cl_chat = st.button(label='Clear',
                                help='Clear current chat history.',
                                key='clear_chat',
                                on_click=clear_chat)
            undo_clear = st.button(label='Undo Clear',
                                   type='secondary',
                                   help='Load chat messages from your last session.',
                                   key='undo_clear',
                                   on_click=load_chat)
            save_chat = st.download_button(
                label = 'Save Chat',
                data = compile_chat(),
                file_name = "chat.txt",
                mime = "text/markdown"
            )
        with st.expander('ChatGPT', expanded=False):
            curr_model = st.session_state.model_name
            st.selectbox(label='Engine',
                          key='_model_name',
                          on_change=update_settings,
                          kwargs={'keys': ['model_name']},
                          index=st.session_state.engine_choices.index(curr_model),
                          options=st.session_state.engine_choices)
            st.number_input(label='Max Tokens',
                            key='_max_tokens',
                            on_change=update_settings,
                            kwargs={'keys': ['max_tokens']},
                            value=st.session_state.max_tokens)
            st.slider(label='Temperature',
                      key='_temperature',
                      on_change=update_settings,
                      kwargs={'keys': ['temperature']},
                      value=st.session_state.temperature)
            st.slider(label='Top P',
                      key='_top_p',
                      on_change=update_settings,
                      kwargs={'keys': ['top_p']},
                      value=st.session_state.top_p)
            st.slider(label='Presence Penalty',
                      min_value=0.0,
                      max_value=2.0,
                      key='_presence_penalty',
                      on_change=update_settings,
                      kwargs={'keys': ['presence_penalty']},
                      value=st.session_state.presence_penalty)
            st.slider(label='Frequency Penalty',
                      min_value=0.0,
                      max_value=2.0,
                      key='_frequency_penalty',
                      on_change=update_settings,
                      kwargs={'keys': ['frequency_penalty']},
                      value=st.session_state.frequency_penalty)
            st.button('Reset',
                      on_click=reset_gpt)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        if st.session_state.draft_chat:
            st.write(st.session_state.messages)
            if (st.session_state.messages is None) or (len(st.session_state.messages) == 0):
                st.session_state.messages = draft_prompt
            else:
                if st.session_state.messages[0] != draft_prompt:
                    st.session_state.messages.insert(0, draft_prompt)

        st.session_state.messages.append({"role": "user",
                                          "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]
            try:
                completion = openai.ChatCompletion.create(
                    engine=st.session_state.engine,
                    messages=messages,
                    temperature=st.session_state.temperature,
                    max_tokens=st.session_state.max_tokens,
                    top_p=st.session_state.top_p,
                    frequency_penalty=st.session_state.frequency_penalty,
                    presence_penalty=st.session_state.presence_penalty,
                    stream=True,
                    stop=None
                )
                for response in completion:
                    try:
                        full_response += (response.choices[0].delta.content or "")
                    except:
                        full_response += ""
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
            except:
                st.error('OpenAI API currently unavailable.')
        st.session_state.messages.append({"role": "assistant",
                                          "content": full_response})
