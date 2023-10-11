from MySignalsApp.schemas import (
    WalletSchema,
    SpotSchema,
    FuturesSchema,
    IntQuerySchema,
    PageQuerySchema,
)
from flask import Blueprint, jsonify, request, session
from MySignalsApp.models import User, Signal
from binance.um_futures import UMFutures
from binance.error import ClientError
from pydantic import ValidationError
from MySignalsApp import cache, db
from MySignalsApp.utils import (
    query_paginate_filtered,
    has_permission,
    query_one_filtered,
    is_active,
)
from binance.spot import Spot

provider = Blueprint("provider", __name__, url_prefix="/provider")


@provider.route("/signals")
def get_signals():
    user_id = has_permission(session, "Provider")
    user = is_active(User, user_id)
    try:
        page = PageQuerySchema(request.args.get("page", 1))
        signals = query_paginate_filtered(Signal, page.page, provider=user_id)

        return (
            jsonify(
                {
                    "message": "Success",
                    "signals": [signal.format() for signal in signals]
                    if signals.items
                    else [],
                    "total": signals.total,
                    "pages": signals.pages,
                }
            ),
            200,
        )
    except ValidationError as e:
        msg = []
        for err in e.errors():
            msg.append({"field": err["loc"][0], "error": err["msg"]})
        return (
            jsonify({"error": "Bad Request", "message": msg}),
            400,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                }
            ),
            500,
        )


@provider.route("/spot/pairs")
@cache.cached(timeout=1296000)  # 15 days
def get_spot_pairs():
    user_id = has_permission(session, "Provider")
    user = is_active(User, user_id)
    try:
        spot_client = Spot()

        usdt_symbols = spot_client.exchange_info(permissions=["SPOT"])["symbols"]
        pairs = []
        if not usdt_symbols:
            return jsonify({"message": "success", "pairs": pairs}), 200
        for symbol in usdt_symbols:
            if symbol["symbol"][-4:] == "USDT":
                pairs.append(symbol["symbol"])
        return jsonify({"message": "success", "pairs": pairs}), 200
    except ClientError as e:
        return (
            jsonify(
                {
                    "error": e.error_code,
                    "message": e.error_message,
                }
            ),
            e.status_code,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": e.error_code,
                    "message": e.error_message,
                }
            ),
            e.status_code,
        )


@provider.route("/futures/pairs")
@cache.cached(timeout=1296000)  # 15 days
def get_futures_pairs():
    user_id = has_permission(session, "Provider")
    user = is_active(User, user_id)
    try:
        futures_client = UMFutures(base_url="https://testnet.binancefuture.com")
        usdt_symbols = futures_client.exchange_info()["symbols"]
        pairs = []
        if not usdt_symbols:
            return jsonify({"message": "success", "pairs": pairs}), 200
        for symbol in usdt_symbols:
            if (
                symbol["symbol"][-4:] == "USDT"
                and symbol["contractType"] == "PERPETUAL"
            ):
                pairs.append(symbol["symbol"])
        return jsonify({"message": "success", "pairs": pairs}), 200
    except ClientError as e:
        return (
            jsonify(
                {
                    "error": e.error_code,
                    "message": e.error_message,
                }
            ),
            e.status_code,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                }
            ),
            500,
        )


@provider.route("/update_wallet", methods=["POST"])
def change_wallet():
    user_id = has_permission(session, "Provider")
    data = request.get_json()

    user = is_active(User, user_id)
    try:
        data = WalletSchema(**data)
        user.wallet = data.wallet
        user.update()

        return jsonify({"message": "Wallet changed"}), 200
    except ValidationError as e:
        msg = []
        for err in e.errors():
            msg.append({"field": err["loc"][0], "error": err["msg"]})
        return (
            jsonify({"error": "Bad Request", "message": msg}),
            400,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                }
            ),
            500,
        )


# test server is connected
@provider.route("/time")
def get_time():
    try:
        return Spot().ping()
    except ClientError as e:
        return (
            jsonify(
                {
                    "error": e.error_code,
                    "message": e.error_message,
                }
            ),
            e.status_code,
        )


