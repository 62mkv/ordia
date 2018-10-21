"""views."""


import json
import re

from flask import (Blueprint, current_app, redirect, render_template, request,
                   url_for)
from werkzeug.routing import BaseConverter

from ..api import wb_search_lexeme_entities
from ..query import iso639_to_q


class RegexConverter(BaseConverter):
    """Converter for regular expression routes.

    References
    ----------
    https://stackoverflow.com/questions/5870188

    """

    def __init__(self, url_map, *items):
        """Set up regular expression matcher."""
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


def add_app_url_map_converter(self, func, name=None):
    """Register a custom URL map converters, available application wide.

    References
    ----------
    https://coderwall.com/p/gnafxa/adding-custom-url-map-converters-to-flask-blueprint-objects

    """
    def register_converter(state):
        state.app.url_map.converters[name or func.__name__] = func

    self.record_once(register_converter)


Blueprint.add_app_url_map_converter = add_app_url_map_converter
main = Blueprint('app', __name__)
main.add_app_url_map_converter(RegexConverter, 'regex')


# Wikidata item identifier matcher
q_pattern = '<regex("Q[1-9]\d*"):q>'
l_pattern = '<regex("L[1-9]\d*"):l>'
f_pattern = '<regex("F[1-9]\d*"):f>'
s_pattern = '<regex("S[1-9]\d*"):s>'
p_pattern = '<regex("P[1-9]\d*"):p>'
iso_language_pattern = """\
<regex("[a-z]{2,3}"):language>"""
q_language_pattern = """\
<regex("(Q[1-9]\d*)|([a-z]{2,3}((-[a-z]{2})|(-x-Q[1-9]\d*)))"):q>"""

Q_PATTERN = re.compile(r'Q[1-9]\d*')
L_PATTERN = re.compile(r'L[1-9]\d*')
S_PATTERN = re.compile(r'S[1-9]\d*')
P_PATTERN = re.compile(r'P[1-9]\d*')


@main.route("/")
def index():
    """Return rendered index page.

    Returns
    -------
    html : str
        Rederende HTML for index page.

    """
    return render_template('index.html')


@main.route("/" + l_pattern)
def show_l(l):
    """Render webpage for l Wikidata item.

    Parameters
    ----------
    l : str
        Wikidata lexeme item identifier

    """
    print('Hallo')
    entity = current_app.base.entities.get(l)
    formatted_entity = json.dumps(entity, indent=2)
    return render_template("l.html", l=l, entity=entity,
                           formatted_entity=formatted_entity)


@main.route("/grammatical-feature/")
def show_grammatical_feature_index():
    """Render webpage for grammatical feature index page."""
    grammatical_features = current_app.base.grammatical_feature_index.keys()
    return render_template("grammatical_feature_index.html",
                           grammatical_features=grammatical_features)


@main.route("/language/" + iso_language_pattern)
def redirect_language(language):
    """Redirect from ISO language code.

    Parameters
    ----------
    language : str
        ISO language identifier as a string

    Returns
    -------
    reponse : werkzeug.wrappers.Response
        Redirect

    """
    q = iso639_to_q(language)
    if q:
        return redirect(url_for('app.show_language', q=q), code=302)
    return render_template('404.html')


@main.route("/language/" + q_language_pattern)
def show_language(q):
    """Render webpage for language.

    Parameters
    ----------
    q : str
        Wikidata item for the language.

    """
    print('show_language')
    if q.startswith('Q'):
        return render_template("language.html", q=q)
    else:
        q = q.split('-')[-1]
        return redirect(url_for('app.show_language', q=q), code=302)


@main.route("/language/")
def show_language_index():
    """Render index webpage for language."""
    return render_template("language_index.html")


@main.route("/lexical-category/")
def show_lexical_category_index():
    """Render webpage for lexical_category index page."""
    lexical_category_counts = current_app.base.lexical_category_counts
    return render_template("lexical_category_index.html",
                           lexical_category_counts=lexical_category_counts)


@main.route("/" + l_pattern + "-" + f_pattern)
def show_lf(l, f):
    """Render webpage for l-f Wikidata item.

    Parameters
    ----------
    l : str
        Wikidata lexeme form item identifier
    f : str
        Wikidata lexeme form identifier

    """
    entity = current_app.base.entities.get(l)
    for form in entity['forms']:
        if form['id'] == l + '-' + f:
            break
    else:
        form = {}
    return render_template("lf.html", l=l, f=f, form=form)


@main.route("/" + l_pattern + "-" + s_pattern)
def show_ls(l, s):
    """Render webpage for l-s Wikidata item.

    Parameters
    ----------
    l : str
        Wikidata lexeme form item identifier
    s : str
        Wikidata lexeme sense identifier

    """
    return render_template("ls.html", l=l, s=s)


@main.route("/" + q_pattern)
def show_q(q):
    """Render webpage for q Wikidata item.

    Parameters
    ----------
    q : str
        Wikidata item identifier

    """
    return render_template("q.html", q=q)


@main.route("/search")
def show_search():
    """Render webpage for q Wikidata item.

    Parameters
    ----------
    q : str
        Wikidata item identifier

    """
    query = request.args.get('q', '')
    if query:
        # As the cache in the `base` is not updated currently,
        # it may be better to search with the API.
        # Alternatively, the two results could be intertwined.
        # search_results = current_app.base.search(query)

        search_results = wb_search_lexeme_entities(query)
    else:
        search_results = []
    return render_template("search.html",
                           query=query, search_results=search_results)
