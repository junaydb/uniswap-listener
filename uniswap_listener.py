import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

ether_scan_api_key = os.environ.get("ETHERSCAN_KEY")
ether_scan_rest_endpoint = "https://api.etherscan.io/api"
uniswap_V3_factory_address = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
uniswap_V3_graphql_endpoint = (
    "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
)

block_range = int(input("Enter block range: "))


def flatten(string):
    split = string.split("\n")
    flattened = ""
    for line in split:
        flattened += line.replace(" ", "")
    return flattened


def getLatestBlock():
    print(
        "Searching for latest liquidity pool in range of last {block_range} blocks...".format(
            block_range=block_range
        )
    )

    get_block_num_endpoint = """
    {url}
    ?module=block
    &action=getblocknobytime
    &timestamp={time}
    &closest=before
    &apikey={api_key}""".format(
        url=ether_scan_rest_endpoint, time=int(time.time()), api_key=ether_scan_api_key
    )
    response = requests.get(flatten(get_block_num_endpoint))
    latest_block_number = int(response.json()["result"])

    return latest_block_number


def getEventLogs(latest_block_number):
    get_event_logs_endpoint = """
    {url}
    ?module=logs
    &action=getLogs
    &address={address}
    &fromBlock={fromBlock}
    &toBlock={toBlock}
    &apikey={api_key}""".format(
        url=ether_scan_rest_endpoint,
        fromBlock=latest_block_number - block_range,
        toBlock=latest_block_number,
        api_key=ether_scan_api_key,
        address=uniswap_V3_factory_address,
    )
    response = requests.get(flatten(get_event_logs_endpoint))
    result_container = response.json()["result"]

    try:
        latest_liquidity_pool = result_container[len(result_container) - 1]
    except:
        print(
            "No new liquidity pool found for the last {range} blocks!".format(
                range=block_range
            )
        )
        raise RuntimeError

    token_a_topic = latest_liquidity_pool["topics"][1]
    token_b_topic = latest_liquidity_pool["topics"][2]

    # convert topic hex to address hex
    token_a_address = "0x" + token_a_topic[26 : len(token_a_topic)]
    token_b_address = "0x" + token_b_topic[26 : len(token_b_topic)]

    return [token_a_address, token_b_address]


def getTokenData(token_a_address, token_b_address):
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
        token_a_address=token_a_address
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
        token_b_address=token_b_address
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

    return [token_a_symbol, token_b_symbol]


def main():
    try:
        latest_block_number = getLatestBlock()
    except:
        print("Error: failed whilst retrieving latest block number")
        raise SystemExit

    try:
        token_addresses = getEventLogs(latest_block_number)
    except RuntimeError:
        raise SystemExit
    except:
        print("Error: failed whilst retrieving event logs")
        raise SystemExit

    try:
        token_symbols = getTokenData(token_addresses[0], token_addresses[1])
    except:
        print("Error: failed whilst retrieving token data")
        raise SystemExit

    print(
        "Success!\nFound new liquidity pool created within range of last {range} blocks.".format(
            range=block_range
        )
    )
    print("Token 1 Symbol: {symbol}".format(symbol=token_symbols[0]))
    print("Token 1 Address: {address}".format(address=token_addresses[0]))
    print("Token 2 Symbol: {symbol}".format(symbol=token_symbols[1]))
    print("Token 2 Address: {address}".format(address=token_addresses[1]))


main()
