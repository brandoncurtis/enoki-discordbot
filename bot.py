#!/usr/bin/env python

import requests
import datetime
import time
import random
import asyncio
import discord
import os
from discord.ext.commands import Bot
from discord.ext import commands, tasks
from web3 import Web3
from dotenv import load_dotenv

load_dotenv(override=True)
DISCORD_WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
NODE_URL = os.getenv("NODE_URL")
START_BLOCK = os.getenv("START_BLOCK")
UNIROUTER_ADDR = os.getenv("UNIROUTER_ADDR")
UNIROUTER_ABI = os.getenv("UNIROUTER_ABI")
UNIPOOL_ADDR= os.getenv("UNIPOOL_ADDR")
UNIPOOL_ABI = os.getenv("UNIPOOL_ABI")
VAULT_ABI = os.getenv("VAULT_ABI")
PS_ABI = os.getenv("PS_ABI")
ONE_18DEC = 1000000000000000000
ONE_6DEC = 1000000
ZERO_ADDR = '0x0000000000000000000000000000000000000000'
UNIPOOL_ORACLE_ADDR = '0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc'
ENOKI_ADDR = '0x886058DeDEd1325A27697122512F618db590eA32'

w3 = Web3(Web3.HTTPProvider(NODE_URL))
controller_contract = w3.eth.contract(address=UNIROUTER_ADDR, abi=UNIROUTER_ABI)
pool_contract = w3.eth.contract(address=UNIPOOL_ADDR, abi=UNIPOOL_ABI)
oracle_contract = w3.eth.contract(address=UNIPOOL_ORACLE_ADDR, abi=UNIPOOL_ABI)

client = discord.Client(command_prefix='!')
activity_start = discord.Streaming(name='node syncing',url='https://etherscan.io/address/0x284fa4627AF7Ad1580e68481D0f9Fc7e5Cf5Cf77')

update_index = 0

ASSETS = {
    'ENOKI': {
        'addr':'0x886058DeDEd1325A27697122512F618db590eA32',
        'pool':'0x284fa4627AF7Ad1580e68481D0f9Fc7e5Cf5Cf77',
        'poolnum':'token0'
        },
    'SPORE': {
        'addr':'0xa4Bad5d040d4464EC5CE130987731F2f428c9307',
        'pool':'0x3eb9833BBEA994287A2227E3fEBa0D3Dc5D99F05',
        'poolnum':'token0'
        }
}

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(activity=activity_start)
    update_price.start()

@tasks.loop(seconds=120)
async def update_price():
    global update_index
    asset = list(ASSETS.keys())[update_index % 2]
    token = ASSETS[asset]
    print(f'fetching pool reserves for {token["addr"]}...')
    pool_contract = w3.eth.contract(address=token['pool'], abi=UNIPOOL_ABI)
    poolvals = pool_contract.functions['getReserves']().call()
    oraclevals = oracle_contract.functions['getReserves']().call()
    print(f'calculating price...')
    oracle_price = controller_contract.functions['quote'](ONE_6DEC, oraclevals[0], oraclevals[1]).call()*10**-18
    print(f'oracle price: {oracle_price}')
    token_price = controller_contract.functions['quote'](ONE_18DEC, poolvals[0], poolvals[1]).call()*10**-18
    price = token_price / oracle_price
    print(f'updating the price...')
    msg = f'${price:0.2f} {asset}'
    #new_price = discord.Streaming(name=msg,url='https://etherscan.io/address/0x284fa4627AF7Ad1580e68481D0f9Fc7e5Cf5Cf77')
    new_price = discord.Streaming(name=msg,url='https://etherscan.io/address/0x284fa4627AF7Ad1580e68481D0f9Fc7e5Cf5Cf77')
    print(msg)
    await client.change_presence(activity=new_price)
    update_index += 1

@client.event
async def on_message(msg):
    if client.user.id != msg.author.id:
        if '!foo' in msg.content:
            await msg.channel.send('bar')
        if '!ap' in msg.content:
            val = float(msg.content.split(' ')[-1])
            # APY = (1 + APR / n) ** n - 1
            APYfromAPR_daily = 100 * ((1 + val / (100 * 365)) ** 365 - 1)
            APYfromAPR_weekly = 100 * ((1 + val / (100 * 52)) ** 52 - 1)
            # APR = n * (1 + APY) ** (1 / n) -n
            APRfromAPY_daily = 100 * (365 * ((1 + val / 100) ** (1 / 365)) - 365)
            APRfromAPY_weekly = 100 * (52 * ((1 + val / 100) ** (1 / 52)) - 52)
            embed = discord.Embed(
                    title=':man_teacher: **Convert between APR and APY?**',
                    )
