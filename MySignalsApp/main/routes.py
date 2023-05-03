from flask import jsonify, Blueprint, request, session
from MySignalsApp.models import User, Signal, get_uuid
from MySignalsApp.utils import (
    query_paginate_filtered,
    has_permission,
    query_one_filtered,
    is_active,
)
from binance.spot import Spot
from binance.cm_futures import CMFutures
from binance.error import ClientError
from time import sleep
from cryptography.fernet import Fernet
import os


main = Blueprint("main", __name__)

KEY = os.getenv("FERNET_KEY")

kryptr = Fernet(KEY.encode("utf-8"))


@main.route("/")
def get_active_signals():
    page = request.args.get("page", 1)
    try:
        signals = query_paginate_filtered(Signal, page, status=True)
        filtered_signals = []
        if not signals.items:
            return (
                jsonify(
                    {
                        "message": "Success",
                        "signals": filtered_signals,
                        "pages": signals.pages,
                        "total":signals.total
                    }
                ),
                200,
            )

        for signal in signals:
            filtered_signals.append(
                {
                    "id": signal.id,
                    "signal": {
                        "symbol": signal.signal.get("symbol"),
                        "side": signal.signal.get("side"),
                    },
                    "is_spot": signal.is_spot,
                    "provider": signal.user.wallet,
                    "date_created": signal.date_created,
                }
            )

        return (
            jsonify(
                {
                    "message": "Success",
                    "signals": filtered_signals,
                    "total": signals.total,
                    "pages": signal.pages,
                }
            ),
            200,
        )
    except Exception as e:
        print(e)
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                }
            ),
            500,
        )


@main.route("/spot/trade/<int:signal_id>", methods=["POST"])
def place_spot_trade(signal_id):
    user_id = has_permission(session, "User")
    user = is_active(User, user_id)
    #  TODO uncomment when hash check is implemented
    # tx_hash=(request.get_json()).get("tx_hash")
    # if not tx_hash:
    #     return (
    #         jsonify({"error": "Bad Request", "message": "tx hash missing"}),
    #         400,
    #     )

    user_api_key = kryptr.decrypt((user.api_key).encode("utf-8")).decode("utf-8")
    user_api_secret = kryptr.decrypt((user.api_secret).encode("utf-8")).decode("utf-8")

    spot_client = Spot(
        api_key=user_api_key,
        api_secret=user_api_secret,
        base_url="https://testnet.binance.vision",
    )
    # TODO check hash that correct signal.provider was paid
    signal = ""
    trade_uuid = get_uuid()
    try:
        signal = query_one_filtered(Signal, id=signal_id)
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
        if not signal.is_spot:
            return (
                jsonify(
                    {
                        "error": "Forbidden",
                        "message": "endpoint only accepts spot trades",
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

        return (
            jsonify(
                {
                    "message": "success",
                    "signal": {**params, "sl": stops.get("sl"), "tp": stops.get("tp")},
                }
            ),
            200,
        )

    except ClientError as e:
        if spot_client.get_order(signal["symbol"], origClientOrderId=trade_uuid):
            spot_client.cancel_order(signal["symbol"], origClientOrderId=trade_uuid)
        print(e)
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
        print(e)
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "It's not you it's us",
                }
            ),
            500,
        )


@main.route("/signal/<int:signal_id>")
def get_signal(signal_id):
    user_id = has_permission(session, "User")
    data = request.get_json()
    tx_hash = data.get("tx_hash")
    if not tx_hash:
        return (
            jsonify({"error": "Bad Request", "message": "tx hash missing"}),
            400,
        )
    user = is_active(User, user_id)
    try:
        signal = query_one_filtered(Signal, id=signal_id)
        # TODO check hash that correct signal.provider was paid use web3.py

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
