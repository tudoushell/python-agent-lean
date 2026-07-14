import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import text, select
from sqlalchemy.orm import Session

from ai_chat_service.app.db.session import session_local
from ai_chat_service.app.models.order_model import OrderModel


@dataclass(frozen=True)
class OrderInfo:
    id: int
    order_id: str
    user_name: str | None
    status: str
    amount: Decimal
    remark: str
    created_at: datetime


class OrderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_by_order_id(self, order_id: str) -> OrderInfo | None:
        sql = text("""
             SELECT id,order_id, user_name, status, amount, remark, created_at
            FROM orders
            WHERE order_id = :order_id""")

        row = self.db.execute(sql, {"order_id": order_id}).mappings().first()

        if row is None:
            return None
        return OrderInfo(
            id=row["id"],
            order_id=row["order_id"],
            user_name=row["user_name"],
            status=row["status"],
            amount=row["amount"],
            remark=row["remark"],
            created_at=row["created_at"]
        )

    def find_by_order_model_id(self, order_id: str) -> OrderModel | None:
        stmt = select(OrderModel).where(OrderModel.order_id == order_id)
        return self.db.scalars(stmt).first()


if __name__ == '__main__':
    with session_local() as db:
        orderMapper = OrderRepository(db)
        # result = orderMapper.find_by_order_id("OD1001")
        result = orderMapper.find_by_order_model_id("OD1001")

        if result is None:
            print("订单不存在")
        else:
            result_dict = {
                column.name: getattr(result, column.name)
                for column in result.__table__.columns
            }
            print(json.dumps(
                result_dict,
                ensure_ascii=False,
                default=str,
                indent=2,
            ))
