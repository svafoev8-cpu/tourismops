from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

login_manager.login_view = "auth.login"
login_manager.login_message = None  # скрыть "Please log in to access this page."
# login_manager.login_message_category = "info"  # или поменять категорию, если не скрываешь
