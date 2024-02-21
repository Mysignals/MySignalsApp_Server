from MySignalsApp.models.base import BaseModel
from MySignalsApp import db, admin
from flask import session, flash, redirect
from flask_admin.contrib.sqla import ModelView

class ProviderApplication(BaseModel):
    __tablename__="providerappliications"
    id = db.Column(db.Integer(), primary_key=True, unique=True, nullable=False)
    user_id=db.Column(db.String(34),db.ForeignKey("users.id"),unique=True,nullable=False)
    user=db.Relationship("User",back_populates="provider_application",lazy=True)
    wallet=db.Column(db.String(42),nullable=False)
    experience=db.Column(db.String(300),nullable=False)
    socials_and_additional=db.Column(db.String(500),nullable=False)

    def __init__(self,user_id,wallet,experience,socials_and_additional):
        self.user_id=user_id
        self.wallet=wallet
        self.experience=experience
        self.socials_and_additional=socials_and_additional

    def __repr__(self):
        return f"username({self.user.user_name}, wallet({self.wallet}), experience({self.experience}))"
    
    def format(self):
        return {
            "id":self.id,
            "user":self.user.user_name,
            "wallet":self.wallet,
            "experience":self.experience,
            "socials_and_additional":self.socials_and_additional,
            "date_created":self.date_created
        }
    
class ProviderApplicationView(ModelView):
    def is_accessible(self):
        user = session.get("user") if session else None
        return "Registrar" in user.get("permission") if user else False


    def inaccessible_callback(self, name, **kwargs):
        flash("You are not Authorized", category="error")
        return redirect("/admin/login", 302)
    
    column_list=[
        "id", 
        "user.user_name", 
        "wallet", 
        "experience", 
        "socials_and_additional", 
        "date_created"
    ]
    form_columns=[
        "user", 
        "wallet", 
        "experience", 
        "socials_and_additional", 
        "date_created"
    ]
    column_searchable_list = ["user_id","user.user_name", "wallet"]
    column_filters = ["date_created"]

admin.add_view(ProviderApplicationView(ProviderApplication,db.session))