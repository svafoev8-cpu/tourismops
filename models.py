# C:\tourismops\models.py
from datetime import datetime, date
from decimal import Decimal
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager


# ========= Пользователи и справочники =========
class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)  # храним ТОЛЬКО хеш
    role = db.Column(db.String(20), nullable=False, default="user", index=True)

    cash_operations = db.relationship("CashOperation", back_populates="user", lazy="dynamic", passive_deletes=True)
    bank_operations = db.relationship("BankOperation", back_populates="user", lazy="dynamic", passive_deletes=True)
    ticket_sales   = db.relationship("TicketSale",   back_populates="user", lazy="dynamic", passive_deletes=True)
    internal_tours = db.relationship("InternalTour", back_populates="user", lazy="dynamic", passive_deletes=True)
    external_tours = db.relationship("ExternalTour", back_populates="user", lazy="dynamic", passive_deletes=True)
    audit_logs     = db.relationship("AuditLog",     back_populates="user", lazy="dynamic", passive_deletes=True)

    # --- пароли ---
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Client(db.Model):
    __tablename__ = "client"

    id = db.Column(db.Integer, primary_key=True)
    # 5-значный код, только цифры; уникальный и индексируемый
    code = db.Column(db.String(5), unique=True, nullable=False, index=True)
    # Наименование клиента
    name = db.Column(db.String(255), nullable=False, index=True)
    # Тип счёта
    account_type = db.Column(db.String(50), nullable=False, index=True)
    # Статус счёта: open|closed
    account_status = db.Column(db.String(10), nullable=False, default="open", index=True)
    # Бизнес-статус клиента: active|inactive (то, что ты просил для формы)
    status = db.Column(db.String(20), nullable=False, default="active", index=True)

    # ОБРАТНЫЕ СВЯЗИ (совпадают с back_populates в других моделях)
    cash_operations = db.relationship("CashOperation", back_populates="client", lazy="dynamic", passive_deletes=True)
    bank_operations = db.relationship("BankOperation", back_populates="client", lazy="dynamic", passive_deletes=True)
    ticket_sales    = db.relationship("TicketSale",    back_populates="client", lazy="dynamic", passive_deletes=True)
    internal_tours  = db.relationship("InternalTour",  back_populates="client", lazy="dynamic", passive_deletes=True)
    external_tours  = db.relationship("ExternalTour",  back_populates="client", lazy="dynamic", passive_deletes=True)

    def __repr__(self):
        return f"<Client {self.code} - {self.name} [{self.account_type}] ({self.account_status}/{self.status})>"


class Supplier(db.Model):
    __tablename__ = "supplier"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(32))

    cash_operations = db.relationship("CashOperation", back_populates="supplier", lazy="dynamic", passive_deletes=True)
    bank_operations = db.relationship("BankOperation", back_populates="supplier", lazy="dynamic", passive_deletes=True)
    ticket_sales   = db.relationship("TicketSale",   back_populates="supplier", lazy="dynamic", passive_deletes=True)
    internal_tours = db.relationship("InternalTour", back_populates="supplier", lazy="dynamic", passive_deletes=True)
    external_tours = db.relationship("ExternalTour", back_populates="supplier", lazy="dynamic", passive_deletes=True)

    def __repr__(self):
        return f"<Supplier {self.code} - {self.name}>"


# ========= Касса (наличные) =========
class CashOperation(db.Model):
    __tablename__ = "cash_operation"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id", ondelete="SET NULL"), nullable=True, index=True)

    # 'income' | 'expense'
    op_type = db.Column(db.String(10), nullable=False, index=True)

    currency = db.Column(db.String(3), nullable=False, default="USD")
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    rate = db.Column(db.Numeric(12, 6), nullable=True)

    description = db.Column(db.Text, nullable=True)
    fio = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="cash_operations")
    client = db.relationship("Client", back_populates="cash_operations")
    supplier = db.relationship("Supplier", back_populates="cash_operations")

    def __repr__(self):
        return f"<CashOperation {self.op_type} {self.amount} {self.currency} user={self.user_id}>"


# ========= Банк (безнал) =========
class BankOperation(db.Model):
    __tablename__ = "bank_operation"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id", ondelete="SET NULL"), nullable=True, index=True)

    # 'incoming' | 'outgoing'
    op_type = db.Column(db.String(10), nullable=False, index=True)

    currency = db.Column(db.String(3), nullable=False, default="USD")
    amount = db.Column(db.Numeric(16, 2), nullable=False)
    rate = db.Column(db.Numeric(12, 6), nullable=True)

    doc_number = db.Column(db.String(64), nullable=True, index=True)
    value_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="bank_operations")
    client = db.relationship("Client", back_populates="bank_operations")
    supplier = db.relationship("Supplier", back_populates="bank_operations")

    def __repr__(self):
        return f"<BankOperation {self.op_type} {self.amount} {self.currency} user={self.user_id}>"


