"""Updates content templates."""
import json
import ssl

from bs4 import BeautifulSoup as bs
from urllib.request import urlopen


ssl._create_default_https_context = ssl._create_unverified_context
templates = json.load(open('data/app_config.json', 'r'))['templates']
template_names = list(templates.keys())
print('Pulling fresh content templates. Please wait...')
for template_name in template_names:
    try:
        url = templates[template_name]['url']
        page = bs(urlopen(url), features='html.parser')
        with open('data/websites/templates/html/' + template_name, 'w') as f:
            f.write(str(page))
            f.close()
    except:
        print(template_name + ' URL is currently unavailable.')
