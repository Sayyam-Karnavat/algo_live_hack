from algosdk import account
from algosdk import mnemonic


def generate_account():
    generated_account_private_key , generated_account_wallet_address = account.generate_account()
    generated_mnemonic = mnemonic.from_private_key(generated_account_private_key)
    return (generated_mnemonic , generated_account_private_key , generated_account_wallet_address)


if __name__ == "__main__":
    mnemo , key , wallet = generate_account()
    print(mnemo)
    print(key)
    print(wallet)

