from flask import jsonify, Blueprint, request, session
from MySignalsApp.models import User, Signal
from MySignalsApp.utils import query_all_filtered, has_permission, query_one_filtered


main = Blueprint("main", __name__)


@main.route("/")
def get_active_signals():
    try:
        signals = query_all_filtered(Signal, status=True)
        filtered_signals = []
        if not signals:
            return (
                jsonify(
                    {
                        "message": "Success",
                        "signals": filtered_signals,
                        "total": len(filtered_signals),
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
                    "total": len(filtered_signals),
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


@main.route("/trade")
def place_trade():
    params = {
        "symbol": "BNBUSDT",
        "side": "BUY",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": "12",
        "price": "339",
    }

    tpparam = {
        "symbol": "BNBUSDT",
        "side": "SELL",
        "type": "TAKE_PROFIT_LIMIT",
        "stopPrice": "341",
        "timeInForce": "GTC",
        "quantity": "12",
    }
    # TODO check hash that correct signal.provider was paid
    try:
        # trade= spot_client.new_order(**params)
        # print(trade)
        # sleep(1)
        # trade2 = spot_client.new_order(**tpparam)
        # print(trade2)
        return (
            jsonify({"message": "success", "signal": {**params, "stopPrice": "341"}}),
            200,
        )
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
        # TODO check hash that correct signal.provider was paid

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
