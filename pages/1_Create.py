"""Streamlit app for editing web pages with an LLM."""
import streamlit as st
import streamlit.components.v1 as components
import json
import platform
import os
import sys
import urllib
import openai
import tiktoken

from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
from trubrics.integrations.streamlit import FeedbackCollector


from tools import html, generic, strml
from tools.strml import update_settings, save_text, reset_gpt


def update_page_soup(encoding="utf-8"):
    global TEMP_HTML_DIR

    template_name = st.session_state._template_choice
    fpath = TEMP_HTML_DIR + template_name + '.html'

    with open(fpath, "r", encoding=encoding) as file:
        st.session_state._page_soup = bs(file, features='html.parser')

def update_prompt(strip_option=True):
    keep_heads = st.session_state._select_sections

    if keep_heads == []:
        keep_heads = st.session_state.section_options
        strip_option = False
    
    st.session_state.page_soup = html.keep_sections(
        st.session_state._page_soup,
        section_names=keep_heads
    )

    st.session_state._template_text = html.generate_prompt(soup=st.session_state.page_soup,
                                                           strip_option=strip_option)
    keys = ['template_choice', 'template_text', 'sections']
    kept = [strml.keep(key) for key in keys]
    return

def update_sections():
    update_page_soup()
    temp_headers = html.list_headers(st.session_state._page_soup)
    st.session_state.section_options = temp_headers[0]
    st.session_state.sections = temp_headers[0]
    strml.keep('template_choice')
    if st.session_state._select_sections == []:
        update_prompt(strip_option=False)

    return


def update_rag():
    pass


def prompt_model():
    inst_text = st.session_state.user_instructions
    temp_text = st.session_state.template_text
    context_text = 'When writing, please base your answer on the following\
    information:\nContext: (' + st.session_state.context + ')\n'
    input = inst_text + context_text + '\n\n' + temp_text
    st.session_state._response = start_generation(input)
    keys = ['user_instructions', 'template_text', 'response']
    kept = [strml.keep(key) for key in keys]
    st.session_state.saved_text = st.session_state.response
    return


def start_generation(s, GPT=True):
    if LOGGING:
        st.session_state.logged_prompt = collector.log_prompt(
            config_model={"model": st.session_state.model_name},
            prompt=st.session_state._template_text,
            generation=s,
        )
    with st.spinner('Generating Text...'):
        if GPT:
            try:
                message = [
                    {"role": "system", "content": st.session_state.gpt_persona},
                    {"role": "user", "content": s},
                ]
                completion = openai.ChatCompletion.create(
                    engine=st.session_state.engine,
                    messages=message,
                    temperature=st.session_state.temperature,
                    max_tokens=st.session_state.max_tokens,
                    top_p=st.session_state.top_p,
                    frequency_penalty=st.session_state.frequency_penalty,
                    presence_penalty=st.session_state.presence_penalty,
                    stop=None
                )
                res = completion['choices'][0]['message']['content']
            except:
                st.error('OpenAI API currently unavailable. Please try again.')
                res = s
        else:
            res = s
    return res


def erase_response():
    st.session_state.response = 'Click "Go" to prompt the model'
    return


def stop_generation():
    st.session_state.response = st.session_state.response
    st.stop()
    return


def add_context_page(page_type='file',
                     header_levels=['h1', 'h2', 'h3', 'h4', 'p']):
    context = []
    if page_type == 'url':
        if st.session_state._context_urls is not None:
            to_load = st.session_state._context_urls.split('\n')
            for url in to_load:
                if url not in st.session_state.context_list:
                    page = bs(urlopen(url), features='html.parser')
                    st.session_state.context_list += url + '\n'
                    chunks = [html.fetch_section(page, search_tag=h)[0]
                              for h in header_levels]
                    context.append(''.join(set(chunks)))
    else:
        if st.session_state._context_pages is not None:
            files = st.session_state._context_pages
            for f in files:
                page_name = f.name
                if page_name not in st.session_state.context_list:
                    st.session_state.context_list += f.name + '\n'
                    page = bs(f, features='html.parser')
                    chunks = [html.fetch_section(page, search_tag=h)[0]
                              for h in header_levels]
                    context.append(''.join(set(chunks)))
    st.session_state.context +=  '\n'.join(context)
    return


