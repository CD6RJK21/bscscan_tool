from bscscan import BscScan
import asyncio

API_KEY = 'BWPJX37Q9GKPHFFKWY6KEX7HTHACIB4533'


async def main():
    address = input() # 0x958434Ce9C5854f64E612F3093434F313B8911E3
    async with BscScan(API_KEY) as client:
        print('balance:',
            await client.get_bnb_balance(
                address=address
            )
        )
        print('all BEP20 token transfer events:',
            await client.get_bep20_token_transfer_events_by_address(
                address=address,
                startblock=0,
                endblock=999999999,
                sort="asc"
            )
        )


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
