from jinja2 import Environment
from django.urls import reverse
from django.templatetags.static import static

def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'url_for': url_for,
    })
    return env

def url_for(endpoint, **kwargs):
    if endpoint == 'static':
        # Replicate Flask's url_for('static', filename='...')
        return static(kwargs.get('filename', ''))
    
    # Otherwise, attempt to reverse standard Django namespaced URLs
    return reverse(endpoint, kwargs=kwargs)
