from algosdk import account, transaction
from algosdk.v2client import algod
import os
from dotenv import load_dotenv

load_dotenv()



ALGOD_ADDRESS = "https://testnet-api.algonode.cloud"
ALGOD_TOKEN = "a" * 64
SENDER_PRIVATE_KEY_1 = os.environ['MASTER_PRIVATE_KEY']
SENDER_PRIVATE_KEY_2 = os.environ['MULTIISG_PRIVATE_KEY_2']
SENDER_ADDRESS_1 = account.address_from_private_key(SENDER_PRIVATE_KEY_1)
SENDER_ADDRESS_2 = account.address_from_private_key(SENDER_PRIVATE_KEY_2)



random_account_private_key , random_account_wallet_address = account.generate_account()
RECEIVER_ADDRESS = random_account_wallet_address



# Initialize algod client
algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

# Create a multisig account (version=1, threshold=2, two addresses)
msig = transaction.Multisig(
    version=1,
    threshold=2,
    addresses=[SENDER_ADDRESS_1, SENDER_ADDRESS_2]
)


# Fund the accounts
def fund_accounts(address):
    try:
        params = algod_client.suggested_params()
        amount = 1_000_000  # 1 Algo
        payment_txn = transaction.PaymentTxn(
            sender=os.environ['MASTER_ADDRESS'],
            sp=params,
            receiver=address,
            amt=amount,
        )
        signed_txn = payment_txn.sign(os.environ['MASTER_PRIVATE_KEY'])
        transaction_id = algod_client.send_transaction(signed_txn)
        transaction.wait_for_confirmation(algod_client=algod_client, txid=transaction_id)
        print(f"Account {address} funded!")
    except Exception as e:
        print(f"Error funding account {address}: {e}")


fund_accounts(address=msig.address())

# Get suggested params from the network
params = algod_client.suggested_params()

# Create an asset transfer transaction from the multisig account
txn = transaction.AssetTransferTxn(
    sender=msig.address(),
    sp=params,
    receiver=RECEIVER_ADDRESS,
    amt=1,
    index=741174820
)

# Create a multisig transaction object
mtx = transaction.MultisigTransaction(txn, msig)

# Sign the transaction with the first private key
mtx.sign(SENDER_PRIVATE_KEY_1)

# Sign the transaction with the second private key
mtx.sign(SENDER_PRIVATE_KEY_2)

# Serialize the signed transaction
signed_txn = mtx

# Send the transaction
txid = algod_client.send_raw_transaction(transaction.encoding.msgpack_encode(signed_txn))
print("Transaction ID:", txid)

