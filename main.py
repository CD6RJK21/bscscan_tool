from bscscan import BscScan
import asyncio
from datetime import datetime
from pycoingecko import CoinGeckoAPI
import requests
import time


API_KEY = 'BWPJX37Q9GKPHFFKWY6KEX7HTHACIB4533'
# print(cryptocompare.get_price('BNB', currency='USD'))


def get_token_id(trade):
    if type(trade) is dict:
        return next((crypt.get('id') for crypt in coins_list if trade['tokenSymbol'].lower() == crypt['symbol'].lower()),
                    '')
    return next((crypt for crypt in coins_list if trade == crypt['symbol'].lower()), '')


def get_token_price(trade):
    date = datetime.fromtimestamp(int(trade['timeStamp']))
    id = get_token_id(trade)
    price = 0
    if id != '':  # and id not in BAN
        try:
            # price = cg.get_coin_history_by_id(id, "{}-{}-{}".format(date.day, date.month, date.year))
            # price = price['market_data']['current_price']['bnb']
            price = cg.get_coin_market_chart_range_by_id(id, 'bnb',
                                                         trade['timeStamp'], str(int(trade['timeStamp']) + 3600))
            price = price['prices'][0][1]
        except IndexError as ie:
            price = 0

        except KeyError as ke:
            price = 0
        except requests.exceptions.HTTPError as e429:
            # time.sleep(60)
            price = 0
    return price


async def main():
    address = input()  # 0x1e2c0f0cc139a3781f866cb5b383c57ed620f7ca
    global client
    async with BscScan(API_KEY) as client:
        curr_price = await client.get_bnb_last_price()
        curr_price = float(curr_price['ethusd'])
        print('balance:',
            int(await client.get_bnb_balance(
                address=address
                )) / 1000000000000000000 * curr_price, 'USD'
        )
        address_trades = await client.get_bep20_token_transfer_events_by_address(  # get_normal_txs_by_address
                address=address,
                startblock=0,
                endblock=999999999,
                sort="asc"
            )
        bought_tokens = dict()
        percents = []
        for trade in address_trades:
            try:
                hash_value = await client.get_internal_txs_by_txhash(txhash=trade['hash'])
            except AssertionError as ae:
                continue
            hash_value = hash_value[0]

            if trade.get('to').lower() == address.lower():  # buying
                if trade.get('tokenSymbol') in bought_tokens:
                    bought_tokens[trade.get('tokenSymbol')][0] += int(hash_value.get('value')) / 1000000000000000000
                    bought_tokens[trade.get('tokenSymbol')][1] += int(trade.get('value'))
                else:
                    bought_tokens[trade.get('tokenSymbol')] = [int(hash_value.get('value')) / 1000000000000000000,
                                                               int(trade.get('value')), 0, 0]
            else:  # selling
                if trade.get('tokenSymbol') in bought_tokens:
                    bought_tokens[trade.get('tokenSymbol')][2] += int(hash_value.get('value')) / 1000000000000000000
                    bought_tokens[trade.get('tokenSymbol')][3] += int(trade.get('value'))
                else:
                    bought_tokens[trade.get('tokenSymbol')] = [0, 0, int(hash_value.get('value')) / 1000000000000000000,
                                                               int(trade.get('value'))]
            time.sleep(0.2)
        for key in bought_tokens.keys():
            bought = bought_tokens[key][0]
            sold = bought_tokens[key][2]
            if bought != 0:
                roi = sold / bought * 100
                if roi != 100 and roi != 0:
                    percents.append(roi)

        if len(percents) > 0:
            print(percents)
            print('Average profit: ', sum(percents) / len(percents), '%', sep='')
        else:
            print(percents)


if __name__ == "__main__":
    cg = CoinGeckoAPI()
    coins_list = cg.get_coins_list()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
