# C:\tourismops\app.py
import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask
from werkzeug.security import generate_password_hash

from config import config_map  # ожидается: {"development": DevConfig, "production": ProdConfig, ...}
from extensions import db, migrate, login_manager


# =========================
#  Загрузка .env и базовые настройки
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))


def _select_env() -> str:
    """
    APP_ENV > FLASK_ENV > 'development'
    Если ключа нет в config_map — откатываемся на 'development'.
    """
    env = os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "development"
    return env if env in config_map else "development"


def create_app() -> Flask:
    env = _select_env()
    app = Flask(__name__)
    app.config.from_object(config_map[env])

    # Строка подключения из .env имеет приоритет
    uri = (os.getenv("SQLALCHEMY_DATABASE_URI") or "").strip()
    if uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = uri

    # Дефолты
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "change-me"))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", {"pool_pre_ping": True})

    # PyMySQL под MySQLdb (актуально для Windows)
    if app.config.get("SQLALCHEMY_DATABASE_URI", "").startswith("mysql+pymysql"):
        try:
            import pymysql  # noqa: F401
            pymysql.install_as_MySQLdb()
        except Exception:
            pass

    # =========================
    #  Инициализация расширений
    # =========================
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    # страница логина задаётся в extensions.py (auth.login)
    login_manager.login_message = None  # не показывать английское сообщение по умолчанию

    # =========================
    #  Регистрация блюпринтов
    # =========================
    from blueprints.auth import bp as auth_bp
    from blueprints.core import bp as core_bp
    from blueprints.cash import bp as cash_bp
    from blueprints.bank import bp as bank_bp
    from blueprints.tickets import bp as tickets_bp
    from blueprints.internal_tour import bp as int_bp
    from blueprints.external_tour import bp as ext_bp
    from blueprints.reports import bp as reports_bp
    from blueprints.analytics import bp as analytics_bp

    # Опциональные (могут отсутствовать)
    try:
        from blueprints.refs import bp as refs_bp
        app.register_blueprint(refs_bp, url_prefix="/refs")
    except Exception:
        pass

    try:
        from blueprints.directory import bp as dir_bp
        app.register_blueprint(dir_bp, url_prefix="/directory")
    except Exception:
        pass

    # Основные
    app.register_blueprint(auth_bp)
    app.register_blueprint(core_bp)
    app.register_blueprint(cash_bp, url_prefix="/cash")
    app.register_blueprint(bank_bp, url_prefix="/bank")
    app.register_blueprint(tickets_bp, url_prefix="/tickets")
    app.register_blueprint(int_bp, url_prefix="/internal")
    app.register_blueprint(ext_bp, url_prefix="/external")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")

    # Делает в Jinja доступной проверку наличия эндпойнта (для безопасного меню)
    app.jinja_env.globals["has_endpoint"] = lambda name: name in app.view_functions

    # =========================
    #  Flask-Login: user_loader
    # =========================
    # ВАЖНО: импорт моделей после init_app, чтобы избежать круговых импортов
    from models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return db.session.get(User, int(user_id))  # SA 2.x
        except Exception:
            try:
                return User.query.get(int(user_id))     # fallback для SA 1.x
            except Exception:
                return None

    # =========================
    #  Context processor: год для футера
    # =========================
    @app.context_processor
    def inject_year():
        return {"year": datetime.utcnow().year}

    # =========================
    #  Посев админа из .env (однократно, если таблицы уже есть)
    # =========================
    with app.app_context():
        try:
            admin_username = os.getenv("ADMIN_USERNAME", "admin")
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

            # Импорт ещё раз здесь, чтобы гарантированно был маппер
            from models import User as UserModel  # имя отдельно, чтобы не путать с локальным User
            exists = db.session.execute(
                db.select(UserModel).filter_by(username=admin_username)
            ).scalar_one_or_none()
            if not exists:
                db.session.add(UserModel(
                    username=admin_username,
                    password_hash=generate_password_hash(admin_password)
                ))
                db.session.commit()
                app.logger.info("Создан админ-пользователь: %s", admin_username)
        except Exception as exc:
            # Может сработать до миграций — просто залогируем и продолжим
            app.logger.warning("Посев админа пропущен: %s", exc)

    # =========================
    #  Обработчики ошибок
    # =========================
    @app.errorhandler(401)
    def err_401(e):
        return ("Не авторизовано", 401)

    @app.errorhandler(403)
    def err_403(e):
        return ("Доступ запрещён (недостаточно прав)", 403)

    @app.errorhandler(404)
    def err_404(e):
        return ("Страница не найдена", 404)

    @app.errorhandler(500)
    def err_500(e):
        return ("Внутренняя ошибка сервера", 500)

    return app


# Экземпляр приложения для flask CLI / wsgi
app = create_app()
