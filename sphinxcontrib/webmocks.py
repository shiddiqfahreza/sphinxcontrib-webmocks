# -*- coding: utf-8 -*-
"""
    sphinxcontrib.webmocks
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2012 by Takeshi KOMIYA
    :license: BSD, see LICENSE for details.
"""
import re
import uuid
from collections import OrderedDict

import docutils.utils
from docutils import nodes
from docutils.nodes import fully_normalize_name as normalize_name
from docutils.parsers import rst
from docutils.statemachine import ViewList
from sphinx.util.nodes import split_explicit_title


class MenuList(object):
    def __init__(self):
        self.menu = OrderedDict()

    def update(self, _dict):
        self.menu = _dict

    def keys(self):
        return self.menu.keys()

    def get(self, menu):
        return self.menu.get(menu)

    def add_menu(self, menu):
        if menu not in self.menu:
            self.menu[menu] = []

    def add_submenu(self, menu, submenu):
        self.add_menu(menu)
        self.menu[menu].append(submenu)


class MenuListDirective(rst.Directive):
    has_content = True

    def run(self):
        node = nodes.Element()
        self.state.nested_parse(self.content, self.content_offset, node)
        if isinstance(node[0], nodes.bullet_list):
            bullet = node[0]['bullet']
            parent = None
            for line in self.content:
                matched = re.match('^%s\s+(.*)' % re.escape(bullet), line)
                if matched:
                    parent = matched.group(1)
                    menulist.add_menu(parent)

                matched = re.match('^\s+%s\s+(.*)' % re.escape(bullet), line)
                if matched:
                    submenu = matched.group(1)
                    menulist.add_submenu(parent, submenu)

        return []


class PageDirective(rst.Directive):
    has_content = True
    optional_arguments = 1
    option_spec = {
        'breadcrumb': rst.directives.unchanged,
        'desctable': rst.directives.flag,
    }

    def run(self):
        content = self.build_screen_node()
        screen_node = self.build_menu_layout(content)
        node_list = [screen_node]

        if 'desctable' in self.options:
            desctable_node = self.build_desctable(content)
            if desctable_node:
                node_list.append(desctable_node)

        if self.arguments:
            title = " ".join(self.arguments)
            section_node = self.build_section_node(" ".join(self.arguments))
            section_node += node_list[0]
            node_list[0] = section_node

        return node_list

    def build_menu_layout(self, content):
        selected = self.selected_menu()

        # global navigation row
        menu = menulist.keys()
        tbody = nodes.tbody()

        if menu:
            p = nodes.paragraph()
            p += nodes.Text(menu[0])
            for label in menu[1:]:
                p += nodes.Text(' / ')
                p += nodes.Text(label)
            entry = nodes.entry()
            entry += p
            row = nodes.row()
            row += entry
            tbody += row

        # sub navigation row
        submenu = menulist.get(selected[0])

        if submenu:
            entry = nodes.entry()
            p = nodes.paragraph()
            p += nodes.Text(submenu[0])
            entry += p

            for label in submenu[1:]:
                p += nodes.Text(' / ')
                p += nodes.Text(label)

            row = nodes.row()
            row += entry
            tbody += row

        # content body row
        entry = nodes.entry()
        entry += content
        row = nodes.row()
        row += entry
        tbody += row

        tgroup = nodes.tgroup(cols=2)
        tgroup += nodes.colspec(colwidth=15)
        tgroup += nodes.colspec(colwidth=85)
        tgroup += tbody

        table = nodes.table()
        table += tgroup

        return table

    def build_screen_node(self):
        container = nodes.container()
        if self.options.get('breadcrumb'):
            container += self.build_breadcrumb_node()

        self.state.nested_parse(self.content, self.content_offset, container)
        return container

    def selected_menu(self):
        breadcrumb = self.options.get('breadcrumb', '')
        return re.split("\s*[,>]\s*", breadcrumb)

    def build_section_node(self, title):
        section_node = nodes.section()
        textnodes, title_messages = self.state.inline_text(title, self.lineno)
        titlenode = nodes.title(title, '', *textnodes)
        name = normalize_name(titlenode.astext())
        section_node['names'].append(name)
        section_node += titlenode
        section_node += title_messages
        self.state.document.note_implicit_target(section_node, section_node)

        return section_node

    def build_breadcrumb_node(self):
        breadcrumb_node = nodes.paragraph()
        breadcrumb = self.selected_menu()

        ref = nodes.reference(refuri="#")
        ref += nodes.emphasis(text=breadcrumb[0].strip())
        breadcrumb_node += ref
        for bread in breadcrumb[1:]:
            breadcrumb_node += nodes.Text(" ")
            breadcrumb_node += nodes.emphasis(text=">>")
            breadcrumb_node += nodes.Text(" ")

            ref = nodes.reference(refuri="#")
            ref += nodes.emphasis(text=bread.strip())
            breadcrumb_node += ref

        return breadcrumb_node

    def _get_desctable_attributes(self, content):
        attrs = []
        for node in content.traverse(element):
            if isinstance(node.parent.parent, nodes.field_body):
                name = node.parent.parent.parent[0][0]
                attrs.append((name, node))
            elif isinstance(node.parent.parent.parent, nodes.field_body):
                name = node.parent.parent.parent.parent[0][0]
                attrs.append((name, node))

        return attrs

    def build_desctable(self, content):
        attrs = self._get_desctable_attributes(content)
        if not attrs:
            return None

        # header row
        thead = nodes.thead()
        row = nodes.row()
        thead += row
        for label in ['No', 'Name', 'Type', 'Required', 'Description']:
            p = nodes.paragraph()
            p += nodes.Text(label)
            entry = nodes.entry()
            entry += p
            row += entry

        # desctable body
        tbody = nodes.tbody()
        for i, attr in enumerate(attrs):
            name, node = attr

            required = ''
            if node.is_required():
                required = 'o'

            row = nodes.row()
            for label in [i + 1, name, node.longname, required, node.description()]:
                p = nodes.paragraph()
                p += nodes.Text(label)
                entry = nodes.entry()
                entry += p
                row += entry
            tbody += row

        tgroup = nodes.tgroup(cols=4)
        tgroup += nodes.colspec(colwidth=5)  # No
        tgroup += nodes.colspec(colwidth=20)  # Name
        tgroup += nodes.colspec(colwidth=20)  # Type
        tgroup += nodes.colspec(colwidth=5)  # Required
        tgroup += nodes.colspec(colwidth=50)  # Description
        tgroup += thead
        tgroup += tbody

        table = nodes.table()
        table += tgroup

        return table


