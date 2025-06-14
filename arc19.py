import hashlib
import json
import os
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from algosdk import mnemonic,account,transaction,encoding
import algokit_utils
import re
import requests
from multiformats_cid import make_cid
import multihash
from dotenv import load_dotenv


load_dotenv()


class ARC19:
    def __init__(self):
        
        
        # Initialize client
        # self.algod_address = "http://localhost:4001"
        # self.indexer_address = "http://localhost:8980"

        # Testnet 
        self.algod_address = "https://testnet-api.algonode.cloud"
        self.indexer_address = "https://testnet-idx.algonode.cloud"


        self.algod_token = "a" * 64
        self.algod_client = AlgodClient(algod_token=self.algod_token , algod_address=self.algod_address)
        self.algod_indexer = IndexerClient(indexer_token=self.algod_token , indexer_address=self.indexer_address)

        # User account
        # self.user_account = algokit_utils.get_localnet_default_account(client=self.algod_client)

        master_mnemonic = os.environ['MASTER_MNEMONIC']
        self.private_key = mnemonic.to_private_key(master_mnemonic)
        self.user_address = account.address_from_private_key(self.private_key)

        
        # Pinata
        self.pinata_key = os.environ['IPFS_API_KEY']
        self.pinata_secret_key = os.environ['IPFS_SECRET_KEY']

        # Suggested params
        self.sp = self.algod_client.suggested_params()


    def upload_metadata(self , file_path):
        '''
        This will upload the digital assets to IPFS
        Returns the IPFS hash which will be used to convert to reserve address
        '''
        url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
        headers = {
            "pinata_api_key": self.pinata_key,
            "pinata_secret_api_key": self.pinata_secret_key,
        }
        filename = os.path.basename(file_path)
        with open(file_path , 'rb') as file:

            files = {"file" :(filename , file)}
            response = requests.post(url=url , files=files , headers=headers)
            if response.status_code == 200:
                ipfs_hash = response.json().get("IpfsHash")
                return ipfs_hash
            
            else:
                print("Failed to upload file :-" , response.status_code , response.text)
                return None
            
    def reserve_address_from_cid(self,cid):
        decoded_cid = multihash.decode(make_cid(cid).multihash)
        reserve_address = encoding.encode_address(decoded_cid.digest)
        assert encoding.is_valid_address(reserve_address)
        return reserve_address
        
    def version_from_cid(self,cid):
        return make_cid(cid).version

    def codec_from_cid(self,cid):
        return make_cid(cid).codec

    def hash_from_cid(self,cid):
        return multihash.decode(make_cid(cid).multihash).name


    def create_url_from_cid(self,cid):
        version = self.version_from_cid(cid)
        codec = self.codec_from_cid(cid)
        hash = self.hash_from_cid(cid)
        url = "template-ipfs://{ipfscid:" + f"{version}:{codec}:reserve:{hash}" + "}"
        valid = re.compile(
            r"template-ipfs://{ipfscid:(?P<version>[01]):(?P<codec>[a-z0-9\-]+):(?P<field>[a-z0-9\-]+):(?P<hash>[a-z0-9\-]+)}"
        )
        assert bool(valid.match(url))
        return url


    def create_metadata(self , asset_name , description , ipfs_hash , image_mimetype = "application/JPEG"):
        metadata = {
            "name" : asset_name,
            "description" : description,
            "image" : f"ipfs://{ipfs_hash}",
            "creator" : self.user_address,
            "mimetype" : image_mimetype
        }

        nft_url = f"https://indigo-central-dragonfly-340.mypinata.cloud/ipfs/{ipfs_hash}"

        # print(f"NFT URL :- https://indigo-central-dragonfly-340.mypinata.cloud/ipfs/{ipfs_hash}")
        metadata_text = json.dumps(metadata , separators=(",",":"))
        
        metadata_hash = hashlib.sha256(metadata_text.encode()).digest()

        return metadata_hash , nft_url
    
    
    def create_asset(self , metadata_hash , reserve_address , url):

        usigned_txn = transaction.AssetCreateTxn(
            sender=self.user_address,
            sp=self.sp,
            total=1, # Non divisible NFT
            decimals=0 ,# Non divisible NFT
            default_frozen=False,
            asset_name="ARC19",
            unit_name="ARC19NFT",
            manager=self.user_address,
            clawback=self.user_address,
            reserve=reserve_address,
            url=url,
            metadata_hash=metadata_hash
        )

        signed_txn = usigned_txn.sign(self.private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        confirmed_transaction = transaction.wait_for_confirmation(algod_client=self.algod_client , txid=tx_id)

        asset_ID = confirmed_transaction['asset-index']
        print("Asset ID :-" , asset_ID)
        return tx_id , asset_ID

if __name__ == "__main__":


    file_path = "washing.jpg"
    username = "ssk"

    arc_obj = ARC19()
    # CID is basically the IPFS file hash 
    cid = arc_obj.upload_metadata(file_path=file_path)

    metadata_hash , nft_url = arc_obj.create_metadata(
        asset_name=username,
        description="shortDesc",
        ipfs_hash=cid
    )

    reserve_address = arc_obj.reserve_address_from_cid(cid=cid)

    url = arc_obj.create_url_from_cid(cid=cid)

    transaction_id , asset_ID = arc_obj.create_asset(
        metadata_hash=metadata_hash,
        reserve_address=reserve_address,
        url=url
    )
    print("Transaction :\n https://lora.algokit.io/testnet/transaction/{}".format(transaction_id))