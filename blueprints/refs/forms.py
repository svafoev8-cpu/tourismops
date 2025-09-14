# C:\tourismops\blueprints\refs\forms.py
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp

ACCOUNT_TYPE_CHOICES = [
    ("Поставщик", "Поставщик"),
    ("Субагент", "Субагент"),
    ("Корпоранты", "Корпоранты"),
    ("B2C", "B2C"),
    ("Сотрудник FLY.TJ", "Сотрудник FLY.TJ"),
    ("УК и его проекты", "УК и его проекты"),
    ("Руководство", "Руководство"),
    ("Доходы", "Доходы"),
    ("Расходы", "Расходы"),
    ("Инкассация", "Инкассация"),
    ("Капитал", "Капитал"),
]

ACCOUNT_STATUS_CHOICES = [
    ("open", "Открыт"),
    ("closed", "Закрыт"),
]


class ClientForm(FlaskForm):
    item_id = HiddenField()  # для режима редактирования
    code = StringField(
        "Код клиента (5 цифр)",
        validators=[
            DataRequired(message="Укажите 5-значный код"),
            Length(min=5, max=5, message="Код должен быть ровно 5 символов"),
            Regexp(r"^\d{5}$", message="Допускаются только цифры"),
        ],
    )
    name = StringField(
        "Наименование клиента", validators=[DataRequired(), Length(max=255)]
    )
    account_type = SelectField(
        "Тип счета", choices=ACCOUNT_TYPE_CHOICES, validators=[DataRequired()]
    )
    account_status = SelectField(
        "Статус счета",
        choices=ACCOUNT_STATUS_CHOICES,
        default="open",
        validators=[DataRequired()],
    )
    submit = SubmitField("Сохранить")