#            embed.add_field(name = 'Compounded Daily', value = 'If you redeem and reinvest rewards daily...', inline=False)
#            embed.add_field(
#                    name = f'APR to APY',
#                    value = f'{val:,.2f}% APR is equal to {APYfromAPR_daily:,.2f}% APY. $1000 will make about ${1000*val/100/365:,.2f} per day.',
#                    inline = True
#                    )
#            embed.add_field(
#                    name = f'APY to APR',
#                    value = f'{val:,.2f}% APY is equal to {APRfromAPY_daily:,.2f}% APR. $1000 will make about ${1000*APRfromAPY_daily/100/365:,.2f} per day.',
#                    inline = True
#                    )
            embed.add_field(name = 'Compounded Weekly', value = 'If you redeem and reinvest rewards weekly...', inline=False)
            embed.add_field(
                    name = f'APR to APY',
                    value = f'{val:,.2f}% APR is equal to {APYfromAPR_weekly:,.2f}% APY. $1000 will make about ${1000*val/100/365:,.2f} per day.',
                    inline = True
                    )
            embed.add_field(
                    name = f'APY to APR',
                    value = f'{val:,.2f}% APY is equal to {APRfromAPY_weekly:,.2f}% APR. $1000 will make about ${1000*APRfromAPY_weekly/100/365:,.2f} per day.',
                    inline = True
                    )
            await msg.channel.send(embed=embed)
        if '!uniswap' in msg.content:
            uni_addr, uni_deposit_token, uni_deposit_pairing, uni_token_frac = get_uniswapstate()
            embed = discord.Embed(
                    title=f':mag: ENOKI:ETH Uniswap Pool',
                    description=f':bank: Uniswap contract: [{uni_addr}](https://etherscan.io/address/{uni_addr})\n'
                                f':moneybag: Liquidity: `{uni_deposit_token:,.2f}` ENOKI (`{100*uni_token_frac:.2f}%` of supply), `{uni_deposit_pairing:,.2f}` ETH\n'
                                f':arrows_counterclockwise: [Trade ENOKI](https://app.uniswap.org/#/swap?outputCurrency={ENOKI_ADDR}), '
                                f'[Add Liquidity](https://app.uniswap.org/#/add/eth/{ENOKI_ADDR}), '
                                f'[Remove Liquidity](https://app.uniswap.org/#/remove/ETH/{ENOKI_ADDR})\n'
                                f':bar_chart: [ENOKI:ETH Uniswap chart](https://beta.dex.vision/?ticker=UniswapV2:ENOKIUSD-0x284fa4627AF7Ad1580e68481D0f9Fc7e5Cf5Cf77&interval=5)'
                    )
            await msg.channel.send(embed=embed)
        else:
            return


        if '!bot' in msg.content:
            embed = discord.Embed(
                    title='Autonomous Agricultural Assistant, at your service :tractor:',
                    description=':bar_chart: `!trade`: FARM markets and trading\n'
                                ':thinking: `!payout`: information on farming rewards\n'
                                ':globe_with_meridians: `!contribute`: contribute to the community wiki\n'
                                ':bank: `!vault fdai/fwbtc/etc`: Harvest vault state\n'
                                ':chart_with_upwards_trend: improve me [on GitHub](https://github.com/brandoncurtis/harvest-discordbot)'
                    )
            await msg.channel.send(embed=embed)
        if '!payout' in msg.content:
            embed = discord.Embed(
                    title='When do I get the CRV/SWRV/UNI/&etc? :thinking:',
                    description='Farmed tokens are sold to grow the value of your deposit :seedling: '
                                '[read more about farming strategies](https://farm.chainwiki.dev/en/strategy)',
                    )
            await msg.channel.send(embed=embed)
        if '!contribute' in msg.content:
            embed = discord.Embed(
                    title='**:sparkles: Great Idea :sparkles:**',
                    description='please add that [to the wiki](https://farm.chainwiki.dev/en/contribute)!',
                    )
            await msg.channel.send(embed=embed)
        if '!supply' in msg.content:
            embed = discord.Embed(
                    title=':bar_chart: **What is the FARM token supply?**',
                    )
            embed.add_field(
                    name = 'Maximum Supply',
                    value = 'Emission is capped at 690,420 FARM tokens. 630,741.56 (91.4%) will be emitted in the first year.',
                    inline = False
                    )
            if 'week' in msg.content:
                    weeknum = msg.content.split(' ')[-1]
                    emissions_this_week, supply_this_week = emissions(weeknum)
                    embed.add_field(
                            name = f'Emissions during Week {weeknum}',
                            value = f'{emissions_this_week:,.2f} FARM will be emitted',
                            inline = True
                            )
                    embed.add_field(
                            name = f'Supply at the end of Week {weeknum}',
                            value = f'{supply_this_week:,.2f} FARM total supply',
                            inline = True
                            )
            await msg.channel.send(embed=embed)
        if '!trade' in msg.content:
            embed = discord.Embed(
                    title='**How To Buy FARM :bar_chart:**',
                    )
            embed.add_field(
                    name = 'Token Info :mag:',
                    value = '[0xa0246c9032bC3A600820415aE600c6388619A14D](https://etherscan.io/address/0xa0246c9032bc3a600820415ae600c6388619a14d)',
                    inline = False
                    )
            embed.add_field(
                    name = 'Uniswap :arrows_counterclockwise:',
                    value = '[swap now](https://app.uniswap.org/#/swap?outputCurrency=0xa0246c9032bc3a600820415ae600c6388619a14d), '
                            '[pool info](https://uniswap.info/token/0xa0246c9032bc3a600820415ae600c6388619a14d)',
                    inline = True
                    )
            embed.add_field(
                    name = 'DEX Aggregators :arrow_right::arrow_left:',
                    value = '[debank](https://debank.com/swap?to=0xa0246c9032bc3a600820415ae600c6388619a14d), '
                            '[1inch](https://1inch.exchange/#/USDC/FARM), '
                            '[limit orders](https://1inch.exchange/#/limit-order/USDC/FARM)',
                    inline = True
                    )
            embed.add_field(
                    name = 'Trading Stats :chart_with_upwards_trend:',
                    value = '[CoinGecko](https://www.coingecko.com/en/coins/harvest-finance), '
                            '[CoinMarketCap](https://coinmarketcap.com/currencies/harvest-finance/), '
                            '[DeBank](https://debank.com/projects/harvest), '
                            '[dapp.com](https://www.dapp.com/app/harvest-finance), '
                            #'[defiprime](https://defiprime.com/product/harvest), '
                            'defipulse (soon!)',
                    inline = False
                    )
            await msg.channel.send(embed=embed)
        if '!vault' in msg.content:
            vault = msg.content.split(' ')[-1].lower()
            underlying = vault[1:]
            address, shareprice, vault_total, vault_buffer, vault_target, vault_strat, vault_strat_future, vault_strat_future_time = get_vaultstate(vault)
            vault_invested = vault_total - vault_buffer
            embed = discord.Embed(
                    title=f'{vault} Vault State :bank::mag:',
                    description=f':map: {vault} address: [{address}](https://etherscan.io/address/{address})\n'
                                f':moneybag: {vault} share price = {shareprice} {underlying}\n'
                                f':sponge: {underlying} withdrawal buffer = {vault_buffer:,.4f} {underlying}\n'
                                f':bar_chart: {underlying} invested = {vault_invested:,.4f} '
                                f'{underlying} ({100*vault_invested/vault_total:0.2f}%, target {100*vault_target:0.2f}%)\n'
                                f':compass: vault strategy: [{vault_strat}](https://etherscan.io/address/{vault_strat})\n'
                    )
            if vault_strat_future_time != 0:
                vault_update_dt = datetime.datetime.fromtimestamp(vault_strat_future_time)
                embed.description += f':rocket: future strategy: [{vault_strat_future}](https://etherscan.io/address/{vault_strat_future})\n'
                vault_update_timeleft = ( vault_update_dt - datetime.datetime.now() )
                if vault_update_timeleft.total_seconds() < 0:
                    embed.description += f':alarm_clock: future strategy can be activated at any time; [subscribe to updates on Twitter](https://twitter.com/farmer_fud)'
                else:
                    embed.description += f':alarm_clock: future strategy can be activated at {vault_update_dt} GMT '
                    embed.description += f'({vault_update_timeleft.total_seconds()/3600:.1f} hours); [subscribe to updates on Twitter](https://twitter.com/farmer_fud)'
            else:
                embed.description += f':alarm_clock: no strategy updates are pending; [subscribe to updates on Twitter](https://twitter.com/farmer_fud)'
            await msg.channel.send(embed=embed)
        if '!profitshare' in msg.content:
            ps_address = vault_addr['profitshare']['addr']
            ps_deposits, ps_rewardperday, ps_rewardfinish, ps_stake_frac = get_profitsharestate()
            ps_apr = 100* (ps_rewardperday / ps_deposits) * 365
            ps_timeleft = ( ps_rewardfinish - datetime.datetime.now() )
            embed = discord.Embed(
                    title=f':bank::mag: FARM Profit Sharing',
                    description=f':map: Profitshare address: [{ps_address}](https://etherscan.io/address/{ps_address})\n'
                                f':moneybag: Profitshare deposits: `{ps_deposits:,.2f}` FARM (`{100*ps_stake_frac:0.2f}%` of supply)\n'
                                f':bar_chart: Profitshare rewards per day: `{ps_rewardperday:,.2f}` FARM'
                                f' (`{ps_apr:.2f}%` instantaneous APR)\n'
                                f':alarm_clock: Current harvests pay out until: `{ps_rewardfinish} GMT`'
                                f' (`{ps_timeleft.total_seconds()/3600:.1f}` hours)'
                    )
            await msg.channel.send(embed=embed)

