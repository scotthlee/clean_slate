"""Functions for converting HTML pages to text."""
import numpy as np
import pandas as pd
import urllib
import re

from bs4 import BeautifulSoup as bs
from html2text import HTML2Text
from copy import deepcopy


def strip_returns(s):
    """Strips extra new lines from a string."""
    s = s.replace('\n\n\n\n\n', '\n\n')
    s = s.replace('\n\n\n\n', '\n\n')
    s = s.replace('\n\n\n', '\n\n')
    s = s.replace('\n\n  ', '\n\n')
    s = s.replace('\n\n ', '\n\n')
    s = s.replace('\n ', '\n')
    return s


def strip_formatting(s):
    """Strips newlines and hashtags."""
    s = s.replace('\n', ' ')
    s = s.replace('#', '')
    return s


def combine_sections():
    regex = re.compile

def paragraphs(d, strip_new=True, min_length=50):
    """Saves text information from a file."""
    out = [p.text for p in d.find_all('p')]
    if strip_new:
        out = [d.replace('\n', '') for d in out]
        out = [d for d in out if len(d) >= min_length]
    return out


def dump(page,
         fname,
         fdir,
         ftype='.txt',
         split_str=' ',
         strip_new=True,
         min_length=50):
    """Dumps a page's text content to file."""
    page_text = paragraphs(bs(page), strip_new, min_length)
    page_text = split_str.join(page_text)
    with open(fdir + fname + ftype, 'w') as f:
        f.write(page_text)
    return


def list_headers(s):
    """Lists the sections of a content template."""
    h2s = s.find_all('h2')
    headers = [h.text for h in h2s]
    header_dict = dict(zip(headers,
                           np.arange(len(headers))))
    return headers, header_dict


def keep_sections(soup,
                  section_names=None,
                  section_idx=None):
    """Keeps only the selected sections of a content template."""
    s2 = deepcopy(soup)
    all_headers = s2.find_all('h2')
    all_names = [h.text for h in all_headers]
    max_headers = np.arange(len(all_names))
    header_dict = dict(zip(all_names, max_headers))
    if not section_idx:
        assert section_names is not None
        section_idx = [header_dict[n] for n in section_names]
    drop_idx = np.setdiff1d(max_headers, section_idx)
    for id in drop_idx:
        all_headers[id].decompose()
    return s2


def fetch_guidance(soup,
                   div_id='accordion-1',
                   block_num=0,
                   strip=False,
                   prepend='## '):
    """Fetches the template guidance from a content template."""
    h = HTML2Text()
    h.ignore_links = True
    guidance = soup.find_all('div', {'id': div_id})[block_num]
    if strip:
        guidance = guidance.extract()
    guidance = h.handle(str(guidance))
    return prepend + guidance


def fetch_key_card(soup,
                   search_tag='div',
                   class_='card border-0 rounded-0 mb-3',
                   card_num=0):
    """Fetches the main page blurb from a content template."""
    h = HTML2Text()
    h.ignore_links = True
    card = soup.find_all(search_tag, class_=class_)[card_num]
    card_text = h.handle(str(card))
    return '## ' + card_text


def fetch_section(soup,
                  section=None,
                  search_text=None,
                  tag_id=0,
                  search_tag='h2',
                  stop_tag=None,
                  strip=False,
                  join=True,
                  join_str='\n'):
    """Fetches a single section from a content template."""
    h = HTML2Text()
    h.ignore_links = True
    if not stop_tag:
        stop_tag = search_tag
    if not section:
        candidates = soup.find_all(search_tag)
        if search_text:
            candidates = [c for c in candidates
                          if search_text in c.text]
        out = [fetch_section(soup=soup,
                             section=c,
                             search_text=None,
                             tag_id=tag_id,
                             search_tag=search_tag,
                             stop_tag=stop_tag,
                             strip=strip,
                             join=join,
                             join_str=' ')
               for c in candidates]
        section_text = [s[0] for s in out]
        section = [s[1] for s in out]
        if join:
            section_text = '\n\n'.join(section_text)
    else:
        #section_text = [section.text]
        section_text = [h.handle(str(section))]
        for sib in section.find_next_siblings():
            if sib.name == stop_tag:
                break
            else:
                section_text.append(sib.text)
        if strip:
            section = section.extract()
        if join:
            section_text = join_str.join(section_text)
    return section_text, section


def fetch_callout(soup,
                  search_tag='em',
                  search_text='callout',
                  strip=False,
                  join=True,
                  join_str=' ',
                  replace_h2=True):
    """Fetches the optional callout from a content template."""
    h = HTML2Text()
    h.ignore_links = True
    preview = soup.find(search_tag)
    if (preview is None) or (search_text not in preview.text):
        return
    parent_section = preview.parent.parent
    callout_block = parent_section.next_sibling
    block = fetch_section(soup=soup,
                          section=callout_block,
                          stop_tag='div',
                          strip=strip)[0]
    preview_text = h.handle(str(preview)) + '\n'
    if replace_h2:
        preview_text = preview_text.replace('under any H2s',
                                            'in any section')
    callout = '## ' + block
    return callout


def fetch_title(soup):
    """Fetches the page title from a content template."""
    h = HTML2Text()
    h.ignore_links = True
    title = h.handle(str(soup.title))
    title = '## Page title : ' + title
    return title


def generate_prompt(soup, join_str='\n\n', strip_option=True):
    """Generates a text prompt from a content template."""
    key_card = fetch_key_card(soup)
    guidance = fetch_guidance(soup)
    callout = fetch_callout(soup)
    sections = fetch_section(soup)[0]
    title = fetch_title(soup)
    prompt_list = [guidance, callout, title, key_card, sections]
    prompt = join_str.join([d for d in prompt_list if d is not None])
    prompt = strip_returns(prompt)
    if strip_option:
        prompt = prompt.replace('(optional)', '')
    return prompt


def open_page(url, soup=True):
    """Opens a webpage and returns it as either raw text or a BeautifulSoup
    soup file.
    """
    with urllib.request.urlopen(url) as f:
        page = f.read()
    if soup:
        page = bs(page)
    return page
