from algosdk import account, transaction
import os
from dotenv import load_dotenv
import algokit_utils
from algokit_utils import AlgorandClient, AlgoAmount, MultisigMetadata, AssetOptInParams, AssetTransferParams , PaymentParams 
from algosdk import mnemonic


load_dotenv()



ALGOD_ADDRESS = "https://testnet-api.algonode.cloud"
ALGOD_TOKEN = "a" * 64
SENDER_PRIVATE_KEY_1 = os.environ['MASTER_PRIVATE_KEY']
SENDER_PRIVATE_KEY_2 = os.environ['MULTIISG_PRIVATE_KEY_2']
SENDER_ADDRESS_1 = account.address_from_private_key(SENDER_PRIVATE_KEY_1)
SENDER_ADDRESS_2 = account.address_from_private_key(SENDER_PRIVATE_KEY_2)

ASSET_ID = 741182425

# Initialize algod client
algorand_client = algokit_utils.AlgorandClient.testnet()


random_account_private_key , random_account_wallet_address = account.generate_account()
random_account_mnemonic = mnemonic.from_private_key(random_account_private_key)
random_account = algorand_client.account.from_mnemonic(mnemonic=random_account_mnemonic)

print("Random receiver account :-" , random_account_wallet_address)


master_account = algorand_client.account.from_mnemonic(mnemonic=os.environ['MASTER_MNEMONIC'])
multisig_account_1 = algorand_client.account.from_mnemonic(mnemonic=os.environ['MULTISIG_MNEMONIC_1'])



multisig_account = algorand_client.account.multisig(
    metadata=MultisigMetadata(
        version=1,
        threshold=2,
        addresses=[
           master_account.address,
            multisig_account_1.address
        ],
    ),
    signing_accounts=[master_account, multisig_account_1],
)


def fund_account(address):

    payment_txn = algorand_client.send.payment(
        PaymentParams(
            sender=master_account.address,
            receiver=address,
            amount=AlgoAmount(algo=2),
        )
    )

    print("Payment transaction successfull")

fund_account(address=multisig_account.address)
fund_account(address=multisig_account_1.address)


# 5. Opt-in multisig account to the asset (replace 1234 with your asset ID)
algorand_client.send.asset_opt_in(
    AssetOptInParams(
        sender=multisig_account.address,
        asset_id=ASSET_ID,
        signer=multisig_account.signer,  # Collects required multisig signatures
    )
)




# 6. Transfer asset to the multisig account
algorand_client.send.asset_transfer(
    AssetTransferParams(
        sender=master_account.address,         # Must be an account already opted-in and holding the asset
        receiver=multisig_account.address,
        asset_id=ASSET_ID,
        amount=1,
    )
)


print("Transfer from master account to multisign done !!!!")

# From multisign to random user

algorand_client.send.asset_opt_in(
    AssetOptInParams(
        sender=random_account_wallet_address,
        asset_id=ASSET_ID,
        signer=random_account,  # Collects required multisig signatures
    )
)


algorand_client.send.asset_transfer(
    AssetTransferParams(
        sender=multisig_account.address,         # Must be an account already opted-in and holding the asset
        receiver=random_account_wallet_address,
        asset_id=ASSET_ID,
        amount=1,
    )
)

print("Done !!!")



