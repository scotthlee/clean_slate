import streamlit as st
import streamlit.components.v1 as components
import json
import platform
import os
import urllib

from bs4 import BeautifulSoup as bs
#from transformers import AutoTokenizer, AutoModelForCausalLM
#from trubrics.integrations.streamlit import FeedbackCollector

from tools import html, generic


# Set up the page
st.set_page_config(layout='wide', page_title='View', page_icon='👓')
st.title('Web Page Preview')
st.header('', divider='rainbow')

if 'saved_text' not in st.session_state:
    st.markdown('')
else:
    mkd_display = st.markdown(st.session_state.saved_text)
