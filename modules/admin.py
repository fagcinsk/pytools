from lib.pt_admin_views import PTModelView


class Admin():
    def __init__(self, modules):
        self._modules = modules
        from dotenv import load_dotenv
        load_dotenv()

    def run(self, host='127.0.0.1', port=8888):
        """Runs web interface"""
        from lib.pt_models import create_tables

        create_tables()

        self._init_flask()
        self._init_login()
        self._init_admin()
        self._load_models()
        self._load_modules()

        print('[*] Running server...')
        self._app.run(host, port)

    def _init_flask(self):
        print('[*] Init flask...')
        import os
        from flask import Flask, cli, render_template, request, session
        from flask_babelex import Babel

        self._app = Flask(__name__, template_folder='../templates')
        cli.show_server_banner = lambda *_: None
        self._app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'Ih4v3s3cr'
        self._app.config['MAX_CONTENT_LENGTH'] = 4096

        babel = Babel(self._app, default_locale='en')
        print(babel.list_translations())

        @babel.localeselector
        def get_locale():
            # if request.args.get('lang'):
            #     session['lang'] = request.args.get('lang')
            # return session.get('lang', 'ru')
            return request.accept_languages.best_match(['ru', 'en'])

        @self._app.route('/')
        def index():
            return render_template('index.html')

    def _init_login(self):
        print('[*] Init login...')
        import flask_login as login
        from lib.pt_models import User
        self._login_manager = login.LoginManager()
        self._login_manager.init_app(self._app)

        # Create user loader function
        @self._login_manager.user_loader
        def load_user(user_id):
            return User.get(user_id)

    def _init_admin(self):
        print('[*] Init admin...')
        from flask_admin import Admin
        from werkzeug.security import generate_password_hash
        from lib.pt_models import User
        from lib.pt_admin_views import IndexView

        if not User.select().where(User.login == 'ptadmin').exists():
            default_login = 'ptadmin'
            default_pass = 'PT_p@$$w0rd'
            User.create(
                login=default_login,
                first_name='PyTools',
                last_name='Admin',
                email='ptadmin@admin.adm',
                is_admin=True,
                password=generate_password_hash(default_pass))
            print('Admin: (login: {}, password: {}), you can change that'.format(
                default_login, default_pass))

        self._app.config['FLASK_ADMIN_SWATCH'] = 'cosmo'

        self._admin = Admin(self._app, 'PyTools admin',
                            template_mode='bootstrap4', index_view=IndexView(), base_template='layout.html')

    def _load_modules(self):
        print('[*] Load modules...')
        from flask_admin import expose
        from flask_admin.base import BaseView
        from flask_babelex import lazy_gettext as gettext

        modules = self._modules

        class ModuleView(BaseView):
            @expose('/')
            def index(self):
                return self.render('admin/module.html', modules=modules)

        for m in modules:
            self._admin.add_view(ModuleView(
                m, gettext('Modules'), 'admin.' + m))

    def _load_models(self):
        print('[*] Load models...')
        from lib.pt_models import SEOSession, SEOCheckResult, User, Config, FortuneIP
        from lib.pt_admin_views import SEOSessionView, SEOCheckResultView, UserView, SEOResultSummaryView, ConfigView
        from flask_babelex import lazy_gettext as gettext

        self._admin.add_view(ConfigView(
            Config, name=gettext('Config'), category='Settings'))
        self._admin.add_view(SEOSessionView(
            SEOSession, name=gettext('Sessions'), category='SEO'))
        self._admin.add_view(SEOCheckResultView(
            SEOCheckResult, name=gettext('Results'), category='SEO'))
        self._admin.add_view(SEOResultSummaryView(
            name=gettext('Summary'), category='SEO'))
        self._admin.add_view(
            UserView(User, name=gettext('Users'), category=gettext('Administration')))
        self._admin.add_view(PTModelView(FortuneIP, name=gettext(
            'Fortune'), category=gettext('Gathering')))

        try:
            import local.models as local_models
            self._load_models_from_module(local_models)
        except:
            pass

    def _load_models_from_module(self, module):
        print('[*] Load model {}...'.format(module.__name__))
        from inspect import isclass
        from lib.pt_admin_views import PTModelView
        from flask_babelex import lazy_gettext as gettext

        for member in module.__dict__:
            if member.startswith('_'):
                continue
            m = getattr(module, member)
            if isclass(m) and m is not module.BaseModel and issubclass(m, module.BaseModel):
                self._admin.add_view(PTModelView(
                    m, category=gettext('Models')))
