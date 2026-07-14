from decimal import Decimal

from ai_chat_service.app.db.session import session_local
from ai_chat_service.app.repositories.order_repository import OrderRepository, OrderInfo

MOCK_ORDERS = {
    "OD1001": {
        "order_id": "OD1001",
        "user_name": "张三",
        "status": "已支付",
        "amount": Decimal("199.00"),
        "remark": "预计明天发货",
    },
    "OD1002": {
        "order_id": "OD1002",
        "user_name": "李四",
        "status": "已发货",
        "amount": Decimal("89.90"),
        "remark": "快递单号 SF123456",
    },
    "OD1003": {
        "order_id": "OD1003",
        "user_name": "王五",
        "status": "已取消",
        "amount": Decimal("299.00"),
        "remark": "用户主动取消",
    },
}


def query_order(order_id: str):
    """
     根据订单号查询订单状态
    :param order_id:
    :return:
    """
    order = MOCK_ORDERS.get(order_id)
    if order is None:
        return f"没有查询到订单：{order_id}"

    return (
        f"订单号：{order['order_id']}\n"
        f"客户：{order['user_name']}\n"
        f"状态：{order['status']}\n"
        f"金额：{order['amount']} 元\n"
        f"说明：{order['remark']}"
    )


def query_online_orders(order_id: str) -> str:
    with session_local() as db:
        repository = OrderRepository(db)
        order = repository.find_by_order_id(order_id)
    if order is None:
        return f"没有查询到订单：{order_id}"
    return format_order(order)


def format_order(order: OrderInfo) -> str:
    return (
        f"订单号：{order.order_id}\n"
        f"客户：{order.user_name}\n"
        f"状态：{order.status}\n"
        f"金额：{order.amount} 元\n"
        f"说明：{order.remark}\n"
        f"创建时间：{order.created_at}"
    )


# 参考 https://developers.openai.com/api/docs/guides/tools?tool-type=function-calling
ORDER_TOOLS_SCHEMA = [
    {
        "type": "function",
        "name": "query_order",
        "description": "根据订单号查询订单状态、客户姓名、订单金额和物流说明。当用户想查询订单、物流、支付状态时使用这个工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "订单号，例如 OD1001、OD1002、OD1003",
                }
            },
            "required": ["order_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "query_online_orders",
        "description": "根据订单号在线查询订单状态、客户姓名、订单金额和物流说明。当用户想查询订单、物流、支付状态时使用这个工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "订单号，例如 OD1001、OD1002、OD1003",
                }
            },
            "required": ["order_id"],
            "additionalProperties": False,
        },
        "strict": True,
    }
]


def call_order_tool(name: str, arguments: dict) -> str:
    if name == "query_order":
        return query_order(arguments["order_id"])
    if name == "query_online_orders":
        return query_online_orders(arguments["order_id"])
    return f"未知工具：{name}"
