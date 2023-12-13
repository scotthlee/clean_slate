import streamlit as st
import openai
import os


def keep(key):
    st.session_state[key] = st.session_state['_' + key]
    return


def unkeep(key):
    st.session_state['_' + key] = st.session_state[key]
    return


def update_settings(keys, toast=True):
    for key in keys:
        keep(key)
    if toast:
        st.toast('Settings updated!', icon='🔨')
    pass


def save_text(mode='create', file_dir='output/', toast=True):
    # Check that path exists; if not, create it
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    # Check for some basic fail points
    mode_message = "The 'mode' argument must either be 'create' or 'edit'."
    assert mode in ['create', 'edit'], mode_message
    err_mess = 'No draft to save. Please create some content by loading \
             a file or passing an empty content template to the model.'
    if 'saved_text' not in st.session_state:
        st.error(err_mess)
    elif st.session_state.saved_text == 'Click "Start" to prompt the model.':
        st.error(err_mess)
    else:
        fname = st.session_state[mode + '_draft_filename']
        fname += st.session_state.draft_file_type
        open(file_dir + fname, 'w').write(st.session_state.saved_text)
        if toast:
            st.toast('Text saved!', icon='💾')
    return


def reset_gpt():
    for key in st.session_state.gpt_keys:
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
