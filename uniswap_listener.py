#!/usr/bin/env python3

import requests
import time
import sys
import os

etherscan_api_key = os.environ.get("ETHERSCAN_KEY")
ether_scan_rest_endpoint = "https://api.etherscan.io/api"
uniswap_V3_factory_address = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
uniswap_V3_graphql_endpoint = (
    "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
)


def flattenString(string):
    split = string.split("\n")
    flattened = ""
    for line in split:
        flattened += line.replace(" ", "")
    return flattened


def getLatestBlock(block_range):
    print(
        f"Searching for latest liquidity pool in range of last {block_range} blocks..."
    )

    get_block_num_endpoint = f"""
    {ether_scan_rest_endpoint}
    ?module=block
    &action=getblocknobytime
    &timestamp={int(time.time())}
    &closest=before
    &apikey={etherscan_api_key}"""
    response = requests.get(flattenString(get_block_num_endpoint))
    latest_block_number = int(response.json()["result"])

    return latest_block_number


def getEventLogs(latest_block_number, block_range):
    get_event_logs_endpoint = f"""
    {ether_scan_rest_endpoint}
    ?module=logs
    &action=getLogs
    &address={uniswap_V3_factory_address}
    &fromBlock={latest_block_number - block_range}
    &toBlock={latest_block_number}
    &apikey={etherscan_api_key}"""
    response = requests.get(flattenString(get_event_logs_endpoint))
    result_container = response.json()["result"]

    try:
        latest_liquidity_pool = result_container[len(result_container) - 1]
    except:
        raise RuntimeError

    token_a_topic = latest_liquidity_pool["topics"][1]
    token_b_topic = latest_liquidity_pool["topics"][2]

    # convert topic hex to address hex
    token_a_address = "0x" + token_a_topic[26 : len(token_a_topic)]
    token_b_address = "0x" + token_b_topic[26 : len(token_b_topic)]

    return [token_a_address, token_b_address]


def getTokenData(token_a_address, token_b_address):
    token_a_data_query = f"""
    {{
      token(id:"{token_a_address}") {{
        symbol
        name
        decimals
        volumeUSD
        poolCount
      }}
    }}
    """
    token_b_data_query = f"""
    {{
      token(id:"{token_b_address}") {{
        symbol
        name
        decimals
        volumeUSD
        poolCount
      }}
    }}
    """

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


def defaultMode():
    block_range = int(input("Enter block range: "))

    try:
        latest_block_number = getLatestBlock(block_range)
    except:
        print("Error: failed whilst retrieving latest block number")
        raise SystemExit

    try:
        token_addresses = getEventLogs(latest_block_number, block_range)
    except RuntimeError:
        print(f"No new liquidity pool found for the last {block_range} blocks")
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
        f"Success!\nFound new liquidity pool created within range of last {block_range} blocks"
    )
    print(f"Token 1 Symbol: {token_symbols[0]}")
    print(f"Token 1 Address: {token_addresses[0]}")
    print(f"Token 2 Symbol: {token_symbols[1]}")
    print(f"Token 2 Address: {token_addresses[1]}")


def listenMode():
    print("TO-DO: Add listen mode")


def main():
    if len(sys.argv) < 2:
        print("No mode specified. Using default mode...")
        try:
            defaultMode()
        except KeyboardInterrupt:
            None
        exit(0)

    match sys.argv[1]:
        case "-l" | "-listen":
            print("Using listen mode...")
            try:
                listenMode()
            except KeyboardInterrupt:
                None
        case "-d" | "-default":
            print("Using default mode...")
            try:
                defaultMode()
            except KeyboardInterrupt:
                None
        case _:
            print("Invalid option. Exiting...")
            exit(0)


main()
