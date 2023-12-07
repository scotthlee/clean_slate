import streamlit as st
import openai


def keep(key):
    st.session_state[key] = st.session_state['_' + key]
    return


def unkeep(key):
    # Copy from permanent key to temporary widget key
    st.session_state['_' + key] = st.session_state[key]


def update_settings(keys, toast=True):
    for key in keys:
        keep(key)
    if toast:
        st.toast('Settings updated!', icon='👍')
    pass


def save_text(toast=True):
    err_mess = 'No draft to save. Please create some content by loading \
             a file or passing an empty content template to the model.'
    if 'saved_text' not in st.session_state:
        st.error(err_mess)
    elif st.session_state.saved_text == 'Click "Start" to prompt the model.':
        st.error(err_mess)
    else:
        fname = st.session_state.draft_file_name
        fname += st.session_state.draft_file_type
        open('output/' + fname, 'w').write(st.session_state.saved_text)
        if toast:
            st.toast('Text saved!', icon='👍')
    return


def reset_gpt():
    for key in st.session_state.gpt_keys['keys']:
        st.session_state[key] = st.session_state.gpt_defaults[key]
    return


def load_openai_settings():
    mod = st.session_state.model_name
    options = st.session_state.gpt_dict[mod]
    st.session_state.engine = options['engine']
    openai.api_base = options['url']
    openai.api_type = st.session_state.api_type
    openai.api_version = st.session_state.api_version
    openai.api_key = options['key']
    return
