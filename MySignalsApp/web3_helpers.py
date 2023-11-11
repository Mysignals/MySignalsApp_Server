from web3 import Web3
from MySignalsApp.errors.handlers import UtilError
from MySignalsApp import contract_address, abi
from web3.datastructures import AttributeDict
from web3.types import _Hash32, TxReceipt
import os

provider = os.getenv("NODE_PROVIDER")
w3 = Web3(Web3.HTTPProvider(provider))

contract = w3.eth.contract(address=contract_address, abi=abi)


def is_transaction_confirmed(tx_hash: _Hash32) -> TxReceipt:
    tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
    if not (
        tx_receipt.status and (w3.eth.get_block_number() - tx_receipt.blockNumber) > 2
    ):
        raise UtilError("Forbidden", 403, "This was not a successful transaction")
    return tx_receipt


def get_compensate_provider_event(tx_receipt: TxReceipt) -> AttributeDict:
    log = ""
    for log in tx_receipt.logs:
        if (
            log["topics"][0]
            == w3.keccak(
                text="CompensateProvider(address,uint256,uint256,string)"
            ).hex()
        ):
            log = log
    return contract.events.CompensateProvider().process_log(log)


def get_compensation_details(log: AttributeDict) -> AttributeDict:
    args = log.args

    return AttributeDict(
        {
            "contract": log.address,
            "provider": args.provider,
            "signalId": args.signalId,
            "userId": args.userId,
        }
    )


def verify_compensation_details(
    tx_hash: _Hash32, provider: _Hash32, user_id: str, siignal_id: int
) -> AttributeDict:
    tx_receipt = is_transaction_confirmed(tx_hash)
    log = get_compensate_provider_event(tx_receipt)

    data = get_compensation_details(log)

    contract_check = w3.to_checksum_address(data.contract) == contract.address
    provider_check = w3.to_checksum_address(data.provider) == w3.to_checksum_address(
        provider
    )
    user_check = data.userId == user_id
    signal_check = data.signalId == siignal_id
    if not (contract_check and provider_check and user_check and signal_check):
        raise UtilError(
            "Forbidden", 403, "Invalid Transaction, compensation details do not match"
        )

    return True
