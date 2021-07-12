from bscscan import BscScan
import asyncio
from datetime import datetime
from pycoingecko import CoinGeckoAPI
import requests
import time


API_KEY = 'BWPJX37Q9GKPHFFKWY6KEX7HTHACIB4533'
BAN = set()

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
    if id != '' and id not in BAN:
        try:
            price = cg.get_coin_history_by_id(id, "{}-{}-{}".format(date.day, date.month, date.year))
            price = price['market_data']['current_price']['bnb']
        except KeyError as ke:
            price = 0
        except requests.exceptions.HTTPError as e429:
            BAN.add(id)
            # time.sleep(60)
            price = 0
    return price



def analyse_trade(trade, address):
    n = 0 if trade[0]['from'].lower() == address.lower() else 1
    id = get_token_id(trade[n])
    if id == 'no such token':
        return 0
    # sold = cryptocompare.get_historical_price(trade[n]['tokenSymbol'].upper(),
    #                                             'USD', trade[n]['timeStamp'])[trade[n]['tokenSymbol'].upper()]['USD']
    #
    # earned = cryptocompare.get_historical_price(trade[n % 2]['tokenSymbol'].upper(),
    #                                             'USD', trade[n % 2]['timeStamp'])[trade[n % 2]['tokenSymbol'].upper()]['USD']
    profit = 0
    try:
        date = datetime.fromtimestamp(int(trade[n]['timeStamp']))
        sold = cg.get_coin_history_by_id(id, "{}-{}-{}".format(date.day, date.month, date.year))
        sold = sold['market_data']['current_price']['bnb'] * int(trade[n]['value'])
        
        id = get_token_id(trade[n % 2])
        date = datetime.fromtimestamp(int(trade[n % 2]['timeStamp']))
        bought = cg.get_coin_history_by_id(id, "{}-{}-{}".format(date.day, date.month, date.year))
        bought = bought['market_data']['current_price']['bnb'] * int(trade[n % 2]['value'])
        profit = (sold - bought) / bought * 100  # count percents
    except BaseException as be:
        print(be.__class__, be)
    return profit
    # return sold - earned


async def main():
    address = input()  # 0xF082127438286454332EaC1C73e3c6EDa3e215aD
    async with BscScan(API_KEY) as client:
        print('balance:',
            await client.get_bnb_balance(
                address=address
            )
        )
        address_trades = await client.get_bep20_token_transfer_events_by_address(  # get_normal_txs_by_address
                address=address,
                startblock=0,
                endblock=999999999,
                sort="asc"
            )
        earnings = []
        lt = {'timeStamp': -1}
        pair = False
        bought_tokens = dict()
        percents = []
        for trade in address_trades:
            if trade.get('to').lower() == address.lower():
                bought_tokens[trade.get('tokenSymbol')] = get_token_price(trade)
            else:
                if trade.get('tokenSymbol') in bought_tokens:
                    if bought_tokens[trade.get('tokenSymbol')]:
                        bought = bought_tokens[trade.get('tokenSymbol')] * int(trade['value'])
                        sold = get_token_price(trade) * int(trade['value'])
                        if bought != 0:
                            profit = (sold - bought) / bought * 100
                            if profit != 0.0:
                                percents.append(profit)
            # if lt.get('timeStamp') == trade.get('timeStamp') and not pair:
            #     pair = True
            #     try:
            #         profit = analyse_trade([lt, trade], address)
            #         if profit:
            #             earnings.append(analyse_trade([lt, trade], address))
            #     except TypeError as TE:
            #         pass
            # # elif not pair and trade['to'].lower() == address.lower():
            # #     print('Income')
            # #     pair = False
            # else:
            #     pair = False
            # lt = trade
        print('Average profit:', sum(percents) / len(percents))


if __name__ == "__main__":
    cg = CoinGeckoAPI()
    coins_list = cg.get_coins_list()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
