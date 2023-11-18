from MySignalsApp.models.users import User
from MySignalsApp.models.base import get_uuid
from MySignalsApp.models.signals import Signal
from MySignalsApp.models.placed_signals import PlacedSignals
from flask import jsonify, Blueprint, request, session, current_app
from MySignalsApp.schemas import (
    ValidTxSchema,
    PageQuerySchema,
    IntQuerySchema,
    RatingSchema,
)
from binance.um_futures import UMFutures
from cryptography.fernet import Fernet
from binance.error import ClientError
from MySignalsApp.utils import (
    query_paginate_filtered,
    has_permission,
    query_one_filtered,
    calculate_rating,
    has_api_keys,
    is_active,
)
from binance.spot import Spot
from time import sleep
import os


main = Blueprint("main", __name__)

KEY = os.getenv("FERNET_KEY")

kryptr = Fernet(KEY.encode("utf-8"))


@main.route("/")
def get_active_signals():
    page = PageQuerySchema(page=request.args.get("page", 1))
    try:
        signals = query_paginate_filtered(Signal, page.page, status=True)

        filtered_signals = (
            [
                {
                    "id": signal.id,
                    "signal": {
                        "symbol": signal.signal.get("symbol"),
                        "side": signal.signal.get("side"),
                    },
                    "is_spot": signal.is_spot,
                    "provider": signal.user.user_name,
                    "provider_wallet": signal.user.wallet,
                    "provider_rating": calculate_rating(signal.user.id),
                    "date_created": signal.date_created,
                }
                for signal in signals
            ]
            if signals.items
            else []
        )

        return (
            jsonify(
                {
                    "message": "Success",
                    "signals": filtered_signals,
                    "total": signals.total,
                    "pages": signals.pages,
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


@main.route("/spot/trade/<int:signal_id>", methods=["POST"])
def place_spot_trade(signal_id):
    user_id = has_permission(session, "User")
    user = is_active(User, user_id)

    tx_hash = (request.get_json()).get("tx_hash")

    has_api_keys(user)

    user_api_key = kryptr.decrypt((user.api_key).encode("utf-8")).decode("utf-8")
    user_api_secret = kryptr.decrypt((user.api_secret).encode("utf-8")).decode("utf-8")

    spot_client = Spot(
        api_key=user_api_key,
        api_secret=user_api_secret,
        base_url="https://testnet.binance.vision",
    )
    signal = ""
    trade_uuid = get_uuid()
    signal_data = ValidTxSchema(id=signal_id, tx_hash=tx_hash)
    try:
        # TODO check signal_data.tx_hash that correct signal.provider was paid
        signal = query_one_filtered(Signal, id=signal_data.id)
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
        if not signal.is_spot:
            return (
                jsonify(
                    {
                        "error": "Forbidden",
                        "message": "endpoint only accepts spot trades",
                        "status": False,
                    }
                ),
                403,
            )
        signal = signal.signal

        params = {
            "symbol": signal["symbol"],
            "side": signal["side"],
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": signal["quantity"],
            "price": signal["price"],
            "newClientOrderId": trade_uuid,
        }
        stops = signal["stops"]

        stop_param = {
            "symbol": signal["symbol"],
            "side": "SELL" if signal["side"] == "BUY" else "BUY",
            "price": stops["tp"],
            "quantity": signal["quantity"],
            "stopPrice": stops["sl"],
            "stopLimitPrice": stops["sl"],
            "stopLimitTimeInForce": "GTC",
        }
        trade = spot_client.new_order(**params)
        sleep(1)
        trade2 = spot_client.new_oco_order(**stop_param)

        placed_signal = PlacedSignals(user_id, signal_data.id)
        placed_signal.insert()

        return (
            jsonify(
                {
                    "message": "success",
                    "signal": {**params, "sl": stops.get("sl"), "tp": stops.get("tp")},
                    "status": True,
                }
            ),
            200,
        )
    except ClientError as e:
        if spot_client.get_order(signal["symbol"], origClientOrderId=trade_uuid):
            spot_client.cancel_order(signal["symbol"], origClientOrderId=trade_uuid)
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


@main.route("/futures/trade/<int:signal_id>", methods=["POST"])
def place_futures_trade(signal_id):
    user_id = has_permission(session, "User")
    user = is_active(User, user_id)
    #  TODO uncomment when hash check is implemented
    tx_hash = (request.get_json()).get("tx_hash")

    has_api_keys(user)

    user_api_key = kryptr.decrypt((user.api_key).encode("utf-8")).decode("utf-8")
    user_api_secret = kryptr.decrypt((user.api_secret).encode("utf-8")).decode("utf-8")

    futures_client = UMFutures(
        key=user_api_key,
        secret=user_api_secret,
        base_url="https://testnet.binancefuture.com",
    )
    # TODO check signal_data.tx_hash that correct signal.provider was paid
    signal = ""
    trade_uuid = get_uuid()
    signal_data = ValidTxSchema(id=signal_id, tx_hash=tx_hash)
    try:
        signal = query_one_filtered(Signal, id=signal_data.id)
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
        if signal.is_spot:
            return (
                jsonify(
                    {
                        "error": "Forbidden",
                        "message": "endpoint only accepts futures trades",
                        "status": False,
                    }
                ),
                403,
            )
        signal = signal.signal

        params = {
            "symbol": signal["symbol"],
            "side": signal["side"],
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": signal["quantity"],
            "price": signal["price"],
            "newClientOrderId": trade_uuid,
        }
        stops = signal["stops"]

        stop_param = {
            "symbol": signal["symbol"],
            "side": "SELL" if signal["side"] == "BUY" else "BUY",
            "closePosition": "true",
            "type": "STOP_MARKET",
            "stopPrice": stops["sl"],
            "quantity": signal["quantity"],
        }
        tp_param = {
            "symbol": signal["symbol"],
            "side": "SELL" if signal["side"] == "BUY" else "BUY",
            "stopPrice": stops["tp"],
            "quantity": signal["quantity"],
            "closePosition": "true",
            "type": "TAKE_PROFIT_MARKET",
        }
        lev = futures_client.change_leverage(signal["symbol"], signal["leverage"])
        futures_client.new_order(**params)
        sleep(1)
        futures_client.new_order(**stop_param)
        futures_client.new_order(**tp_param)

        placed_signal = PlacedSignals(user_id, signal_data.id)
        placed_signal.insert()

        return (
            jsonify(
                {
                    "message": "success",
                    "signal": {
                        **params,
                        "sl": stops.get("sl"),
                        "tp": stops.get("tp"),
                        "leverage": signal["leverage"],
                    },
                    "status": True,
                }
            ),
            200,
        )
    except ClientError as e:
        return (
            jsonify(
                {
                    "error": e.error_code,
                    "message": f"{e.error_message}. Warning: some orders might have been successfull",
                    "status": False,
                }
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


@main.route("/signal/<int:signal_id>")
def get_signal(signal_id):
    user_id = has_permission(session, "User")
    user = is_active(User, user_id)
    data = request.args.get("tx_hash", None)

    signal_data = ValidTxSchema(id=signal_id, tx_hash=data)
    try:
        signal = query_one_filtered(Signal, id=signal_data.id)
        placed_signal = PlacedSignals(user_id, signal_data.id)
        placed_signal.insert()
        # TODO check hash that correct signal.provider was paid use web3.py

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


@main.route("/signal/rate/<int:signal_id>", methods=["POST"])
def rate_signal(signal_id):
    user_id = has_permission(session, "User")
    user = is_active(User, user_id)
    rating = request.get_json()

    signal_data = IntQuerySchema(id=signal_id)
    rating = RatingSchema(rate=rating.get("rate"))
    try:
        signal = query_one_filtered(PlacedSignals, signal_id=signal_data.id)

        if not signal:
            return (
                jsonify(
                    {
                        "error": "Resource Not found",
                        "message": "Trade not found, Did you take this trade?",
                        "status": False,
                    }
                ),
                404,
            )

        signal.rating = rating.rate
        signal.update()

        return (
            jsonify({"message": "success", "rating": rating.rate, "status": True}),
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