def get_uniswapstate():
    uni_addr = UNIPOOL_ADDR
    poolvals = pool_contract.functions['getReserves']().call()
    uni_deposit_token = poolvals[0]*10**-18
    uni_deposit_pairing = poolvals[1]*10**-18
    token_contract = w3.eth.contract(address=ENOKI_ADDR, abi=UNIPOOL_ABI)
    token_totalsupply = token_contract.functions['totalSupply']().call()*10**-18
    uni_token_frac = uni_deposit_token / token_totalsupply
    return (uni_addr, uni_deposit_token, uni_deposit_pairing, uni_token_frac)


def get_profitsharestate():
    ps_address = vault_addr['profitshare']['addr']
    ps_contract = w3.eth.contract(address=ps_address, abi=PS_ABI)
    lp_addr = ps_contract.functions['lpToken']().call()
    lp_contract = w3.eth.contract(address=lp_addr, abi=VAULT_ABI)
    ps_decimals = lp_contract.functions['decimals']().call()
    lp_totalsupply = lp_contract.functions['totalSupply']().call()*10**(-1*ps_decimals)
    ps_rewardrate = ps_contract.functions['rewardRate']().call()
    ps_totalsupply = ps_contract.functions['totalSupply']().call()*10**(-1*ps_decimals)
    ps_rewardfinish = ps_contract.functions['periodFinish']().call()
    ps_rewardperday = ps_rewardrate * 3600 * 24 * 10**(-1*ps_decimals)
    ps_rewardfinishdt = datetime.datetime.fromtimestamp(ps_rewardfinish)
    ps_stake_frac = ps_totalsupply / lp_totalsupply
    return (ps_totalsupply, ps_rewardperday, ps_rewardfinishdt, ps_stake_frac)

