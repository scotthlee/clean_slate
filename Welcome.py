import streamlit as st
import streamlit_authenticator as stauth
import json
import os
import yaml
from dotenv import load_dotenv
load_dotenv()
from yaml.loader import SafeLoader

from tools.strml import update_settings


# Load the config file
config = json.load(open('data/app_config.json', 'r'))

# Set up the page
st.set_page_config(page_title='Welcome', page_icon='👋')
st.write("# Welcome to the Web Content Editor!")

# Load the credentials
creds = yaml.load(open('data/auth.yaml', 'r').read(), Loader=SafeLoader)
#authenticator = stauth.Authenticate(
    #creds['credentials'],
    #creds['cookie']['name'],
    #creds['cookie']['key'],
    #creds['cookie']['expiry_days'],
    #creds['preauthorized']
#)
#name, authentication_status, username = authenticator.login('Login', 'main')

# Processing the login
st.session_state.authentication_status = True
if st.session_state["authentication_status"]:
    pass
    #st.write('')
    #st.write('Ready to leave?')
    #authenticator.logout('Logout', 'main')
elif st.session_state["authentication_status"] == False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] == None:
    st.warning('Please enter your username and password')

# Assigning defaults for the settings menu
if 'draft_chat' not in st.session_state:
    st.session_state.draft_chat = False
if 'saved_text' not in st.session_state:
    m = 'Use the generator on the Create page to draft some content.'
    st.session_state.saved_text = m
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'draft_file_name' not in st.session_state:
    st.session_state.draft_file_name = 'draft'
if 'draft_file_type' not in st.session_state:
    st.session_state.draft_file_type = '.txt'

# Defaults for the creation page
if 'template_options' not in st.session_state:
    st.session_state.template_options = list(config['templates'].keys())
if 'prompt_help' not in st.session_state:
    st.session_state.prompt_help = "Enter any extra instructions you have for \
    the model here."
if 'template_help' not in st.session_state:
    st.session_state.template_help = "This is the template that will be passed \
    to the model, in addition to any extra instructions you supply above."
if 'web_help' not in st.session_state:
    st.session_state.web_help = "Choose CDC websites you'd like the model to be\
     able to 'search'. This is different from specifying an existing page you'd\
      like to modify directly."
if 'pub_help' not in st.session_state:
    st.session_state.pub_help = "Choose publications you'd like the model to be\
     able to 'search'."
if 'template_help' not in st.session_state:
    st.session_state.template_help = "Choose a content template for your site.\
     This will be passed to the model to fill out, along with any additional\
      instructions you provide in the 'Prompt Options' section below."
if 'section_help' not in st.session_state:
    st.session_state.section_help = "Choose which of the sections from the \
    selected content template you'd like to keep (the model will treat these\
    as required). Leave this section blank if you'd like the model itself to\
    decide which sections to keep."
if 'sections' not in st.session_state:
    st.session_state.sections = []
if 'logged_prompt' not in st.session_state:
    st.session_state.logged_prompt = None
if 'example_instructions' not in st.session_state:
    instructions = 'Example instructions for a page about risk factors for Type\
    2 diabetes:\n\n"Use information from the context below to fill out the\
    following template with information about risk factors for Type 2 diabetes.\
    The intended audience is the general public. Please adhere to Federal Plain\
    Language Guidelines when writing."\n\nNote that in this example, we asked\
    the model to use loaded context pages as the basis for its draft. If you\
    have not loaded context pages (i.e., if you want the model to generate\
    context from scratch), then leave that bit out of the instructions.'
    st.session_state.example_instructions = instructions.replace('  ', ' ')
if 'cci_default' not in st.session_state:
    st.session_state.cci_default = 'Select the question types and then click \
    "Score Content" to generate the report.'.replace('    ', ' ')
if 'cci_report' not in st.session_state:
    st.session_state.cci_report = st.session_state.cci_default

# Adding some states for the draft contexxtd and context pages
if 'edit_draft_filename' not in st.session_state:
    st.session_state.edit_draft_filename = 'draft'
if 'create_draft_filename' not in st.session_state:
    st.session_state.create_draft_filename = 'draft'
if 'context_list' not in st.session_state:
    st.session_state.context_list = ''
if 'context' not in st.session_state:
    st.session_state.context = ''

# Setting keys for changing settings from different menus
st.session_state.gpt_keys = [
    'engine', 'max_tokens', 'top_p',
    'temperature', 'frequency_penalty', 'presence_penalty'
]

gpt_defaults = {
    'engine': 'gpt-35-turbo',
    'max_tokens': None,
    'top_p': 0.95,
    'temperature': 0.70,
    'presence_penalty': 0.0,
    'frequency_penalty': 0.0
}
st.session_state.gpt_defaults = gpt_defaults
gpt_dict = {
    'gpt-35-turbo': {
        'engine': 'GPT35-Turbo-0613',
        'url': os.environ['GPT35_URL'],
        'key': os.environ['GPT35_API_KEY']
    },
    'gpt-4-turbo': {
        'engine': 'edav-api-share-gpt4-128k-tpm25plus-v1106-dfilter',
        'url': os.environ['GPT4_URL'],
        'key': os.environ['GPT4_API_KEY']
    }
}

st.session_state.gpt_dict = gpt_dict

if 'model_name' not in st.session_state:
    st.session_state.model_name = gpt_defaults['engine']
if 'engine' not in st.session_state:
    st.session_state.engine = gpt_dict[st.session_state.model_name]['engine']
if 'engine_choices' not in st.session_state:
    st.session_state.engine_choices = list(gpt_dict.keys())
if 'api_type' not in st.session_state:
    st.session_state.api_type = 'azure'
if 'api_version' not in st.session_state:
    st.session_state.api_version = '2023-07-01-preview'
if 'api_key' not in st.session_state:
    st.session_state.api_key = gpt_dict[st.session_state.model_name]['key']
if 'base_url' not in st.session_state:
    st.session_state.base_url = gpt_dict[st.session_state.model_name]['url']
if 'temperature' not in st.session_state:
    st.session_state.temperature = gpt_defaults['temperature']
if 'max_tokens' not in st.session_state:
    st.session_state.max_tokens = gpt_defaults['max_tokens']
if 'top_p' not in st.session_state:
    st.session_state.top_p = gpt_defaults['top_p']
if 'presence_penalty' not in st.session_state:
    st.session_state.presence_penalty = gpt_defaults['presence_penalty']
if 'frequency_penalty' not in st.session_state:
    st.session_state.frequency_penalty = gpt_defaults['frequency_penalty']

if 'gpt_persona' not in st.session_state:
    st.session_state.gpt_persona = "You are an AI assistant that helps people\
    find information."
if 'gpt_temp_suggestion' not in st.session_state:
    st.session_state.gpt_temp_suggestion = ''
if 'suggest_with_context' not in st.session_state:
    st.session_state.suggest_with_context = True
if 'old_messages' not in st.session_state:
    st.session_state.old_messages = ''
