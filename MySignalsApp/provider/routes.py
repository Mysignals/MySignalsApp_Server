from flask import Blueprint, jsonify, request, session
from MySignalsApp.models import User, Signal
from MySignalsApp.utils import query_all_filtered, has_permission, query_one_filtered
from binance.spot import Spot
from dotenv import load_dotenv
import os



load_dotenv(".env")


provider = Blueprint("provider", __name__, url_prefix="/provider")

key=os.environ.get("SKEY")
sec=os.environ.get("SSEC")

spot_client = Spot(api_key=key,api_secret=sec,base_url='https://testnet.binance.vision')


@provider.route("/signals")
def get_signals():
    user_id = has_permission(session, "Provider")
    try:
        is_active = (query_one_filtered(User, id=user_id)).is_active
        # if not is_active:
        #     return (
        #         jsonify({"error": "Unauthorized", "message": "Your account is not active"}),
        #         401,
        #     )

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
        for symbol in usdt_symbols:
            if symbol["symbol"][-4:] == "USDT":
                pairs.append(symbol["symbol"])
        return jsonify({"message": "success", "pairs": pairs}), 200
    except Exception as e:
        return (
            jsonify({"message": "error accessing binance", "error": e.get("msg")}),
            500,
        )


@provider.route("/futures/pairs")
def get_futures_pairs():
    try:
        usdt_symbols = spot_client.exchange_info(permissions=["MARGIN"])["symbols"]
        pairs = []
        for symbol in usdt_symbols:
            if symbol["symbol"][-4:] == "USDT":
                pairs.append(symbol["symbol"])
        return jsonify({"message": "success", "pairs": pairs}), 200
    except Exception as e:
        return (
            jsonify({"message": "error accessing binance", "error": e.get("msg")}),
            500,
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
        # if not user.is_active:
        #     return (
        #         jsonify({"error": "Unauthorized", "message": "Your account is not active"}),
        #         401,
        #     )
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
    except Exception as e:
        print(e)
        return jsonify({
            "error":e.error_code,
            "message":e.error_message,
        }),e.status_code