def get_vaultstate(vault):
    vault_address = vault_addr[vault]['addr']
    vault_contract = w3.eth.contract(address=vault_address, abi=VAULT_ABI)
    vault_strat = vault_contract.functions['strategy']().call()
    vault_strat_future = vault_contract.functions['futureStrategy']().call()
    vault_strat_future_time = int(vault_contract.functions['strategyUpdateTime']().call())
    vault_decimals = int(vault_contract.functions['decimals']().call())
    vault_shareprice = vault_contract.functions['getPricePerFullShare']().call()*10**(-1*vault_decimals)
    vault_total = vault_contract.functions['underlyingBalanceWithInvestment']().call()*10**(-1*vault_decimals)
    vault_buffer = vault_contract.functions['underlyingBalanceInVault']().call()*10**(-1*vault_decimals)
    vault_target_numerator = vault_contract.functions['vaultFractionToInvestNumerator']().call()
    vault_target_denominator = vault_contract.functions['vaultFractionToInvestDenominator']().call()
    vault_target = vault_target_numerator / vault_target_denominator
    return (vault_address, vault_shareprice, vault_total, vault_buffer, vault_target, vault_strat, vault_strat_future, vault_strat_future_time)

def main():
    print(f'starting discord bot...')
    client.run(DISCORD_BOT_TOKEN)
    print(f'discord bot started')

if __name__ == '__main__':
    main()
