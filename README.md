# TourismOps
Админ-панель туризма (Flask, SQLAlchemy, Alembic).

## Запуск (dev)
python -m venv .venv
. .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
flask --app app.py run

![CI](https://github.com/svafoev8-cpu/tourismops/actions/workflows/ci.yml/badge.svg)
