#!/usr/bin/env python
"""
Some helper functions for generating html from python
"""

##################################################################

def _html_tag(tagname, *body, **attrs):
    """
    # A tag with a single argument
    >>> _html_tag('tr', 'test')
    '<tr >test</tr>'

    # Add attributes
    >>> _html_tag('tr', 'test', x='y')
    '<tr x="y">test</tr>'

    # With multiple arguments, we enclose each argument in its own
    # tag, newline separated
    >>> _html_tag('tr', 'test', 'test2', x='y')
    '<tr x="y">test</tr>\\n<tr x="y">test2</tr>'

    # If there is nothing to enclose, assume it's a single tag.
    >>> _html_tag('img', src='test')
    '<img src="test" />'
    """
    attr_str = ' '.join('{0}="{1}"'.format(k, v)
                        for (k, v) in attrs.iteritems())
    if len(body) > 0:
        return '\n'.join('<{0} {2}>{1}</{0}>'.
                         format(tagname, bod, attr_str)
                         for bod in body)
    else:
        return '<{0} {1} />'.format(tagname, attr_str)

# ----------------------------------------------------------------

table = lambda  s: _html_tag('table', s)
tr    = lambda *s: _html_tag('tr', *s)
th    = lambda *s: _html_tag('th', *s)
td    = lambda *s: _html_tag('td', *s)
href  = lambda link, body: _html_tag('a', body, href=link)

def html_table(header, rows):
    """
    @param header: a list of column names

    @param rows: a list of rows.  Each row should be a list with a
                 value for each column
    """
    return table('\n'.join((tr(th(*header)),
                            tr(*(td(*r) for r in rows)))))

##################################################################

def redirect_to(link):
    # http://stackoverflow.com/questions/5411538/how-to-redirect-from-html-page
    return """
<!DOCTYPE HTML>
<html lang="en-US">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="1;url={link}">
        <script type="text/javascript">
            window.location.href = "{link}"
        </script>
        <title>Page Redirection</title>
    </head>
    <body>
        <!-- Note: don't tell people to `click` the link, just tell them that it is a link. -->
        If you are not redirected automatically, go to <a href='{link}'>{link}</a>
    </body>
</html>
""".format(link=link)


##################################################################

if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)

