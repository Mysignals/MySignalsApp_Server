from flask import Blueprint, jsonify, request, session
from MySignalsApp.models import User, Signal
from MySignalsApp.utils import query_all_filtered, has_permission, query_one_filtered
from binance.spot import Spot
from binance.error import ClientError
from dotenv import load_dotenv
import os
from time import sleep


load_dotenv(".env")


provider = Blueprint("provider", __name__, url_prefix="/provider")

spot_key = os.environ.get("SKEY")
spot_sec = os.environ.get("SSEC")

f_key = os.environ.get("FKEY")
f_sec = os.environ.get("FSEC")

spot_client = Spot(
    api_key=spot_key, api_secret=spot_sec, base_url="https://testnet.binance.vision"
)


@provider.route("/signals")
def get_signals():
    user_id = has_permission(session, "Provider")
    try:
        is_active = (query_one_filtered(User, id=user_id)).is_active
        if not is_active:
            return (
                jsonify(
                    {"error": "Unauthorized", "message": "Your account is not active"}
                ),
                401,
            )

        signals = query_all_filtered(Signal, provider=user_id)

        return (
            jsonify(
                {
                    "message": "Success",
                    "signals": [signal.format() for signal in signals],
                    "total": len(signals),
                }
            ),
            200,
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
def get_spot_pairs():
    try:
        usdt_symbols = spot_client.exchange_info(permissions=["SPOT"])["symbols"]
        pairs = []
        if not usdt_symbols:
            return jsonify({"message": "success", "pairs": pairs}), 200
        for symbol in usdt_symbols:
            if symbol["symbol"][-4:] == "USDT":
                pairs.append(symbol["symbol"])
        return jsonify({"message": "success", "pairs": pairs}), 200
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
def get_futures_pairs():
    try:
        usdt_symbols = spot_client.exchange_info(permissions=["MARGIN"])["symbols"]
        pairs = []
        if not usdt_symbols:
            return jsonify({"message": "success", "pairs": pairs}), 200
        for symbol in usdt_symbols:
            if symbol["symbol"][-4:] == "USDT":
                pairs.append(symbol["symbol"])
        return jsonify({"message": "success", "pairs": pairs}), 200
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


@provider.route("/update_wallet", methods=["POST"])
def change_wallet():
    user_id = has_permission(session, "Provider")
    data = request.get_json()
    wallet = data.get("wallet")
    if not wallet or len(wallet) != 42:
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": "Did you provide all fields correctly?",
                }
            ),
            400,
        )

    try:
        user = query_one_filtered(User, id=user_id)
        if not user.is_active:
            return (
                jsonify(
                    {"error": "Unauthorized", "message": "Your account is not active"}
                ),
                401,
            )
        user.wallet = wallet
        user.update()

        return jsonify({"message": "Password changed"}), 200
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
        return spot_client.account()
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
    symbol = data.get("symbol")
    side = data.get("side")
    quantity = data.get("quantity")
    price = data.get("price")
    sl = data.get("sl")
    tp = data.get("tp")

    if not (symbol and side and quantity and price and sl and tp):
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": "Did you provide all fields correctly?",
                }
            ),
            400,
        )
    signal_data = dict(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        stops=dict(sl=sl, tp=tp),
    )
    try:
        user = query_one_filtered(User, id=user_id)
        if not user.is_active:
            return (
                jsonify(
                    {"error": "Unauthorized", "message": "Your account is not active"}
                ),
                401,
            )

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


@provider.route("/delete/<int:signal_id>", methods=["POST"])
def delete_trade(signal_id):
    user_id = has_permission(session, "Provider")
    try:
        user = query_one_filtered(User, id=user_id)
        if not user.is_active:
            return (
                jsonify(
                    {"error": "Unauthorized", "message": "Your account is not active"}
                ),
                401,
            )
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

        if signal.provider != user_id:
            return (
                jsonify(
                    {
                        "error": "Unauthorized",
                        "message": "You do not have permission to delete this Signal",
                    }
                ),
                401,
            )

        signal.delete()
        return jsonify({"message": "success", "signal_id": signal.id})
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
