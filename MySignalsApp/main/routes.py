from flask import jsonify, Blueprint
from MySignalsApp.models import User, Signal


main = Blueprint("main", __name__)


@main.route("/")
def get_active_signals():
    signals = query_all_filtered(Signal, status=True)

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
