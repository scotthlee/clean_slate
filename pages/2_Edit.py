"""Streamlit app for evaluating web content generated by an LLM."""
import streamlit as st
import streamlit.components.v1 as components
import openai
import json
import platform
import os
import io

from tools import html, generic, strml
from tools.strml import update_settings, save_text, reset_gpt


def update_cci_choices():
    pass


def score_by_cci(GPT=True):
    if st.session_state._cci_choices == []:
        st.error('Please choose Question Types before scoring.')
        return
    type_lookup = {
        'All': 'all',
        'Required': 'required',
        'Facts and figures': 'numbers',
        'Behavioral content': 'behavioral',
        'Risk-related content': 'risk'
    }
    question_types = [type_lookup[t] for t in st.session_state._cci_choices]
    strml.keep('cci_choices')
    rubric = []
    if 'All' not in question_types:
        rubric.append(cci_dict['instructions'])
        for question_type in question_types:
            rubric.append(cci_dict[question_type])
    else:
        rubric.append(cci_dict['all'])
    rubric = ' '.join(rubric)
    if not GPT:
        res = rubric
    else:
        draft = 'Content: (' + st.session_state.saved_text + ')\n'
        rubric = 'Rubric: (' + rubric + ')'
        prompt = 'Score the following content using the rubric that follows. \
        Do not change the questions in the rubric.\n'
        prompt = prompt + draft + rubric
        message_text = [
            {"role":"system","content": st.session_state.gpt_persona},
            {"role":"user","content": prompt},
        ]
        try:
            completion = openai.ChatCompletion.create(
                engine=st.session_state.engine,
                messages=message_text,
                temperature=st.session_state.temperature,
                max_tokens=st.session_state.max_tokens,
                top_p=st.session_state.top_p,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None
            )
            res = completion['choices'][0]['message']['content']
        except:
            res = ''
            st.error('OpenAI API currently unavailable.')
    st.session_state.cci_report = res
    strml.keep('cci_report')
    return


def clear_cci_report():
    st.session_state.cci_report = st.session_state.cci_default
    return


def score_by_vt():
    to_edit = st.session_state._vt_edit_choices
    all_choices = st.session_state._vt_id_choices
    [all_choices.append(c) for c in to_edit]
    prompt = 'Check the following text for these grammatical errors: '
    prompt += ', '.join(all_choices) + '. '
    prompt += 'If you find an error, please italicize it using markdown syntax ex: _error_. If the error is\
    one of these--' + ', '.join(to_edit) + '--please also suggest \
    alternative wording italicized in parentheses immediately after the error. ex: (_alternative_)'
    prompt += 'Text: \n\n' + st.session_state.saved_text
    message_text = [
        {"role": "system", "content": st.session_state.gpt_persona},
        {"role": "user", "content": prompt},
    ]
    try:
        completion = openai.ChatCompletion.create(
            engine=st.session_state.engine,
            messages=message_text,
            temperature=st.session_state.temperature,
            max_tokens=st.session_state.max_tokens,
            top_p=st.session_state.top_p,
            frequency_penalty=st.session_state.frequency_penalty,
            presence_penalty=st.session_state.presence_penalty,
            stop=None
        )
        res = completion['choices'][0]['message']['content']
        st.session_state._vt_report = res
    except:
        res = ''
        st.error('OpenAI API is currently unavailable.')
    return


def save_vt_suggestions():
    pass


def update_draft():
    st.session_state.saved_text = st.session_state._vt_report
    return


def save_vt_report(fpath='data/output/vt_report.txt'):
    out = st.session_state._vt_report
    with open(fpath, 'w') as f:
        f.write(out)
        f.close()
    return


def clear_vt_report():
    st.session_state._vt_report = ''
    return


def load_from_file():
    if st.session_state._file_loader is not None:
        bytes = st.session_state._file_loader.getvalue()
        new_text = bytes.decode('utf-8')
        st.session_state.saved_text = new_text
    return


def load_from_generator():
    try:
        st.session_state.saved_text = st.session_state.response
    except:
        st.error('No model-generated content to load.')
    return


def update_markdown():
    st.session_state.saved_text = st.session_state._edited_text
    st.toast('Markdown updated!', icon='👍')
    return


# Load the config; should probably only be done once and added to session_state
config = json.load(open('data/app_config.json', 'r'))
cci_dict = json.load(open('data/cci/cci.json', 'r'))

# Setting up the OpenAI API
strml.load_openai_settings()

# Set up the page
st.set_page_config(layout='wide', page_title='Edit', page_icon='✂')
st.title('Content Editor')

if not st.session_state.authentication_status:
    st.error('Please log in at the Welcome Page to continue.')
