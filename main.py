from bscscan import BscScan
import asyncio
import cryptocompare

API_KEY = 'BWPJX37Q9GKPHFFKWY6KEX7HTHACIB4533'

print(cryptocompare.get_historical_price('Cake-LP', 'USD', 1621951754))
# print(cryptocompare.get_price('BNB', currency='USD'))


def analyse_trade(trade, address):
    n = 0 if trade[0]['from'].lower() == address.lower() else 1
    selled = cryptocompare.get_historical_price(trade[n]['tokenSymbol'].upper(),
                                                'USD', trade[n]['timeStamp'])[trade[n]['tokenSymbol'].upper()]['USD']
    # TODO: * value
    earned = cryptocompare.get_historical_price(trade[n % 2]['tokenSymbol'].upper(),
                                                'USD', trade[n % 2]['timeStamp'])[trade[n % 2]['tokenSymbol'].upper()]['USD']
    return selled - earned


async def main():
    address = input()  # 0x450dcf93160a30be156a4600802c91bf64dffd2e
    async with BscScan(API_KEY) as client:
        print('balance:',
            await client.get_bnb_balance(
                address=address
            )
        )
        address_trades = await client.get_normal_txs_by_address(  # get_bep20_token_transfer_events_by_address
                address=address,
                startblock=0,
                endblock=999999999,
                sort="desc"
            )
        earnings = []
        lt = {'timeStamp': -1}
        for trade in address_trades:
            if lt.get('timeStamp') == trade.get('timeStamp'):
                try:
                    earnings.append(analyse_trade([lt, trade], address))
                except TypeError as TE:
                    pass
            lt = trade
        print('all BEP20 token transfer events:',
            earnings
        )


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
