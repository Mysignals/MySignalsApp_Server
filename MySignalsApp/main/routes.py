from MySignalsApp.models.users import User
from MySignalsApp.models.base import get_uuid
from MySignalsApp.models.signals import Signal
from MySignalsApp.models.provider_application import ProviderApplication
from MySignalsApp.models.placed_signals import PlacedSignals
from MySignalsApp.models.notifications import Notification
from flask import jsonify, Blueprint, request, session, current_app
from MySignalsApp.schemas import (
    ValidTxSchema,
    PageQuerySchema,
    IntQuerySchema,
    RatingSchema,
    ProviderApplicationSchema
)
from pydantic import ValidationError
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
from MySignalsApp.errors.handlers import UtilError
from MySignalsApp.web3_helpers import (
    verify_compensation_details,
    prepare_spot_trade,
    prepare_futures_trade,
)
from MySignalsApp import db
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
                    **signal.format(),
                    "signal": {
                        "symbol": signal.signal.get("symbol"),
                        "side": signal.signal.get("side"),
                        "quantity":signal.signal.get("quantity")
                    },
                    "provider_rating": calculate_rating(signal.provider),
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

    has_api_keys(user)

    user_api_key = kryptr.decrypt((user.api_key).encode("utf-8")).decode("utf-8")
    user_api_secret = kryptr.decrypt((user.api_secret).encode("utf-8")).decode("utf-8")

    spot_client = Spot(
        api_key=user_api_key,
        api_secret=user_api_secret
    )
    signal = ""
    trade_uuid = get_uuid()
    signal_data = IntQuerySchema(id=signal_id)
    try:
        placed_signal = query_one_filtered(
            PlacedSignals, signal_id=signal_data.id, user_id=user_id
        )

        if not placed_signal:
            return (
                jsonify(
                    {
                        "error": "Resource Not found",
                        "message": "Trade not found, Have you purchased this trade?",
                        "status": False,
                    }
                ),
                404,
            )
        signal = placed_signal.signal

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
        params, stops, stop_params = prepare_spot_trade(signal, trade_uuid)
        print(params, stops, stop_params)
        trade = spot_client.new_order(**params)
        sleep(1)
        trade2 = spot_client.new_oco_order(**stop_params)
        notify = Notification(
            user.id,
            f"Spot Signal {signal_data.id} order has been placed on your Binance Account",
        )
        notify.insert()

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
        return (
            jsonify(
                {
                    "error": e.error_code,
                    "message": f"{e.error_message} Warning: some orders might have been successful",
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


@main.route("/futures/trade/<int:signal_id>", methods=["POST"])
def place_futures_trade(signal_id):
    user_id = has_permission(session, "User")
    user = is_active(User, user_id)

    has_api_keys(user)

    user_api_key = kryptr.decrypt((user.api_key).encode("utf-8")).decode("utf-8")
    user_api_secret = kryptr.decrypt((user.api_secret).encode("utf-8")).decode("utf-8")

    futures_client = UMFutures(
        key=user_api_key,
        secret=user_api_secret
    )
    signal = ""
    trade_uuid = get_uuid()
    signal_data = IntQuerySchema(id=signal_id)
    try:
        placed_signal = query_one_filtered(
            PlacedSignals, signal_id=signal_data.id, user_id=user_id
        )
        if not placed_signal:
            return (
                jsonify(
                    {
                        "error": "Resource Not found",
                        "message": "Trade not found, Have you purchased this trade?",
                        "status": False,
                    }
                ),
                404,
            )

        signal = placed_signal.signal
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
        params, stops, stop_params, tp_params = prepare_futures_trade(
            signal, trade_uuid
        )

        lev = futures_client.change_leverage(signal["symbol"], signal["leverage"])
        futures_client.new_order(**params)
        sleep(1)
        futures_client.new_order(**stop_params)
        futures_client.new_order(**tp_params)
        notify = Notification(
            user.id,
            f"Futures Signal {signal_data.id} order has been placed on your Binance Account",
        )
        notify.insert()

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
                    "message": f"{e.error_message}. Warning: some orders might have been successful",
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


@main.route("/signal/<int:signal_id>", methods=["GET", "POST"])
def get_signal(signal_id):
    user_id = has_permission(session, "User")
    user = is_active(User, user_id)
    data = request.args.get("tx_hash", None)

    signal_data = ValidTxSchema(id=signal_id, tx_hash=data)

    try:
        signal = query_one_filtered(Signal, id=signal_data.id)

        if not signal:
            raise UtilError("Resource Not found", 404, "This signal Id does not exist")

        verify_compensation_details(
            signal_data.tx_hash, signal.user.wallet, user_id, signal_id
        )
        if not query_one_filtered(
            PlacedSignals, signal_id=signal_data.id, user_id=user_id
        ):
            placed_signal = PlacedSignals(user_id, signal_data.id, signal_data.tx_hash)
            notify_user = Notification(
                user.id, f"You Successfully purchased signal {signal_data.id}"
            )
            notify_provider = Notification(
                signal.user.id, f"Your Signal {signal_data.id} was purchased"
            )
            placed_signal.insert()
            if user.referrer:
                notify_referrer = Notification(
                    user.referrer.id,
                    f"You Earned referral Bonus from {user.user_name} on signal {signal_data.id}",
                )
                notify_referrer.insert()
            notify_provider.insert()
            notify_user.insert()

        return (
            jsonify({"message": "success", "signal": signal.format(), "status": True}),
            200,
        )
    except UtilError as e:
        return (
            jsonify({"error": e.error, "message": e.message, "status": False}),
            e.code,
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
        placed_signal = query_one_filtered(
            PlacedSignals, signal_id=signal_data.id, user_id=user_id
        )

        if not placed_signal:
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

        placed_signal.rating = rating.rate
        placed_signal.update()

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


@main.route("/mytrades")
def get_user_placed_signals():
    user_id = has_permission(session, "User")
    user = is_active(User, user_id)
    page = PageQuerySchema(page=request.args.get("page", 1))

    placed_signals = query_paginate_filtered(PlacedSignals, page.page, user_id=user_id)

    signal_data = (
        [
            {
                **data.signal.format(),
                "tx_hash": data.tx_hash,
                "user_rating": data.rating,
                "date_created": data.date_created,
            }
            for data in placed_signals
        ]
        if placed_signals
        else []
    )
    return (
        jsonify(
            {
                "message": "success",
                "mytrades": signal_data,
                "status": True,
                "total": placed_signals.total,
                "pages": placed_signals.pages,
            }
        ),
        200,
    )

@main.route("/apply/provider",methods=["POST"])
def apply_provider():
    user_id = has_permission(session, "User")
    user = is_active(User, user_id)
    try:
        data=ProviderApplicationSchema()
    except ValidationError as e:
        msg=[f"{err['loc'][0]}: {err['msg']}." for err in e.errors()]
        msg="\n".join(msg)
        raise UtilError("Bad Request",400,msg)
    if(query_one_filtered(ProviderApplication, user_id=user_id)): 
        raise UtilError("Forbidden", 403, "You have already applied in the past")

    application=ProviderApplication(user_id, data.wallet, data.experience, data.socials_and_additional)
    application.insert()
    return jsonify({
        "message":"success", 
        "status":True
    }), 200

    