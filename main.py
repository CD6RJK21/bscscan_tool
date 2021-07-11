from bscscan import BscScan
import asyncio
from datetime import datetime
from pycoingecko import CoinGeckoAPI


API_KEY = 'BWPJX37Q9GKPHFFKWY6KEX7HTHACIB4533'

# print(cryptocompare.get_price('BNB', currency='USD'))


def analyse_trade(trade, address):
    n = 0 if trade[0]['from'].lower() == address.lower() else 1
    id = next((crypt for crypt in coins_list if trade[n]['tokenSymbol'].lower() == crypt['symbol'].lower()), {'id': 'no such token'})
    if id['id'] == 'no such token':
        return
    # sold = cryptocompare.get_historical_price(trade[n]['tokenSymbol'].upper(),
    #                                             'USD', trade[n]['timeStamp'])[trade[n]['tokenSymbol'].upper()]['USD']
    # 
    # earned = cryptocompare.get_historical_price(trade[n % 2]['tokenSymbol'].upper(),
    #                                             'USD', trade[n % 2]['timeStamp'])[trade[n % 2]['tokenSymbol'].upper()]['USD']
    profit = 0
    try:
        date = datetime.fromtimestamp(int(trade[n]['timeStamp']))
        sold = cg.get_coin_history_by_id(id['id'], "{}-{}-{}".format(date.day, date.month, date.year))
        sold = sold['market_data']['current_price']['bnb'] * int(trade[n]['value'])
        print(sold)
#
        id = next((crypt for crypt in coins_list if trade[n % 2]['tokenSymbol'].lower() == crypt['symbol'].lower()), None)
        date = datetime.fromtimestamp(int(trade[n % 2]['timeStamp']))
        bought = cg.get_coin_history_by_id(id['id'], "{}-{}-{}".format(date.day, date.month, date.year))
        bought = bought['market_data']['current_price']['bnb'] * int(trade[n % 2]['value'])
        profit = (sold - bought) / bought * 100  # count percents
    except BaseException as be:
        print(be.__class__, be)
    return profit
    # return sold - earned


async def main():
    address = input()  # 0x450dcf93160a30be156a4600802c91bf64dffd2e
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
                sort="desc"
            )
        earnings = []
        lt = {'timeStamp': -1}
        pair = False
        for trade in address_trades:
            if lt.get('timeStamp') == trade.get('timeStamp') and not pair:
                pair = True
                try:
                    profit = analyse_trade([lt, trade], address)
                    if profit:
                        earnings.append(analyse_trade([lt, trade], address))
                except TypeError as TE:
                    pass
            # elif not pair and trade['to'].lower() == address.lower():
            #     print('Income')
            #     pair = False
            else:
                pair = False
            lt = trade
        print('all BEP20 token transfer events:',
            earnings
        )


if __name__ == "__main__":
    cg = CoinGeckoAPI()
    coins_list = cg.get_coins_list()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
