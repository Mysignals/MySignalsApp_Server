from MySignalsApp.schemas import (
    WalletSchema,
    SpotSchema,
    FuturesSchema,
    IntQuerySchema,
    PageQuerySchema,
)
from flask import Blueprint, jsonify, request, session, current_app
from MySignalsApp.web3_helpers import prepare_futures_trade, prepare_spot_trade
from MySignalsApp.models.users import User
from MySignalsApp.models.base import get_uuid
from MySignalsApp.models.signals import Signal
from MySignalsApp.models.notifications import Notification
from binance.um_futures import UMFutures
from binance.error import ClientError
from binance.spot import Spot
from MySignalsApp import cache
from MySignalsApp.utils import (
    query_paginate_filtered,
    has_permission,
    query_one_filtered,
    is_active,
    calculate_rating,
    send_tg_notification,
)
from binance.spot import Spot
import os

provider = Blueprint("provider", __name__, url_prefix="/provider")


@provider.route("/signals")
def get_signals():
    user_id = has_permission(session, "Provider")
    user = is_active(User, user_id)
    page = PageQuerySchema(page=request.args.get("page", 1))
    try:
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
                    "provider_rating": calculate_rating(user_id),
                    "status": True,
                }
            ),
            200,
        )
    except Exception as e:
        current_app.log_exception(exc_info=e)
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                    "status": False,
                }
            ),
            500,
        )


@provider.route("/spot/pairs")
@cache.cached(timeout=432000)  # 5 days
def get_spot_pairs():
    user_id = has_permission(session, "Provider")
    user = is_active(User, user_id)
    try:
        spot_client = Spot()

        usdt_symbols = spot_client.exchange_info(permissions=["SPOT"])["symbols"]

        if not usdt_symbols:
            return jsonify({"message": "success", "pairs": [], "status": True}), 200

        pairs = [
            symbol["symbol"]
            for symbol in usdt_symbols
            if symbol["quoteAsset"] == "USDT"
        ]

        return (
            jsonify({"message": "success", "pairs": sorted(pairs), "status": True}),
            200,
        )
    except ClientError as e:
        return (
            jsonify(
                {"error": e.error_code, "message": e.error_message, "status": False}
            ),
            e.status_code,
        )
    except Exception as e:
        current_app.log_exception(exc_info=e)
        return (
            jsonify(
                {"error": e.error_code, "message": e.error_message, "status": False}
            ),
            e.status_code,
        )


@provider.route("/futures/pairs")
@cache.cached(timeout=432000)  # 5 days
def get_futures_pairs():
    user_id = has_permission(session, "Provider")
    user = is_active(User, user_id)
    try:
        futures_client = UMFutures()
        usdt_symbols = futures_client.exchange_info()["symbols"]
        if not usdt_symbols:
            return jsonify({"message": "success", "pairs": [], "status": True}), 200

        pairs = [
            symbol["symbol"]
            for symbol in usdt_symbols
            if symbol["quoteAsset"] == "USDT" and symbol["contractType"] == "PERPETUAL"
        ]
        return (
            jsonify({"message": "success", "pairs": sorted(pairs), "status": True}),
            200,
        )
    except ClientError as e:
        return (
            jsonify(
                {"error": e.error_code, "message": e.error_message, "status": False}
            ),
            e.status_code,
        )
    except Exception as e:
        current_app.log_exception(exc_info=e)
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                    "status": False,
                }
            ),
            500,
        )


@provider.route("/update_wallet", methods=["POST"])
def change_wallet():
    user_id = has_permission(session, "Provider")
    data = request.get_json()

    user = is_active(User, user_id)
    data = WalletSchema(**data)
    try:
        user.wallet = data.wallet
        user.update()
        notify = Notification(
            user.id, f"Your Wallet Address was Successfully Changed to {user.wallet}"
        )
        notify.insert()
        return jsonify({"message": "Wallet changed", "status": True}), 200
    except Exception as e:
        current_app.log_exception(exc_info=e)
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                    "status": False,
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
                {"error": e.error_code, "message": e.error_message, "status": False}
            ),
            e.status_code,
        )


