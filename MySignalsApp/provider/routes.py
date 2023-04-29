from flask import Blueprint,jsonify,request,session
from MySignalsApp.models import User,Signal
from MySignalsApp.utils import query_all_filtered, has_permission

provider=Blueprint("provider", __name__,url_prefix="/provider")

@provider.route("/signals")
def get_signals():
    user_id=has_permission(session, "Provider")
    signals= query_all_filtered(Signal,provider=user_id)

    return jsonify({
        "message": "Success",
        "signals":[signal.format() for signal in signals],
        "total":len(signals)
    }),200

    


