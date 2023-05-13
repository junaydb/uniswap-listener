import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()


def flatten(string):
    split = string.split("\n")
    flattened = ""
    for line in split:
        flattened += line.replace(" ", "")
    return flattened


api_key = os.environ.get("ETHERSCAN_KEY")
uniswap_V3_factory_address = "0x1F98431c8aD98523631AE4a59f267346ea31F984"


get_block_num_endpoint = """https://api.etherscan.io/api
   ?module=block
   &action=getblocknobytime
   &timestamp={time}
   &closest=before
   &apikey={api_key}""".format(
    time=int(time.time()), api_key=api_key
)
res = requests.get(flatten(get_block_num_endpoint))
block_number = int(res.json()["result"])


get_event_logs_endpoint = """https://api.etherscan.io/api
   ?module=logs
   &action=getLogs
   &address={uniswap_V3_factory_address}
   &fromBlock={fromBlock}
   &toBlock={toBlock}
   &page=1
   &offset=5
   &apikey={api_key}""".format(
    fromBlock=block_number - 1000,
    toBlock=block_number,
    api_key=api_key,
    address=uniswap_V3_factory_address,
)
res = requests.get(flatten(get_event_logs_endpoint))
latest_liquidity_pool = res.json()["result"][0]

# TO-DO: Get token names from token ids using Uniswap GraphQL endpoint
# get_token_data_query =
