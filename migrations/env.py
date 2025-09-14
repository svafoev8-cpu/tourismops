import logging
from logging.config import fileConfig

from alembic import context
from flask import current_app

# Alembic config
config = context.config

# Logging
fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")


def get_engine():
    try:
        # Flask-SQLAlchemy<3 and Alchemical
        return current_app.extensions["migrate"].db.get_engine()
    except (TypeError, AttributeError):
        # Flask-SQLAlchemy>=3
        return current_app.extensions["migrate"].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace("%", "%%")
    except AttributeError:
        return str(get_engine().url).replace("%", "%%")


# pass DB url to alembic
config.set_main_option("sqlalchemy.url", get_engine_url())
target_db = current_app.extensions["migrate"].db


def get_metadata():
    if hasattr(target_db, "metadatas"):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=get_metadata(),
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,  # <<< важно
    )

    with context.begin_transaction():
        context.run_migrations()


def include_object(object, name, type_, reflected, compare_to):
    """
    НЕ удаляем объекты, которые существуют в БД, но отсутствуют в моделях.
    Это отключает автодроп старых таблиц/индексов (account, account_type, subagent, ...).
    """
    # если это таблица, полученная из отражения (reflected=True), и ей нет пары в моделях -> не трогаем
    if type_ == "table" and reflected and compare_to is None:
        return False
    # индексы «чужих» таблиц тоже не дропаем
    if type_ == "index" and reflected and compare_to is None:
        return False
    return True


def run_migrations_online():
    """Run migrations in 'online' mode."""

    def process_revision_directives(context_, revision, directives):
        if getattr(config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("No changes in schema detected.")

    conf_args = current_app.extensions["migrate"].configure_args

    # добавляем наши параметры, если не заданы
    conf_args.setdefault("process_revision_directives", process_revision_directives)
    conf_args.setdefault("compare_type", True)
    conf_args.setdefault("compare_server_default", True)
    conf_args["include_object"] = include_object  # <<< важно

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=get_metadata(), **conf_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
