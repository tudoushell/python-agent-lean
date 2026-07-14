from dataclasses import asdict

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session

from ai_chat_service.app.db.session import get_db
from ai_chat_service.app.repositories.order_repository import OrderRepository

router = APIRouter(prefix="/orders", tags=["order"])


@router.get("/order/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db)):
    repository = OrderRepository(db)
    order = repository.find_by_order_id(order_id)

    if order is None:
        return {
            "code": "ORDER_NOT_FOUND",
            "message": f"订单不存在：{order_id}",
            "data": None,
        }
    return {
        "code": "SUCCESS",
        "message": "成功",
        "data": asdict(order)
    }
