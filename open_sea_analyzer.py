import asyncio

import aiohttp
import numpy as np
import orjson
import requests


class Token:
    id = -1
    name = ''
    traitScore = dict()
    priceToBuyNow = -1
    priceOfLastSale = -1

    def __init__(self, id, name, traitScore, priceToBuyNow, priceOfLastSale):
        self.id = id
        self.name = name
        self.traitScore = traitScore
        self.priceToBuyNow = priceToBuyNow
        self.priceOfLastSale = priceOfLastSale


async def get(session: aiohttp.ClientSession, offset):
    print(offset)
    url = 'https://api.opensea.io/api/v1/assets?collection=cryptoadz-by-gremplin&offset=' + str(offset) + '&limit=50'
    resp = await session.request('GET', url=url)
    # Note that this may raise an exception for non-2xx responses
    # You can either handle that here, or pass the exception through
    data = await resp.json()
    return data


async def dos():
    data = []
    async with aiohttp.ClientSession() as session:
        for i in range(0, 300, 50):
            data.append(get(session, i))
        datas = await asyncio.gather(*data)
    print("pop")


asyncio.run(dos())


def getCollectionInfo():
    allTraits = dict()
    resp = requests.get('https://api.opensea.io/api/v1/collection/cryptoadz-by-gremplin')
    print(resp.status_code)
    collection = orjson.loads(resp.content)['collection']
    stats = collection['stats']
    count = stats['count']
    average_price = stats['average_price']
    num_owners = stats['num_owners']
    traits = collection['traits']
    minTraits = 0
    maxTraits = 0
    commonTraitMultiplier = 1
    for traitType in traits:
        allTraits[traitType.upper()] = dict()
        if traitType == '# Traits':
            minTraits = traits[traitType]['min']
            maxTraits = traits[traitType]['max']
            continue
        for trait in traits[traitType]:
            allTraits[traitType.upper()][trait.upper()] = traits[traitType][trait] / count
            commonTraitMultiplier *= 1 - traits[traitType][trait] / count
    print(count, average_price, num_owners, minTraits, maxTraits)
    return count, allTraits, commonTraitMultiplier


def getTraitsStat():
    traitTypes = allTraits.keys()
    return traitTypes
    # for traitType in allTraits:


def getTraitScoreOfItem(traits):
    traitScore = 100000000
    itemTraitMultiplier = commonTraitMultiplier
    for trait in traits:
        if trait['trait_type'] == '# Traits':
            continue
        traitScore = allTraits[trait['trait_type'].upper()][trait['value'].upper()] * traitScore
        itemTraitMultiplier /= 1 - allTraits[trait['trait_type'].upper()][trait['value'].upper()]
    return traitScore * itemTraitMultiplier


def getPriceToBuyNow(sellOrders):
    if sellOrders is None:
        return 0
    temp = sellOrders[0]["current_price"].split('.')[0]
    price = temp[0:-18] + '.' + temp[-18:]
    return float(price)


def getPriceOfLastSale(lastSale):
    if lastSale is None:
        return 0
    temp = lastSale["total_price"].split('.')[0]
    price = temp[0:-18] + '.' + temp[-18:]
    return float(price)


def getBatchOfItemsInCollection(offset):
    print(offset)
    resp = requests.get('https://api.opensea.io/api/v1/assets?collection=cryptoadz-by-gremplin&offset=' +
                        str(offset) + '&limit=50')
    collections = orjson.loads(resp.content)['assets']
    tokens = list()
    for item in collections:
        traitScore = getTraitScoreOfItem(item['traits'])
        priceToBuyNow = getPriceToBuyNow(item['sell_orders'])
        priceOfLastSale = getPriceOfLastSale(item['last_sale'])
        tokens.append(Token(item['token_id'], item['name'], traitScore, priceToBuyNow, priceOfLastSale))
    return tokens


def getAllOfItemsInCollection():
    allTokens = list()
    for offset in range(0, int(itemsCount), 50):
        allTokens.extend(getBatchOfItemsInCollection(offset))
    prices = list()
    traitScores = list()
    for token in allTokens:
        prices.append(token.priceOfLastSale)
        traitScores.append(token.traitScore)
    print("Price to traitScore correlation:", np.corrcoef(np.array(prices), np.array(traitScores))[0][1])
    # print("name: " + token.name + ", traitScore: " + str(token.traitScore) + ", priceToBuyNow:  " + str(
    #    token.priceToBuyNow) + ", priceOfLastSale: " + str(token.priceOfLastSale))
    # print("Price to traitScore covariance:", np.cov(np.array(prices), np.array(traitScores)))


itemsCount, allTraits, commonTraitMultiplier = getCollectionInfo()
getAllOfItemsInCollection()