def clear_context():
    st.session_state.context = ''
    st.session_state.context_list = ''
    st.toast('Context pages cleared!', icon='🧹')
    return


def update_instructions():
    strml.keep('user_instructions')
    return


def suggest_template():
    options = '\n'.join(st.session_state.template_options)
    options = options.replace('_', ' ')
    temp_descr = st.session_state._temp_suggest_description
    prompt = "I'm working on a website. "
    if temp_descr != '':
        prompt += "Here's a brief description of it: "
        prompt += temp_descr
    if st.session_state.suggest_with_context:
        prompt += "\n If it helps, here's some existing content that I'm going\
        to base the new page on: " + st.session_state.context
    prompt += "\n\n Based on their names, which of these page types do you \
    think would be a good fit for my page? Types: ["
    prompt += options + ']'
    message = [{"role": "system", "content": st.session_state.gpt_persona},
                {"role": "user", "content": prompt}]
    try:
        completion = openai.ChatCompletion.create(
            engine=st.session_state.engine,
            messages=message,
            temperature=st.session_state.temperature,
            max_tokens=st.session_state.max_tokens,
            top_p=st.session_state.top_p,
            frequency_penalty=st.session_state.frequency_penalty,
            presence_penalty=st.session_state.presence_penalty,
            stop=None
        )
        res = completion['choices'][0]['message']['content']
    except openai.error.PermissionError as e:
        res = ''
        st.error('OpenAI API currently unavailable.')
        print(e)
        # raise
    st.session_state.gpt_temp_suggestion = res
    return


# Deciding whether to accept user feedback
LOGGING = False

# Load the config file
config = json.load(open('data/app_config.json', 'r'))

# Setting up the OpenAI API
strml.load_openai_settings()

# Setting a default prompt to use
TEMP_HTML_DIR = 'data/websites/templates/html/'

# Call only on init
if '_template_choice' not in st.session_state:
    st.session_state._template_choice = 'about'
    update_page_soup()

    default_headers, default_header_idx = html.list_headers(st.session_state._page_soup)

# Setting default text in textbox
# (if you set by value and then update, it throws a warning for some reason)
if "_response" not in st.session_state:
    st.session_state["_response"] = 'Click "Start" to prompt the model.'

# Set up the page
st.set_page_config(page_title='Create', layout='wide', page_icon='✨')
st.title('Content Generator')

if not st.session_state.authentication_status:
    st.error('Please log in at the Welcome Page to continue.')