@provider.route("/spot/new", methods=["POST"])
def new_spot_trade():
    user_id = has_permission(session, "Provider")
    user = is_active(User, user_id)

    if not user.wallet:
        return (
            jsonify(
                {
                    "error": "Forbidden",
                    "message": "Provider has no wallet address",
                    "status": False,
                }
            ),
            403,
        )

    data = request.get_json()
    data = SpotSchema(**data)

    signal_data = dict(
        symbol=data.symbol,
        side="BUY",
        quantity=data.quantity,
        price=data.price,
        stops=dict(sl=data.sl, tp1=data.tp1, tp2=data.tp2, tp3=data.tp3),
    )

    spot_client = Spot(
        api_key=os.getenv("SKEY"),
        api_secret=os.getenv("SSEC"),
        base_url="https://testnet.binance.vision",
    )
    params, _, stop_params = prepare_spot_trade(
        signal_data, get_uuid(), data.tp1, data.quantity
    )
    spot_client.new_order_test(**params)
    spot_client.new_oco_order(**stop_params)

    send_tg_notification(
        user.user_name, "SPOT", signal_data.get("side"), signal_data.get("symbol")
    )
    try:
        signal = Signal(signal_data, True, user_id, True, data.short_text)
        signal.insert()
        return (
            jsonify({"message": "success", "signal": signal.format(), "status": True}),
            200,
        )
    except Exception as e:
        current_app.log_exception(exc_info=e)
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                    "status": False,
                }
            ),
            500,
        )


@provider.route("/futures/new", methods=["POST"])
def new_futures_trade():
    user_id = has_permission(session, "Provider")
    user = is_active(User, user_id)

    if not user.wallet:
        return (
            jsonify(
                {
                    "error": "Forbidden",
                    "message": "Provider has no wallet address",
                    "status": False,
                }
            ),
            403,
        )

    data = request.get_json()
    data = FuturesSchema(**data)

    signal_data = dict(
        symbol=data.symbol,
        side=data.side,
        quantity=data.quantity,
        price=data.price,
        leverage=data.leverage,
        stops=dict(sl=data.sl, tp1=data.tp1, tp2=data.tp2, tp3=data.tp3),
    )

    futures_client = UMFutures(
        key=os.getenv("FKEY"),
        secret=os.getenv("FSEC"),
        base_url="https://testnet.binancefuture.com",
    )
    params, _, stop_params, tp_params = prepare_futures_trade(
        signal_data, get_uuid(), data.tp1, data.quantity, data.leverage
    )
    futures_client.new_order_test(**params)
    futures_client.new_order_test(**stop_params)
    futures_client.new_order_test(**tp_params)

    send_tg_notification(
        user.user_name, "FUTURES", signal_data.get("side"), signal_data.get("symbol")
    )
    try:
        signal = Signal(signal_data, True, user_id, False, data.short_text)
        signal.insert()
        return (
            jsonify({"message": "success", "signal": signal.format(), "status": True}),
            200,
        )
    except Exception as e:
        current_app.log_exception(exc_info=e)
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                    "status": False,
                }
            ),
            500,
        )


@provider.route("/delete/<int:signal_id>", methods=["POST"])
def delete_trade(signal_id):
    user_id = has_permission(session, "Provider")
    user = is_active(User, user_id)
    signal_id = IntQuerySchema(id=signal_id)
    try:
        signal = query_one_filtered(Signal, id=signal_id.id)
        if not signal:
            return (
                jsonify(
                    {
                        "error": "Resource Not found",
                        "message": "The signal with the provided Id does not exist",
                        "status": False,
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
                        "status": False,
                    }
                ),
                403,
            )

        signal.delete()
        return jsonify({"message": "success", "signal_id": signal.id, "status": True})
    except Exception as e:
        current_app.log_exception(exc_info=e)
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                    "status": False,
                }
            ),
            500,
        )


@provider.route("/deactivate/<int:signal_id>", methods=["POST"])
def deactivate_trade(signal_id):
    user_id = has_permission(session, "Provider")
    user = is_active(User, user_id)
    signal_id = IntQuerySchema(id=signal_id)
    try:
        signal = query_one_filtered(Signal, id=signal_id.id)
        if not signal:
            return (
                jsonify(
                    {
                        "error": "Resource Not found",
                        "message": "The signal with the provided Id does not exist",
                        "status": False,
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
                        "status": False,
                    }
                ),
                403,
            )
        signal.status = False
        signal.update()
        return jsonify({"message": "success", "signal_id": signal.id, "status": True})
    except Exception as e:
        current_app.log_exception(exc_info=e)
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                    "status": False,
                }
            ),
            500,
        )
