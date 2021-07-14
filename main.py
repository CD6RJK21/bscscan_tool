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


# sold = cryptocompare.get_historical_price(trade[n]['tokenSymbol'].upper(),
#                                             'USD', trade[n]['timeStamp'])[trade[n]['tokenSymbol'].upper()]['USD']
#
# earned = cryptocompare.get_historical_price(trade[n % 2]['tokenSymbol'].upper(),
#                                             'USD', trade[n % 2]['timeStamp'])[trade[n % 2]['tokenSymbol'].upper()]['USD']


async def main():
    address = input()
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
        for trade in address_trades:  # maybe use % of sold to all amount of bought
            if trade.get('to').lower() == address.lower():
                bought_tokens[trade.get('tokenSymbol')] = get_token_price(trade)
            else:
                if trade.get('tokenSymbol') in bought_tokens:
                    if bought_tokens[trade.get('tokenSymbol')]:
                        # k = int(trade.get('value')) / bought_tokens[trade.get('tokenSymbol')][1]
                        bought = bought_tokens[trade.get('tokenSymbol')] * int(trade['value'])  # last buy price * sold value
                        sold = get_token_price(trade) * int(trade['value'])  # price when sold * sold value
                        if bought != 0:
                            profit = (sold - bought) / bought * 100
                            if profit != 0.0:
                                if len(percents) > 0 and (percents[-1] > profit + 0.5 or percents[-1] < profit - 0.5):
                                    percents.append(profit)
                                elif len(percents) == 0:
                                    percents.append(profit)
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
