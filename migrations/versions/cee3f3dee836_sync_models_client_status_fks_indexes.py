"""sync models: client.status, FKs, indexes

Revision ID: cee3f3dee836
Revises: ef68991e21a0
Create Date: 2025-09-14 12:25:44.355507
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "cee3f3dee836"
down_revision = "ef68991e21a0"
branch_labels = None
depends_on = None


# ---- helpers ---------------------------------------------------------------
def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns(table_name)]
    return column_name in cols


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        idx = insp.get_indexes(table_name)
    except Exception:
        return False
    names = {i.get("name") for i in idx if i.get("name")}
    return index_name in names


def _add_created_at_safely(table_name: str):
    """
    Для MySQL: добавляем NOT NULL DATETIME с временным default CURRENT_TIMESTAMP,
    чтобы не ловить '0000-00-00 00:00:00' на существующих строках.
    После — убираем server_default.
    """
    if not _column_exists(table_name, "created_at"):
        op.add_column(
            table_name,
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )
        op.alter_column(table_name, "created_at", server_default=None)


# ---- upgrade ---------------------------------------------------------------
def upgrade():
    # ----- AUDIT_LOG -----
    with op.batch_alter_table("audit_log", schema=None) as batch_op:
        if not _column_exists("audit_log", "details"):
            batch_op.add_column(sa.Column("details", sa.Text(), nullable=True))
        batch_op.alter_column(
            "action", existing_type=sa.String(length=255), nullable=False
        )
        batch_op.alter_column("timestamp", existing_type=sa.DateTime(), nullable=False)

    if not _index_exists("audit_log", "ix_audit_log_timestamp"):
        op.create_index("ix_audit_log_timestamp", "audit_log", ["timestamp"])
    if not _index_exists("audit_log", "ix_audit_log_user_id"):
        op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"])

    # ----- BANK_OPERATION -----
    with op.batch_alter_table("bank_operation", schema=None) as batch_op:
        if not _column_exists("bank_operation", "client_id"):
            batch_op.add_column(sa.Column("client_id", sa.Integer(), nullable=True))
        if not _column_exists("bank_operation", "supplier_id"):
            batch_op.add_column(sa.Column("supplier_id", sa.Integer(), nullable=True))
        if not _column_exists("bank_operation", "op_type"):
            batch_op.add_column(
                sa.Column("op_type", sa.String(length=10), nullable=False)
            )
        if not _column_exists("bank_operation", "rate"):
            batch_op.add_column(sa.Column("rate", sa.Numeric(12, 6), nullable=True))
        if not _column_exists("bank_operation", "doc_number"):
            batch_op.add_column(
                sa.Column("doc_number", sa.String(length=64), nullable=True)
            )
        if not _column_exists("bank_operation", "value_date"):
            batch_op.add_column(sa.Column("value_date", sa.Date(), nullable=True))

        # ужесточаем существующие
        batch_op.alter_column("user_id", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column(
            "currency",
            existing_type=sa.String(length=10),
            type_=sa.String(length=3),
            nullable=False,
        )
        batch_op.alter_column(
            "amount",
            existing_type=sa.Numeric(12, 2),
            type_=sa.Numeric(16, 2),
            nullable=False,
        )

        # старые поля (если вдруг есть)
        if _column_exists("bank_operation", "timestamp"):
            batch_op.drop_column("timestamp")
        if _column_exists("bank_operation", "type"):
            batch_op.drop_column("type")

    _add_created_at_safely("bank_operation")

    for idx_name, cols in [
        ("ix_bank_operation_client_id", ["client_id"]),
        ("ix_bank_operation_created_at", ["created_at"]),
        ("ix_bank_operation_doc_number", ["doc_number"]),
        ("ix_bank_operation_op_type", ["op_type"]),
        ("ix_bank_operation_supplier_id", ["supplier_id"]),
        ("ix_bank_operation_user_id", ["user_id"]),
        ("ix_bank_type_time", ["op_type", "created_at"]),
        ("ix_bank_user_time", ["user_id", "created_at"]),
    ]:
        if not _index_exists("bank_operation", idx_name):
            op.create_index(idx_name, "bank_operation", cols)

    # FKs (могут существовать — пробуем создать, в MySQL дубликат вызовет ошибку, поэтому мягко)
    try:
        op.create_foreign_key(
            None, "bank_operation", "client", ["client_id"], ["id"], ondelete="SET NULL"
        )
    except Exception:
        pass
    try:
        op.create_foreign_key(
            None,
            "bank_operation",
            "supplier",
            ["supplier_id"],
            ["id"],
            ondelete="SET NULL",
        )
    except Exception:
        pass

    # ----- CASH_OPERATION -----
    with op.batch_alter_table("cash_operation", schema=None) as batch_op:
        if not _column_exists("cash_operation", "op_type"):
            batch_op.add_column(
                sa.Column("op_type", sa.String(length=10), nullable=False)
            )
        if not _column_exists("cash_operation", "rate"):
            batch_op.add_column(sa.Column("rate", sa.Numeric(12, 6), nullable=True))
        if not _column_exists("cash_operation", "fio"):
            batch_op.add_column(sa.Column("fio", sa.String(length=255), nullable=True))

        batch_op.alter_column("user_id", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column(
            "currency",
            existing_type=sa.String(length=10),
            type_=sa.String(length=3),
            nullable=False,
        )
        batch_op.alter_column(
            "amount",
            existing_type=sa.Numeric(12, 2),
            type_=sa.Numeric(14, 2),
            nullable=False,
        )

        # старые поля, если остались
        if _column_exists("cash_operation", "timestamp"):
            batch_op.drop_column("timestamp")
        if _column_exists("cash_operation", "type"):
            batch_op.drop_column("type")

    _add_created_at_safely("cash_operation")

    for idx_name, cols in [
        ("ix_cash_operation_created_at", ["created_at"]),
        ("ix_cash_operation_op_type", ["op_type"]),
        ("ix_cash_operation_user_id", ["user_id"]),
        ("ix_cash_type_time", ["op_type", "created_at"]),
        ("ix_cash_user_time", ["user_id", "created_at"]),
    ]:
        if not _index_exists("cash_operation", idx_name):
            op.create_index(idx_name, "cash_operation", cols)

    # восстановим FKs, если их не было
    try:
        op.create_foreign_key(
            None,
            "cash_operation",
            "supplier",
            ["supplier_id"],
            ["id"],
            ondelete="SET NULL",
        )
    except Exception:
        pass
    try:
        op.create_foreign_key(
            None, "cash_operation", "client", ["client_id"], ["id"], ondelete="SET NULL"
        )
    except Exception:
        pass

    # ----- CLIENT -----
    with op.batch_alter_table("client", schema=None) as batch_op:
        if not _column_exists("client", "account_type"):
            batch_op.add_column(
                sa.Column(
                    "account_type",
                    sa.String(length=50),
                    nullable=False,
                    server_default="current",
                )
            )
            batch_op.alter_column("account_type", server_default=None)

        if not _column_exists("client", "account_status"):
            batch_op.add_column(
                sa.Column(
                    "account_status",
                    sa.String(length=10),
                    nullable=False,
                    server_default="open",
                )
            )
            batch_op.alter_column("account_status", server_default=None)

        if not _column_exists("client", "status"):
            batch_op.add_column(
                sa.Column(
                    "status",
                    sa.String(length=20),
                    nullable=False,
                    server_default="active",
                )
            )
            batch_op.alter_column("status", server_default=None)

        # code: 64 -> 5
        batch_op.alter_column(
            "code",
            existing_type=sa.String(length=64),
            type_=sa.String(length=5),
            existing_nullable=False,
        )

    for idx_name, cols in [
        ("ix_client_account_status", ["account_status"]),
        ("ix_client_account_type", ["account_type"]),
        ("ix_client_name", ["name"]),
        ("ix_client_status", ["status"]),
    ]:
        if not _index_exists("client", idx_name):
            op.create_index(idx_name, "client", cols)

    # ----- EXTERNAL_TOUR -----
    with op.batch_alter_table("external_tour", schema=None) as batch_op:
        for name, col in [
            ("user_id", sa.Column("user_id", sa.Integer(), nullable=False)),
            ("client_id", sa.Column("client_id", sa.Integer(), nullable=True)),
            ("supplier_id", sa.Column("supplier_id", sa.Integer(), nullable=True)),
            (
                "order_type",
                sa.Column("order_type", sa.String(length=50), nullable=True),
            ),
            ("fio", sa.Column("fio", sa.String(length=255), nullable=True)),
            ("direction", sa.Column("direction", sa.String(length=255), nullable=True)),
            (
                "currency",
                sa.Column(
                    "currency",
                    sa.String(length=3),
                    nullable=False,
                    server_default="USD",
                ),
            ),
        ]:
            if not _column_exists("external_tour", name):
                batch_op.add_column(col)
                if name == "currency":
                    batch_op.alter_column("currency", server_default=None)

        batch_op.alter_column(
            "cost",
            existing_type=sa.Numeric(12, 2),
            type_=sa.Numeric(14, 2),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "sale_price",
            existing_type=sa.Numeric(12, 2),
            type_=sa.Numeric(14, 2),
            existing_nullable=True,
        )

        if _column_exists("external_tour", "client_name"):
            batch_op.drop_column("client_name")

    _add_created_at_safely("external_tour")

    for idx_name, cols in [
        ("ix_external_tour_client_id", ["client_id"]),
        ("ix_external_tour_created_at", ["created_at"]),
        ("ix_external_tour_order_type", ["order_type"]),
        ("ix_external_tour_supplier_id", ["supplier_id"]),
        ("ix_external_tour_user_id", ["user_id"]),
        ("ix_exttour_user_time", ["user_id", "created_at"]),
    ]:
        if not _index_exists("external_tour", idx_name):
            op.create_index(idx_name, "external_tour", cols)

    for args in [
        (None, "external_tour", "client", ["client_id"], ["id"]),
        (None, "external_tour", "supplier", ["supplier_id"], ["id"]),
        (None, "external_tour", "user", ["user_id"], ["id"]),
    ]:
        try:
            op.create_foreign_key(*args)
        except Exception:
            pass

    # ----- INTERNAL_TOUR -----
    with op.batch_alter_table("internal_tour", schema=None) as batch_op:
        for name, col in [
            ("user_id", sa.Column("user_id", sa.Integer(), nullable=False)),
            ("client_id", sa.Column("client_id", sa.Integer(), nullable=True)),
            ("supplier_id", sa.Column("supplier_id", sa.Integer(), nullable=True)),
            (
                "order_type",
                sa.Column("order_type", sa.String(length=50), nullable=True),
            ),
            ("fio", sa.Column("fio", sa.String(length=255), nullable=True)),
            ("direction", sa.Column("direction", sa.String(length=255), nullable=True)),
            (
                "currency",
                sa.Column(
                    "currency",
                    sa.String(length=3),
                    nullable=False,
                    server_default="USD",
                ),
            ),
        ]:
            if not _column_exists("internal_tour", name):
                batch_op.add_column(col)
                if name == "currency":
                    batch_op.alter_column("currency", server_default=None)

        batch_op.alter_column(
            "cost",
            existing_type=sa.Numeric(12, 2),
            type_=sa.Numeric(14, 2),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "sale_price",
            existing_type=sa.Numeric(12, 2),
            type_=sa.Numeric(14, 2),
            existing_nullable=True,
        )

        if _column_exists("internal_tour", "client_name"):
            batch_op.drop_column("client_name")

    _add_created_at_safely("internal_tour")

    for idx_name, cols in [
        ("ix_internal_tour_client_id", ["client_id"]),
        ("ix_internal_tour_created_at", ["created_at"]),
        ("ix_internal_tour_order_type", ["order_type"]),
        ("ix_internal_tour_supplier_id", ["supplier_id"]),
        ("ix_internal_tour_user_id", ["user_id"]),
        ("ix_inttour_user_time", ["user_id", "created_at"]),
    ]:
        if not _index_exists("internal_tour", idx_name):
            op.create_index(idx_name, "internal_tour", cols)

    for args in [
        (None, "internal_tour", "client", ["client_id"], ["id"]),
        (None, "internal_tour", "supplier", ["supplier_id"], ["id"]),
        (None, "internal_tour", "user", ["user_id"], ["id"]),
    ]:
        try:
            op.create_foreign_key(*args)
        except Exception:
            pass

    # ----- SUPPLIER -----
    with op.batch_alter_table("supplier", schema=None) as batch_op:
        batch_op.alter_column(
            "phone",
            existing_type=sa.String(length=50),
            type_=sa.String(length=32),
            existing_nullable=True,
        )
    if not _index_exists("supplier", "ix_supplier_code"):
        op.create_index("ix_supplier_code", "supplier", ["code"], unique=True)

    # ----- TICKET_SALE -----
    with op.batch_alter_table("ticket_sale", schema=None) as batch_op:
        for name, col in [
            ("client_id", sa.Column("client_id", sa.Integer(), nullable=True)),
            ("supplier_id", sa.Column("supplier_id", sa.Integer(), nullable=True)),
            (
                "airline_code",
                sa.Column("airline_code", sa.String(length=8), nullable=True),
            ),
            (
                "order_number",
                sa.Column("order_number", sa.String(length=64), nullable=True),
            ),
            (
                "flight_number",
                sa.Column("flight_number", sa.String(length=32), nullable=True),
            ),
            ("departure_date", sa.Column("departure_date", sa.Date(), nullable=True)),
            ("rate", sa.Column("rate", sa.Numeric(12, 6), nullable=True)),
            (
                "fare_supplier",
                sa.Column("fare_supplier", sa.Numeric(14, 2), nullable=True),
            ),
            (
                "tax_supplier",
                sa.Column("tax_supplier", sa.Numeric(14, 2), nullable=True),
            ),
            (
                "other_fees_supplier",
                sa.Column("other_fees_supplier", sa.Numeric(14, 2), nullable=True),
            ),
            (
                "our_fee_supplier",
                sa.Column("our_fee_supplier", sa.Numeric(14, 2), nullable=True),
            ),
            (
                "total_supplier",
                sa.Column("total_supplier", sa.Numeric(14, 2), nullable=True),
            ),
        ]:
            if not _column_exists("ticket_sale", name):
                batch_op.add_column(col)

        # ужесточения по существующим
        batch_op.alter_column("user_id", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column(
            "currency",
            existing_type=sa.String(length=10),
            type_=sa.String(length=3),
            nullable=False,
        )
        batch_op.alter_column(
            "ticket_number",
            existing_type=sa.String(length=64),
            type_=sa.String(length=32),
            existing_nullable=True,
        )

        if _column_exists("ticket_sale", "amount"):
            batch_op.drop_column("amount")

    _add_created_at_safely("ticket_sale")

    for idx_name, cols in [
        ("ix_ticket_dep_date", ["departure_date"]),
        ("ix_ticket_sale_airline_code", ["airline_code"]),
        ("ix_ticket_sale_client_id", ["client_id"]),
        ("ix_ticket_sale_created_at", ["created_at"]),
        ("ix_ticket_sale_date", ["sale_date"]),
        ("ix_ticket_sale_flight_number", ["flight_number"]),
        ("ix_ticket_sale_order_number", ["order_number"]),
        ("ix_ticket_sale_supplier_id", ["supplier_id"]),
        ("ix_ticket_sale_ticket_number", ["ticket_number"]),
        ("ix_ticket_sale_user_id", ["user_id"]),
        ("ix_ticket_user_time", ["user_id", "created_at"]),
    ]:
        if not _index_exists("ticket_sale", idx_name):
            op.create_index(idx_name, "ticket_sale", cols)

    for args in [
        (None, "ticket_sale", "client", ["client_id"], ["id"]),
        (None, "ticket_sale", "supplier", ["supplier_id"], ["id"]),
    ]:
        try:
            op.create_foreign_key(*args, ondelete="SET NULL")
        except Exception:
            pass

    # ----- USER -----
    with op.batch_alter_table("user", schema=None) as batch_op:
        if not _index_exists("user", "ix_user_role"):
            batch_op.create_index("ix_user_role", ["role"], unique=False)
        # username у модели unique=True — индекс делаем уникальный
        if not _index_exists("user", "ix_user_username"):
            batch_op.create_index("ix_user_username", ["username"], unique=True)


# ---- downgrade (минимальный/безопасный) -----------------------------------
def downgrade():
    # Ничего не дропаем, чтобы не потерять данные/связи.
    # При необходимости можно описать обратные операции вручную.
    pass
