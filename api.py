from collections import Counter
import json
import requests
import time
from datetime import datetime

API_KEY1 = 'REDACTED'
API_KEY2 = 'REDACTED'

LOCALE = 'en-US'
CURRENCY = 'USD'

ENDPOINT_URL = 'http://partners.api.skyscanner.net/apiservices'
API_VERSION = 'v1.0'


def perform_request(action, url_parameters=tuple(), query_parameters={}):
    url = '/'.join((ENDPOINT_URL, action, API_VERSION, *url_parameters))
    r = requests.get(url, params=dict(
        {'apiKey': API_KEY1}, **query_parameters))
    return r


r = perform_request('geo')
GEO = json.loads(r.content)

AIRPORTS = {}
for continent in GEO['Continents']:
    for country in continent['Countries']:
        if country['Id'] not in AIRPORTS:
            AIRPORTS[country['Id']] = []
        for city in country['Cities']:
            for airport in city['Airports']:
                if airport['Id'] not in AIRPORTS[country['Id']]:
                    AIRPORTS[country['Id']].append({'id': airport['Id'], 'location': airport['Location']})


def getroute(USERS, outboundDate, inboundDate):
    possible_countries = set().union(
        *(set(USERS[u]['dest_countries']) for u in USERS))

    stored_results = {}
    for uid in USERS:
        cur_user = USERS[uid]
        stored_results[uid] = {}
        for pc in possible_countries:
            r = perform_request(
                'browseroutes', (cur_user['country'], 'USD', 'en-US', cur_user['airport'], pc, outboundDate, inboundDate))
            j = json.loads(r.content)
            stored_results[uid][pc] = j

    min_country_price_sum = {}
    for pc in possible_countries:
        min_country_price_sum[pc] = 0
        for uid in USERS:
            try:
                min_country_price_sum[pc] += min(
                    [r['Price'] for r in stored_results[uid][pc]['Routes'] if 'Price' in r])
            except ValueError as e:
                min_country_price_sum[pc] += 1e10

    sel_countries = sorted(min_country_price_sum,
                           key=min_country_price_sum.get)[:3]

    possible_airports = []
    for uid in USERS:
        cur_user = USERS[uid]

        for sel_country in sel_countries:
            pd = sorted([(r['Price'], r['DestinationId'])
                         for r in stored_results[uid][sel_country]['Routes'] if 'Price' in r])

            for (p, d) in pd[:3]:
                for dest in stored_results[uid][sel_country]['Places']:
                    if dest['PlaceId'] == d:
                        airport = dest['SkyscannerCode']
                        if airport not in possible_airports:
                            possible_airports.append(airport)

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    query_parameters = {
        'currency': 'USD',
        'locale': 'en-US',
        'outboundDate': outboundDate,
        'inboundDate': inboundDate,
        'cabinClass': 'economy',
        'adults': 1
    }

    live_requests = {}
    for uid in USERS:
        live_requests[uid] = {}
        cur_user = USERS[uid]
        query_parameters['country'] = cur_user['country']
        query_parameters['originPlace'] = cur_user['airport'] + '-sky'
        for airport in possible_airports:
            query_parameters['destinationPlace'] = airport + '-sky'
            r = requests.post('/'.join((ENDPOINT_URL, 'pricing', API_VERSION)),
                              headers=headers,
                              data=dict({'apiKey': API_KEY1}, **query_parameters))
            l = r.headers['Location']
            live_requests[uid][airport] = l

    live_request_results = {}
    for uid in USERS:
        live_request_results[uid] = {}
        for airport in possible_airports:
            while True:
                r = perform_request(
                    'pricing', (live_requests[uid][airport].split('/')[-1],))
                try:
                    j = json.loads(r.content)
                    if j['Status'] == 'UpdatesComplete':
                        break
                except json.decoder.JSONDecodeError as e:
                    pass
                time.sleep(0.5)

            live_request_results[uid][airport] = json.loads(r.content)

    min_price_dest_airport = {}
    for uid in USERS:
        min_price_dest_airport[uid] = {}
        for airport in possible_airports:
            min_price_dest_airport[uid][airport] = 1e10
            for i in live_request_results[uid][airport]['Itineraries']:
                p = min(x['Price'] for x in i['PricingOptions'])
                if p < min_price_dest_airport[uid][airport]:
                    min_price_dest_airport[uid][airport] = p

    return min_price_dest_airport
