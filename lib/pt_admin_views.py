from flask import Markup, redirect, request, url_for
from flask_admin import AdminIndexView, expose, helpers, BaseView
from flask_admin.contrib.peewee import ModelView
from flask_admin.contrib.peewee.filters import FilterEqual, FilterEmpty
import flask_login as login

from lib.pt_models import SEOSession, SEOCheckResult


def _raw_formatter(v, c, m, p):
    s = getattr(m, p)
    lines = s.splitlines()
    # todo: remove in next version
    fix = 2 if lines and lines[0].startswith('  h1') else 0
    wrap_f = '<div>{}</div>'
    divs = [wrap_f.format(ln[fix:].replace('  ', '&emsp;')) for ln in lines]
    return Markup(''.join(divs))


def _url_newlines_formatter(v, c, m, p):
    return Markup(m.url.replace('/', '/<br />'))


def _cols_check_mark(attr_bool, attr_val):
    ICON_OK = '<i class="fa fa-check"></i>'
    ICON_FAIL = '<i class="fa fa-close text-danger"></i>'
    ICON_TITLE = '<div title="{}">{}</div>'

    def cm(v, c, m, p):
        return Markup(ICON_TITLE.format(getattr(m, attr_val), ICON_OK if getattr(m, attr_bool) else ICON_FAIL))
    return cm


class IndexView(AdminIndexView):
    def is_visible(self):
        return False

    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(IndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        from lib.pt_admin_forms import LoginForm

        form = LoginForm(request.form)

        if helpers.validate_form_on_submit(form):
            login.login_user(form.get_user(), remember=True)

        if login.current_user.is_authenticated:
            return redirect(request.values.get('next') or url_for(".index"))

        self._template_args['form'] = form
        return super(IndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))


class PTBaseView(BaseView):
    def is_accessible(self):
        import flask_login as login
        return login.current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.login_view', next=request.url))


class PTModelView(ModelView):
    def is_accessible(self):
        import flask_login as login
        return login.current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.login_view', next=request.url))


class ConfigView(PTModelView):
    create_template = 'cfg_edit.html'
    edit_template = 'cfg_edit.html'


class SEOResultSummaryView(PTBaseView):
    @expose('/')
    def index(self):
        from lib.pt_models import SEOCheckResult as SCR
        from collections import defaultdict, Counter

        duplicates = []
        session_titles = defaultdict(list)
        session_descriptions = defaultdict(list)
        items = SCR.select(SCR.id, SCR.session_id,
                           SCR.title_text, SCR.desc_text)
        for item in items:
            session_titles[item.session_id].append(item.title_text)
            session_descriptions[item.session_id].append(item.desc_text)

        for sid, titles in session_titles.items():
            duplicates += [(sid, 'title', title, count)
                           for title, count in Counter(titles).items() if count > 1]
        for sid, descriptions in session_descriptions.items():
            duplicates += [(sid, 'description', description, count)
                           for description, count in Counter(descriptions).items() if count > 1]

        self._template_args['duplicates'] = duplicates
        return self.render('adm/seo/summary.html')


class UserView(PTModelView):
    def is_accessible(self):
        import flask_login as login
        return super().is_accessible() and hasattr(login.current_user, 'is_admin') and login.current_user.is_admin


class SEOSessionView(PTModelView):
    can_edit = False
    can_create = False
    can_delete = False
    column_list = ('created_at', 'base_url', 'results', 'options', 'view')
    column_formatters = dict(
        created_at=lambda v, c, m, p: m.created_at.strftime(
            '%d.%m.%Y %H:%M:%S'),
        results=lambda v, c, m, p: m.results.count(),
    )


class SEOCheckResultView(PTModelView):
    # flask-admin ModelView attributes
    can_edit = True
    # edit_modal = True
    can_create = False
    can_delete = False
    can_view_details = True
    page_size = '250'
    named_filter_urls = True
    column_editable_list = ('comment',)
    column_list = (
        'url',
        'code_ok',
        'code',
        'ttfb_ok',
        'ttfb',
        'title_ok',
        'title_len',
        'title_text',
        'desc_ok',
        'desc_len',
        'desc_text',
        'headings',
        'validation',
        'comment',
        'words',
        'cfg',
    )
    column_exclude_list = ('code', 'created_at', 'id',
                           'validation', 'ttfb', 'code', 'title_len', 'desc_len')
    column_filters = [
        FilterEqual(column=SEOSession.id, name='Session ID'),
        FilterEmpty(column=SEOCheckResult.comment, name='Empty or Full', options=(
            ('Empty', 'Empty'), ('Full', 'Full'))),
    ]
    column_labels = dict(code_ok='Cod', ttfb_ok='TTFB', title_ok='T_OK',
                         desc_ok='D_OK', title_len='TL', desc_len='DL', session='Sess')
    column_formatters = dict(
        created_at=lambda v, c, m, p: m.created_at.strftime('%H:%M:%S'),
        url=_url_newlines_formatter,
        ttfb_ok=_cols_check_mark('ttfb_ok', 'ttfb'),
        code_ok=_cols_check_mark('code_ok', 'code'),
        title_ok=_cols_check_mark('title_ok', 'title_len'),
        desc_ok=_cols_check_mark('desc_ok', 'desc_len'),
        headings=_raw_formatter,
    )
