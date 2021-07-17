from bscscan import BscScan
import asyncio
import requests
import time
from bs4 import BeautifulSoup
import xlsxwriter
import json
import os

if os.path.exists('config.json'):
    with open('config.json') as config_file:
        config = json.load(config_file)
else:
    config = {'API_KEY': "BWPJX37Q9GKPHFFKWY6KEX7HTHACIB4533", 'MAX_USD_FOR_SCAN': 5000000, 'MIN_USD_FOR_SCAN': 50000,
            'MAX_TRN': 1000, 'MIN_TRN': 50, 'START_PAGE': 1, 'END_PAGE': 400}
    with open('config.json', 'w', encoding='utf-8') as config_file:
        json.dump(config, config_file, ensure_ascii=False, indent=4)


API_KEY = config['API_KEY']
MAX_USD_FOR_SCAN = config['MAX_USD_FOR_SCAN']
MIN_USD_FOR_SCAN = config['MIN_USD_FOR_SCAN']
MAX_TRN = config['MAX_TRN']
MIN_TRN = config['MIN_TRN']
START_PAGE = config['START_PAGE']
END_PAGE = config['END_PAGE']


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
            return 0, 0
        time.sleep(0.25)
        try:
            address_trades = await client.get_bep20_token_transfer_events_by_address(  # get_normal_txs_by_address
                address=address,
                startblock=0,
                endblock=999999999,
                sort="asc"
            )
        except AssertionError as AE:
            return 0, 0
    if (len(address_trades) < MIN_TRN) or (len(address_trades) > MAX_TRN):
        return 0, 0
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
    won = 0
    lose = 0
    for key in bought_tokens.keys():
        bought = bought_tokens[key][0]
        sold = bought_tokens[key][2]
        if bought != 0:
            roi = sold / bought * 100
            if roi != 0:
                percents.append(roi)
                if roi >= 100:
                    won += 1
                else:
                    lose += 1
    if won > 0 and lose == 0:
        win_to_lose = 100
    elif lose > 0:
        win_to_lose = won / (won + lose) * 100
    else:
        win_to_lose = 0
    if len(percents) > 0:
        return sum(percents) / len(percents), win_to_lose
    else:
        return 0, 0


async def get_addresses():
    url = "https://bscscan.com/accounts/"
    curr_price = await client.get_bnb_last_price()
    curr_price = float(curr_price['ethusd'])

    workbook = xlsxwriter.Workbook('result.xlsx')
    worksheet = workbook.add_worksheet(name='addresses pages ' + str(START_PAGE) + ' - ' + str(END_PAGE))
    worksheet.write('A1', 'address')
    worksheet.write('B1', 'ROI%')
    worksheet.write('C1', 'win to lose')
    worksheet.write('D1', 'balance in USD')
    row = 2
    for page_number in range(START_PAGE, END_PAGE + 1):
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
                if roi[0] != 0:
                    roi, win_to_lose = roi[0], roi[1]
                    worksheet.write('A' + str(row), address)
                    worksheet.write('B' + str(row), roi)
                    worksheet.write('C' + str(row), win_to_lose)
                    worksheet.write('D' + str(row), balance_in_usd)
                    row += 1
                    print(address, balance_in_usd, roi, win_to_lose)
                # there goes writing
    workbook.close()


async def check_addresses():
    if os.path.exists('addresses.txt'):
        with open('addresses.txt', 'r', encoding='utf-8') as file:
            addresses = [line.replace('\n', '') for line in file.readlines()]
        result = []
        curr_price = await client.get_bnb_last_price()
        curr_price = float(curr_price['ethusd'])
        for address in addresses:
            balance = int(await client.get_bnb_balance(address=address)) / 1000000000000000000 * curr_price
            roi = await get_roi(address)
            result.append(address + ';' + str(roi[0]) + ';' + str(balance))
        with open('result.txt', 'w', encoding='utf-8') as file:
            file.write('\n'.join(result))
        return 1
    else:
        return 0


async def main():
    print('Hello! What do you need. Type the number of your request\n1 Scan address\n2 Scan addresses in the file',
          '3 Scan bscscan.com/accounts', sep='\n')
    command = input()
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
            roi = await get_roi(address)
            print('ROI%:', str(roi[0]) + '%')
            print('Win to lose:', str(roi[1]) + '%')
        elif command == '2':
            if await check_addresses():
                print('done')
            else:
                print('error')
        elif command == '3':
            await get_addresses()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
