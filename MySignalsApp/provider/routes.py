from flask import Blueprint, jsonify, request, session
from MySignalsApp.models import User, Signal
from MySignalsApp.utils import query_all_filtered, has_permission
from binance.spot import Spot


provider = Blueprint("provider", __name__, url_prefix="/provider")

spot_client = Spot()


@provider.route("/signals")
def get_signals():
    user_id = has_permission(session, "Provider")
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
