from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, StringField
from wtforms.validators import DataRequired, NumberRange


class CashForm(FlaskForm):
    type = SelectField(
        "Тип",
        choices=[("income", "Приход"), ("expense", "Расход")],
        validators=[DataRequired()],
    )
    amount = DecimalField(
        "Сумма",
        places=2,
        validators=[DataRequired(), NumberRange(min=0)],
    )
    currency = SelectField(
        "Валюта",
        choices=[("UZS", "UZS"), ("USD", "USD"), ("EUR", "EUR")],
        validators=[DataRequired()],
    )
    description = StringField("Описание")