# define menulist on global
menulist = MenuList()


def webmock_roles(fn):
    def func(name, rawtext, text, lineno, inliner, options={}, content=[]):
        text = docutils.utils.unescape(text)
        has_explicit, title, _options = split_explicit_title(text)
    
        if title in ('-', '_'):
            title = ''
    
        if not has_explicit:
            _options = ""
    
        node = fn()
        node['rawtext'] = rawtext
        node['title'] = title
        node['options'] = _options
    
        return [node], []

    return func


class element(nodes.General, nodes.Element):
    longname = ''

    def type(self):
        return self.__class__.__name__[1:]

    def to_raw(self):
        return nodes.raw(self['rawtext'], self.to_html(), format='html')

    def to_html(self):
        return ''

    def is_required(self):
        if re.search('required', self['options']):
            return True
        else:
            return False

    def description(self):
        return re.sub('required(,\s*)*', '', self['options'])


class multielement(element):
    def description(self):
        choices = u'選択肢: ' + self['title']
        description = super(multielement, self).description()
        if description:
            return choices + ", " + description
        else:
            return choices


class _button(element):
    longname = u'ボタン'

    def to_html(self):
        return """<button>%s</button>""" % self['title']


@webmock_roles
def button_role():
    return _button()


class _text(element):
    longname = u'テキスト'

    def to_html(self):
        return """<input type="text" value="%s" size="40" />""" % self['title']


@webmock_roles
def text_role():
    return _text()


class _textarea(element):
    longname = u'テキスト(複数行)'

    def to_html(self):
        return """<textarea rows="5" cols="60">%s</textarea>""" % self['title']


@webmock_roles
def textarea_role():
    return _textarea()


class _select(multielement):
    longname = u'プルダウン'

    def to_html(self):
        labels = self['title'].split(',')
        options = ("<option>%s</option>" % l for l in labels)
        return """<select>%s</select>""" % "".join(options)


@webmock_roles
def select_role():
    return _select()


class _radio(multielement):
    longname = u'ラジオ'

    def to_html(self):
        _id = uuid.uuid1()
        labels = self['title'].split(',')
        options = ("""<input type="radio" name="%s" value="%s" />%s""" % (_id, l, l) for l in labels)
        return "&nbsp;".join(options)


@webmock_roles
def radio_role():
    return _radio()


class _checkbox(multielement):
    longname = u'チェックボックス'

    def to_html(self):
        labels = self['title'].split(',')
        options = ["""<input type="checkbox" value="%s" />%s""" % (l, l) for l in labels]
        return "&nbsp;".join(options)


@webmock_roles
def checkbox_role():
    return _checkbox()


def on_doctree_resolved(self, doctree, docname):
    for node in doctree.traverse(element):
        node.parent.replace(node, node.to_raw())


def setup(app):
    app.add_directive('menulist', MenuListDirective)
    app.add_directive('page', PageDirective)

    app.add_role('button', button_role)
    app.add_role('text', text_role)
    app.add_role('textarea', textarea_role)
    app.add_role('select', select_role)
    app.add_role('radio', radio_role)
    app.add_role('checkbox', checkbox_role)
    app.connect("doctree-resolved", on_doctree_resolved)