@provider.route("/spot/new", methods=["POST"])
def new_spot_trade():
    user_id = has_permission(session, "Provider")

    data = request.get_json()
    try:
        data = SpotSchema(**data)
    except ValidationError as e:
        msg = []
        for err in e.errors():
            msg.append({"field": err["loc"][0], "error": err["msg"]})
        return (
            jsonify({"error": "Bad Request", "message": msg}),
            400,
        )

    signal_data = dict(
        symbol=data.symbol,
        side=data.side,
        quantity=data.quantity,
        price=data.price,
        stops=dict(sl=data.sl, tp=data.tp),
    )
    user = is_active(User, user_id)
    if not user.wallet:
        return (
            jsonify(
                {"error": "Forbidden", "message": "Provider has no wallet address "}
            ),
            403,
        )
    try:
        signal = Signal(signal_data, True, user_id)
        signal.insert()
        return jsonify({"message": "success", "signal": signal.format()}), 200
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                }
            ),
            500,
        )


@provider.route("/futures/new", methods=["POST"])
def new_futures_trade():
    user_id = has_permission(session, "Provider")

    data = request.get_json()
    try:
        data = FuturesSchema(**data)
    except ValidationError as e:
        msg = []
        for err in e.errors():
            msg.append({"field": err["loc"][0], "error": err["msg"]})
        return (
            jsonify({"error": "Bad Request", "message": msg}),
            400,
        )

    signal_data = dict(
        symbol=data.symbol,
        side=data.side,
        quantity=data.quantity,
        price=data.price,
        leverage=data.leverage,
        stops=dict(sl=data.sl, tp=data.tp),
    )
    user = is_active(User, user_id)
    if not user.wallet:
        return (
            jsonify(
                {"error": "Forbidden", "message": "Provider has no wallet address "}
            ),
            403,
        )
    try:
        signal = Signal(signal_data, True, user_id, is_spot=False)
        signal.insert()
        return jsonify({"message": "success", "signal": signal.format()}), 200
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                }
            ),
            500,
        )


@provider.route("/delete/<int:signal_id>", methods=["POST"])
def delete_trade(signal_id):
    user_id = has_permission(session, "Provider")
    user = is_active(User, user_id)
    try:
        signal_id = IntQuerySchema(id=signal_id)
        signal = query_one_filtered(Signal, id=signal_id.id)
        if not signal:
            return (
                jsonify(
                    {
                        "error": "Resource Not found",
                        "message": "The signal with the provided Id does not exist",
                    }
                ),
                404,
            )

        if signal.provider != user_id:
            return (
                jsonify(
                    {
                        "error": "Forbidden",
                        "message": "You do not have permission to delete this Signal",
                    }
                ),
                403,
            )

        signal.delete()
        return jsonify({"message": "success", "signal_id": signal.id})
    except ValidationError as e:
        msg = []
        for err in e.errors():
            msg.append({"field": err["loc"][0], "error": err["msg"]})
        return (
            jsonify({"error": "Bad Request", "message": msg}),
            400,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                }
            ),
            500,
        )


@provider.route("/deactivate/<int:signal_id>", methods=["POST"])
def deactivate_trade(signal_id):
    user_id = has_permission(session, "Provider")
    user = is_active(User, user_id)
    try:
        signal_id = IntQuerySchema(id=signal_id)
        signal = query_one_filtered(Signal, id=signal_id.id)
        if not signal:
            return (
                jsonify(
                    {
                        "error": "Resource Not found",
                        "message": "The signal with the provided Id does not exist",
                    }
                ),
                404,
            )

        if signal.provider != user_id:
            return (
                jsonify(
                    {
                        "error": "Forbidden",
                        "message": "You do not have permission to edit this Signal",
                    }
                ),
                403,
            )
        signal.status = False
        signal.update()
        return jsonify({"message": "success", "signal_id": signal.id})
    except ValidationError as e:
        msg = []
        for err in e.errors():
            msg.append({"field": err["loc"][0], "error": err["msg"]})
        return (
            jsonify({"error": "Bad Request", "message": msg}),
            400,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                }
            ),
            500,
        )
