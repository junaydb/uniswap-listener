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
uniswap_V3_graphql_endpoint = (
    "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
)

block_range = int(input("Enter block range: "))
print(
    "Searching for latest liquidity pool in range of last {block_range} blocks...".format(
        block_range=block_range
    )
)


get_block_num_endpoint = """https://api.etherscan.io/api
?module=block
&action=getblocknobytime
&timestamp={time}
&closest=before
&apikey={api_key}""".format(
    time=int(time.time()), api_key=api_key
)
response = requests.get(flatten(get_block_num_endpoint))
latest_block_number = int(response.json()["result"])


get_event_logs_endpoint = """https://api.etherscan.io/api
?module=logs
&action=getLogs
&address={address}
&fromBlock={fromBlock}
&toBlock={toBlock}
&apikey={api_key}""".format(
    fromBlock=latest_block_number - block_range,
    toBlock=latest_block_number,
    api_key=api_key,
    address=uniswap_V3_factory_address,
)
response = requests.get(flatten(get_event_logs_endpoint))
result_container = response.json()["result"]

latest_liquidity_pool = result_container[len(result_container) - 1]
token_a_topic = latest_liquidity_pool["topics"][1]
token_b_topic = latest_liquidity_pool["topics"][2]

# convert topic hex to address hex
token_a = "0x" + token_a_topic[26 : len(token_a_topic)]
token_b = "0x" + token_b_topic[26 : len(token_b_topic)]


token_a_data_query = """
{{
  token(id:"{token_a_address}") {{
    symbol
    name
    decimals
    volumeUSD
    poolCount
  }}
}}
""".format(
    token_a_address=token_a
)
token_b_data_query = """
{{
  token(id:"{token_b_address}") {{
    symbol
    name
    decimals
    volumeUSD
    poolCount
  }}
}}
""".format(
    token_b_address=token_b
)

response_a = requests.post(
    uniswap_V3_graphql_endpoint,
    json={"query": token_a_data_query},
)
response_b = requests.post(
    uniswap_V3_graphql_endpoint,
    json={"query": token_b_data_query},
)

token_a_symbol = response_a.json()["data"]["token"]["symbol"]
token_b_symbol = response_b.json()["data"]["token"]["symbol"]

print("Success!\nFound new liquidity pool created within range of last 1000 blocks.")
print("Token 1 Symbol: {symbol}".format(symbol=token_a_symbol))
print("Token 1 Address: {address}".format(address=token_a))
print("Token 2 Symbol: {symbol}".format(symbol=token_b_symbol))
print("Token 2 Address: {address}".format(address=token_b))

# TO-DO: add exception handling