else:
    # Set up options and help for the editing tools
    if 'vt_options' not in st.session_state:
        st.session_state.vt_options = [
            'Passive voice', 'Long sentences', 'Long words',
            'Hidden (nominalized) verbs', 'Grammatical errors',
            'Adverbs', ''
    ]
    if 'vt_edit_help' not in st.session_state:
        st.session_state.vt_edit_help = "Choose which elements you'd like the model\
        to both flag and change."
    if 'vt_id_help' not in st.session_state:
        st.session_state.vt_id_help = "Choose which elements you'd like the model\
        to flag (but not change)."
    if 'cci_options' not in st.session_state:
        st.session_state.cci_options = [
            'All', 'Required', 'Behavioral content',
            'Facts and figures', 'Risk-related content'
    ]

    # Loading previously-generated content
    TO_RELOAD = [
        'vt_edit_choices', 'vt_id_choices', 'vt_report'
    ]
    for key in TO_RELOAD:
        if key in st.session_state:
            strml.unkeep(key)

    # Filling in the sidebar widgets
    with st.sidebar:
        st.write('Settings')
        with st.expander('Content Controls', expanded=True):
            io_cols = st.columns(2)
            with io_cols[1]:
                st.write('')
                st.write('')
                save_button = st.download_button(
                    label='Save Draft',
                    data=st.session_state["saved_text"],
                    file_name=st.session_state["edit_draft_filename"] + ".md",
                    mime="text/markdown"
                )
            with io_cols[0]:
                save_name = st.text_input(label='File Name',
                                          value=st.session_state.edit_draft_filename,
                                          placeholder='Enter a filename here.',
                                          on_change=update_settings,
                                          key='_edit_draft_filename',
                                          kwargs={'keys': ['edit_draft_filename']})
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

    # Fill in the page elements, starting with the left pane
    left_pane, right_pane = st.columns(2)
    with left_pane:
        # Adding the load and save functions
        with st.expander('Load', expanded=True):
            load_file = st.file_uploader('From File',
                                         type=['txt'],
                                         key='_file_loader',
                                         accept_multiple_files=False,
                                         on_change=load_from_file,
                                         help='Load an existing page from disk.\
                                         Pages must be in raw text \
                                         (.txt) format.')
            st.button(label='From Generator',
                      help='Load text from the generator page.',
                      on_click=load_from_generator)

        st.write('Tools')
        # Adding the Clear Communication Index scoring tool
        cci_exp = st.expander(label='🧾📐 Clear Communication Index',
                              expanded=True)
        with cci_exp:
            cci_choice = st.multiselect(label='Question Types',
                                        key='_cci_choices',
                                        placeholder='Choose questions from the CCI\
                                        score sheet for evaluating the content.',
                                        options=st.session_state.cci_options,
                                        on_change=update_cci_choices)
            cci_cols = st.columns(5)
            with cci_cols[0]:
                st.button(label="Score Content",
                          key='cci_score',
                          on_click=score_by_cci)
            with cci_cols[1]:
                cci_clear = st.button(label='Clear Report',
                                      key='cci_clear',
                                      on_click=clear_cci_report)
            with cci_cols[2]:
                st.download_button(label='Save Report',
                                   key='_cci_save',
                                   data=st.session_state.cci_report,
                                   file_name='cci_report.txt',
                                   mime="text/markdown")
            cci_score = st.text_area(label='Score Report',
                                     key='_cci_report',
                                     value=st.session_state.cci_report,
                                     height=500)

        # Adding the Visible Thread-like tool
        vt_exp = st.expander(label='🔎🧵 Visible Thread',
                             expanded=False)
        with vt_exp:
            vt_edit = st.multiselect(label='Edit',
                                     key='_vt_edit_choices',
                                     help=st.session_state.vt_edit_help,
                                     options=st.session_state.vt_options)
            vt_id = st.multiselect(label='Identify',
                                   key='_vt_id_choices',
                                   help=st.session_state.vt_id_help,
                                   options=st.session_state.vt_options)
            vt_cols = st.columns(5)
            with vt_cols[0]:
                st.button(label='Score Content',
                          on_click=score_by_vt)
            with vt_cols[1]:
                st.button(label='Update Draft',
                          on_click=update_draft)
            with vt_cols[2]:
                st.button(label='Save Report',
                          on_click=save_vt_report)
            with vt_cols[3]:
                st.button(label='Clear Report',
                          on_click=clear_vt_report)

            vt_draft = st.text_area(label='Report',
                                    key='_vt_report',
                                    height=500,
                                    placeholder='Choose some plain language\
                                    elements from the Edit or Identify menus\
                                    to get started.')

    with right_pane:
        st.write('Content')
        ed_text = st.text_area(label='Content',
                               key='_saved_text',
                               on_change=update_settings,
                               kwargs={'keys': ['saved_text'],
                                       'toast': False},
                               value=st.session_state.saved_text,
                               label_visibility='collapsed',
                               height=1000)
