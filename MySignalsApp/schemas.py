from pydantic import BaseModel, constr, EmailStr, validator, EmailError
from email_validator import validate_email, EmailNotValidError, EmailUndeliverableError
from uuid import UUID
from web3 import Web3


class RegisterSchema(BaseModel):
    email: EmailStr
    user_name: constr(
        regex=r"^[a-zA-Z0-9_]+$", to_lower=True, max_length=345, min_length=1
    )
    wallet: constr(min_length=42, max_length=42)
    password: constr(max_length=64, min_length=8)
    confirm_password: constr(max_length=64, min_length=8)
    referral_code: constr(max_length=8, min_length=0)

    @validator("email")
    def valid_email_length(cls, v):
        try:
            validate_email(v, check_deliverability=True)
        except (EmailNotValidError, EmailUndeliverableError) as e:
            raise EmailError() from e
        return v

    @validator("wallet")
    def valid_wallet_hex(cls, v):
        # if "0x" not in v[:2]:
        #     raise ValueError("Invalid wallet Address")
        # return v
        try:
            addr = Web3.to_checksum_address(v)
            return addr
        except:
            raise ValueError("Invalid wallet Address")

    @validator("confirm_password")
    def passwords_are_same(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v


class LoginSchema(BaseModel):
    user_name_or_mail: constr(to_lower=True)
    password: str


class UpdateKeysSchema(BaseModel):
    api_key: constr(max_length=100)
    api_secret: constr(max_length=100)


class StringUUIDQuerySchema(BaseModel):
    token: UUID

    @validator("token")
    def return_hex(cls, v):
        return v.hex


class IntQuerySchema(BaseModel):
    id: int


class RatingSchema(BaseModel):
    rate: int

    @validator("rate")
    def valid_rating(cls, v):
        if v not in range(6):
            raise ValueError
        if v == 0:
            raise ValueError
        return v


class PageQuerySchema(BaseModel):
    page: int


class WalletSchema(BaseModel):
    wallet: constr(min_length=42, max_length=42)

    @validator("wallet")
    def valid_wallet(cls, v):
        try:
            addr = Web3.to_checksum_address(v)
            return addr
        except:
            raise ValueError("Invalid wallet Address")


class ValidEmailSchema(BaseModel):
    email: EmailStr

    @validator("email")
    def valid_email_length(cls, v):
        if len(v) > 345:
            raise ValueError
        return v


class ResetPasswordSchema(StringUUIDQuerySchema):
    password: constr(max_length=64, min_length=8)
    confirm_password: constr(max_length=64, min_length=8)

    @validator("confirm_password")
    def passwords_are_same(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v


class ValidTxSchema(IntQuerySchema):
    tx_hash: constr(min_length=66, max_length=66)

    @validator("tx_hash")
    def valid_tx_hash(cls, v):
        if "0x" not in v[:2]:
            raise ValueError("Invalid tx hash")
        return v


class SpotSchema(BaseModel):
    symbol: constr(max_length=12)
    short_text: constr(min_length=0, max_length=100) | None
    quantity: float
    price: float
    sl: float
    tp1: float
    tp2: float | None
    tp3: float | None

    @validator("tp3")
    def validate_tp3(cls, v, values):
        if v is not None and (values.get("tp2") is None or v == values.get("tp2")):
            raise ValueError("tp3 requires tp2 to be set and different from tp3")
        return v


class FuturesSchema(SpotSchema):
    side: constr(max_length=4)
    leverage: int

    @validator("side")
    def is_buy_or_sell(cls, v):
        if v not in ["BUY", "SELL"]:
            raise ValueError
        return v


class TpSchema(IntQuerySchema):
    quoteQty: float
    tp: float


class ProviderApplicationSchema(WalletSchema):
    experience: constr(min_length=10, max_length=300, to_lower=True)
    socials_and_additional: constr(min_length=10, max_length=500, to_lower=True)
