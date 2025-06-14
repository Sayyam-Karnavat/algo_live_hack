import os
from dotenv import load_dotenv
from algosdk import account, transaction
from algosdk.v2client import algod
from algosdk import mnemonic

load_dotenv()




master_mnemonic = os.environ['MASTER_MNEMONIC']
private_key = mnemonic.to_private_key(master_mnemonic)
user_address = account.address_from_private_key(private_key)


print("Master private key :-" , private_key)
print("Master address :-" , user_address)