else:
    # Adding autosave
    if st.session_state.autosave:
        save_text(toast=False)

    # Loading previously-generated content
    TO_RELOAD = [
        'response', 'sections', 'template_text',
        'template_choice', 'user_instructions', 'draft_file_name',
        'context_pages'
    ]
    for key in TO_RELOAD:
        if key in st.session_state:
            strml.unkeep(key)

    # Add a few things to session state
    if 'section_options' not in st.session_state:
        st.session_state.section_options = default_headers

    # Set up the feedback collector; not currently working
    if LOGGING:
        collector = FeedbackCollector(
            email="yle4@cdc.gov",
            password=os.environ[TRUBRICS_PASSWORD],
            project="clean_slate"
        )

    # Adding the sidebar widgets
    with st.sidebar:
        st.write('Settings')
        as_toggle = st.toggle('Autosave',
                              disabled=True,
                              value=st.session_state.autosave,
                              on_change=update_settings,
                              kwargs={'keys': ['autosave']},
                              key='_autosave')
        rag_toggle = st.toggle('Use RAG',
                               value=st.session_state.use_rag,
                               key='_use_rag',
                               disabled=True,
                               kwargs={'keys': ['use_rag']},
                               on_change=update_settings)
        with st.expander('Content Controls', expanded=True):
            io_cols = st.columns(2)
            with io_cols[1]:
                st.write('')
                st.write('')
                save_button = st.button(label='Save Draft',
                                        type='secondary',
                                        on_click=save_text,
                                        kwargs={'file_dir':
                                            st.session_state.working_directory})
            with io_cols[0]:
                save_name = st.text_input(label='File Name',
                                          value=st.session_state.create_draft_filename,
                                          placeholder='Enter a filename here.',
                                          on_change=update_settings,
                                          key='_create_draft_filename',
                                          kwargs={'keys': ['create_draft_filename']})
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

    # Fill in the elements
    left_pane, right_pane = st.columns(2)
    with left_pane:
        with st.expander(f'**Step 1**: Load Existing Pages (Optional)'):
            load_file = st.file_uploader(label='From Disk',
                                         type=['html'],
                                         accept_multiple_files=True,
                                         on_change=add_context_page,
                                         key='_context_pages',
                                         help='Load an existing page or pages\
                                         from disk. Pages must be in HTML (.html)\
                                         format.')
            load_web = st.text_area(label='Or From URL',
                                    key='_context_urls',
                                    kwargs={'page_type': 'url',
                                            'header_levels': ['p']},
                                    on_change=add_context_page,
                                    help='Add URLs for web pages you would\
                                    like to load. Make sure each URL is on\
                                    its own line.')
            context_list = st.text_area(label='Pages in Current Context',
                                        help='These are the pages the model\
                                        will use as context when generating\
                                        new content.',
                                        value=st.session_state.context_list,
                                        key='_context_list')
            st.button('Clear Context Pages',
                      help='Clears the current set of pages used as context for\
                      the prompt',
                      on_click=clear_context)

        suggest_exp = st.expander(label=f'**Step 2**: Get a Template Suggestion\
                                   (Optional)')
        with suggest_exp:
            suggest_with_context = st.toggle(label='Use existing pages',
                                             key='_suggest_with_context',
                                             value=st.session_state.suggest_with_context,
                                             on_change=update_settings,
                                             kwargs={'keys': ['suggest_with_context']},
                                             help="Use pages you've uploaded to \
                                             help ChatGPT recommend templates for \
                                             your project. Load some pages using\
                                             the 'Load' menu above to get started.")
            sugg_cols = st.columns(2)
            with sugg_cols[0]:
                temp_suggest = st.text_input(label='Web Page Description',
                                             key='_temp_suggest_description',
                                             help="Write a brief description of\
                                             the page you'd like to create.")
            with sugg_cols[1]:
                st.write('')
                st.write('')
                st.button('Get Suggestion',
                          on_click=suggest_template,
                          help='Ask ChatGPT to suggest a few templates.')
            suggestion_text = st.text_area(label="Suggested Templates",
                                           key='_gpt_temp_suggestion',
                                           on_change=update_settings,
                                           kwargs={'keys': ['gpt_temp_suggestion'],
                                                   'toast': False},
                                           value=st.session_state.gpt_temp_suggestion)

        temp_exp = st.expander(label=f'**Step 3**: Choose a Template',
                               expanded=True)
        with temp_exp:
            template_choice = st.selectbox(label='Template Choices',
                                           key='_template_choice',
                                           options=st.session_state.template_options,
                                           placeholder='Choose a content template',
                                           help=st.session_state.template_help,
                                           on_change=update_sections)
            header_choce = st.multiselect(label='Template Sections',
                                          key='_select_sections',
                                          options=st.session_state.section_options,
                                          placeholder='What sections would you like to keep?',
                                          help=st.session_state.section_help,
                                          on_change=update_prompt)

        prompt_exp = st.expander(label=f'**Step 4**: Write the Prompt',
                                 expanded=True)
        with prompt_exp:
            prompt_box = st.text_area(label='Model Instructions',
                                      height=200,
                                      value='',
                                      placeholder=st.session_state.example_instructions,
                                      key='_user_instructions',
                                      on_change=update_instructions,
                                      help=st.session_state.prompt_help)
            template_box = st.text_area(label='Template Text',
                                        height=500,
                                        placeholder='Please choose a template and headers.',
                                        help=st.session_state.template_help,
                                        key='_template_text')

    with right_pane:
        st.write(f'**Step 5**: Generate Content')
        go_cols = st.columns(6)
        with go_cols[0]:
            go_button = st.button(label='Start',
                                  key='go_button',
                                  type='primary',
                                  help='Starts text generation.',
                                  on_click=prompt_model)
        with go_cols[1]:
            stop_button = st.button(label='Stop',
                                    help='Stops text generation.',
                                    key='stop_button',
                                    type='secondary')
        with go_cols[2]:
            clear_button = st.button(label='Clear',
                                     key='clear_button',
                                     type='secondary',
                                     help='Clears generated content.',
                                     on_click=erase_response)

        st.write('Content')
        response_box = st.text_area(label='Model Response',
                                    height=700,
                                    key='_response',
                                    label_visibility='collapsed')