# ========= Реестр продаж авиабилетов =========
class TicketSale(db.Model):
    __tablename__ = "ticket_sale"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id", ondelete="SET NULL"), nullable=True, index=True)

    airline_code = db.Column(db.String(8), nullable=True, index=True)      # Код А/К
    passenger_name = db.Column(db.String(255), nullable=True)              # ФИО/Пассажира
    ticket_number = db.Column(db.String(32), nullable=True, index=True)    # Номер А/Б
    order_number = db.Column(db.String(64), nullable=True, index=True)     # Номер заказа
    route = db.Column(db.String(255), nullable=True)                       # Маршрут
    flight_number = db.Column(db.String(32), nullable=True, index=True)    # № рейс

    sale_date = db.Column(db.Date, nullable=True)                          # Дата продажи
    departure_date = db.Column(db.Date, nullable=True)                     # Дата вылета

    currency = db.Column(db.String(3), nullable=False, default="USD")
    rate = db.Column(db.Numeric(12, 6), nullable=True)

    fare_supplier = db.Column(db.Numeric(14, 2), nullable=True)            # тариф (номинал поставщика)
    tax_supplier = db.Column(db.Numeric(14, 2), nullable=True)             # сборы
    other_fees_supplier = db.Column(db.Numeric(14, 2), nullable=True)      # прочие сборы
    our_fee_supplier = db.Column(db.Numeric(14, 2), nullable=True)         # наши сборы
    total_supplier = db.Column(db.Numeric(14, 2), nullable=True)           # итого у поставщика

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="ticket_sales")
    client = db.relationship("Client", back_populates="ticket_sales")
    supplier = db.relationship("Supplier", back_populates="ticket_sales")

    def __repr__(self):
        return f"<TicketSale {self.ticket_number} {self.passenger_name} {self.airline_code}>"


# ========= Внутренний туризм =========
class InternalTour(db.Model):
    """
    Внутренние туры: расчёт нетто и маржи по формуле в приложении.
    """
    __tablename__ = "internal_tour"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id", ondelete="SET NULL"), nullable=True, index=True)

    order_type = db.Column(db.String(50), nullable=True, index=True)  # тип заказа
    fio = db.Column(db.String(255), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    direction = db.Column(db.String(255), nullable=True)             # направление/тур
    notes = db.Column(db.Text, nullable=True)

    currency = db.Column(db.String(3), nullable=False, default="USD")
    cost = db.Column(db.Numeric(14, 2), nullable=True)               # себестоимость
    sale_price = db.Column(db.Numeric(14, 2), nullable=True)         # цена продажи

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="internal_tours")
    client = db.relationship("Client", back_populates="internal_tours")
    supplier = db.relationship("Supplier", back_populates="internal_tours")

    @property
    def net_profit(self):
        try:
            c = Decimal(self.cost or 0)
            s = Decimal(self.sale_price or 0)
            return s - c
        except Exception:
            return None

    @property
    def margin(self):
        try:
            s = Decimal(self.sale_price or 0)
            if s == 0:
                return None
            return (self.net_profit or Decimal(0)) / s
        except Exception:
            return None

    def __repr__(self):
        return f"<InternalTour {self.fio or ''} {self.direction or ''}>"


# ========= Внешний туризм =========
class ExternalTour(db.Model):
    __tablename__ = "external_tour"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id", ondelete="SET NULL"), nullable=True, index=True)

    order_type = db.Column(db.String(50), nullable=True, index=True)
    fio = db.Column(db.String(255), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    direction = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    currency = db.Column(db.String(3), nullable=False, default="USD")
    cost = db.Column(db.Numeric(14, 2), nullable=True)
    sale_price = db.Column(db.Numeric(14, 2), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="external_tours")
    client = db.relationship("Client", back_populates="external_tours")
    supplier = db.relationship("Supplier", back_populates="external_tours")

    @property
    def net_profit(self):
        try:
            c = Decimal(self.cost or 0)
            s = Decimal(self.sale_price or 0)
            return s - c
        except Exception:
            return None

    @property
    def margin(self):
        try:
            s = Decimal(self.sale_price or 0)
            if s == 0:
                return None
            return (self.net_profit or Decimal(0)) / s
        except Exception:
            return None

    def __repr__(self):
        return f"<ExternalTour {self.fio or ''} {self.direction or ''}>"


# ========= Аудит =========
class AuditLog(db.Model):
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    details = db.Column(db.Text, nullable=True)

    user = db.relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog user={self.user_id} action='{self.action}'>"


# ========= Индексы для типовых выборок =========
db.Index("ix_cash_user_time",   CashOperation.user_id,  CashOperation.created_at)
db.Index("ix_cash_type_time",   CashOperation.op_type,  CashOperation.created_at)
db.Index("ix_bank_user_time",   BankOperation.user_id,  BankOperation.created_at)
db.Index("ix_bank_type_time",   BankOperation.op_type,  BankOperation.created_at)
db.Index("ix_ticket_user_time", TicketSale.user_id,     TicketSale.created_at)
db.Index("ix_ticket_sale_date", TicketSale.sale_date)
db.Index("ix_ticket_dep_date",  TicketSale.departure_date)
db.Index("ix_inttour_user_time", InternalTour.user_id,  InternalTour.created_at)
db.Index("ix_exttour_user_time", ExternalTour.user_id,  ExternalTour.created_at)


# ========= Flask-Login user loader =========
@login_manager.user_loader
def load_user(user_id: str):
    try:
        # современный способ без LegacyAPIWarning
        return db.session.get(User, int(user_id))
    except Exception:
        return None
