from bscscan import BscScan
import asyncio
from datetime import datetime
from pycoingecko import CoinGeckoAPI
import requests
import time
from bs4 import BeautifulSoup
import xlsxwriter


API_KEY = 'BWPJX37Q9GKPHFFKWY6KEX7HTHACIB4533'
MAX_USD_FOR_SCAN = 5000000
MIN_USD_FOR_SCAN = 5000
MAX_TRN = 200
MIN_TRN = 50
START_PAGE = 50
END_PAGE = 80


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


async def get_roi(address):
    try:
        address_trades = await client.get_bep20_token_transfer_events_by_address(  # get_normal_txs_by_address
            address=address,
            startblock=0,
            endblock=999999999,
            sort="asc"
        )
    except AssertionError as AE:
        if 'No transactions found' in str(AE):
            return 0
        time.sleep(0.25)
        try:
            address_trades = await client.get_bep20_token_transfer_events_by_address(  # get_normal_txs_by_address
                address=address,
                startblock=0,
                endblock=999999999,
                sort="asc"
            )
        except AssertionError as AE:
            return 0
    if (len(address_trades) < MIN_TRN) or (len(address_trades) > MAX_TRN):
        return 0
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
        return sum(percents) / len(percents)
    else:
        return 0


async def get_addresses():
    url = "https://bscscan.com/accounts/"
    curr_price = await client.get_bnb_last_price()
    curr_price = float(curr_price['ethusd'])

    workbook = xlsxwriter.Workbook('merten.xlsx')
    worksheet = workbook.add_worksheet(name='addresses pages ' + str(START_PAGE) + ' - ' + str(END_PAGE))
    worksheet.write('A1', 'address')
    worksheet.write('B1', 'ROI%')
    worksheet.write('C1', 'balance in USD')
    row = 2
    for page_number in range(1, 400):
        page = requests.get(url + str(page_number)).text
        soup = BeautifulSoup(page, features="html.parser")
        soup = soup.find('tbody')
        soup = soup.find_all('tr')
        for element in soup:
            try:
                if 'text-secondary' in element.contents[1].contents[0].attrs['class']:
                    continue
            except KeyError as KE:
                pass
            bnb_amount = str(element.contents[3].text.replace(',', '').replace(' BNB', ''))
            bnb_amount = float(bnb_amount)
            if (bnb_amount * curr_price >= MIN_USD_FOR_SCAN) and (bnb_amount * curr_price <= MAX_USD_FOR_SCAN):
                try:
                    address = str(element.contents[1].contents[0].contents[1].contents[0])
                except IndexError as IE:
                    address = str(element.contents[1].contents[0].contents[0])
                time.sleep(0.2)
                roi = await get_roi(address)
                balance_in_usd = bnb_amount * curr_price
                if roi != 0:
                    worksheet.write('A' + str(row), address)
                    worksheet.write('B' + str(row), str(roi))
                    worksheet.write('C' + str(row), str(balance_in_usd))
                    print(address, balance_in_usd, roi)
                # there goes writing
    workbook.close()


async def main():
    print('Hello! What do you need. Type the number of your request\n1 Scan address\n2 Scan addresses in the file',
          '3 Scan bscscan.com/accounts', sep='\n')
    command = input()  # 0x1e2c0f0cc139a3781f866cb5b383c57ed620f7ca
    global client
    async with BscScan(API_KEY) as client:
        if command == '1':
            print('Type your address: ', end='')
            address = input()
            curr_price = await client.get_bnb_last_price()
            curr_price = float(curr_price['ethusd'])
            print('balance:',
                  int(await client.get_bnb_balance(
                      address=address
                  )) / 1000000000000000000 * curr_price, 'USD'
                  )
            print('ROI%:', str(await get_roi(address)) + '%')
        elif command == '2':
            pass
        elif command == '3':
            await get_addresses()


if __name__ == "__main__":
    cg = CoinGeckoAPI()
    coins_list = cg.get_coins_list()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
