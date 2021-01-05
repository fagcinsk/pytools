#!/usr/bin/env python
from concurrent.futures import ThreadPoolExecutor
from re import compile
from time import time

from dns.resolver import Answer, Resolver
from requests import get
from tqdm import tqdm


ipv4_re = compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')


class Dns:
    """Perform DNS related actions"""

    @staticmethod
    def _get_nameservers() -> list:
        url = 'https://public-dns.info/nameservers.csv'
        lines = get(url).text.splitlines(False)
        col_names = lines[0].split(',')
        """
        ip_address
        name
        as_number
        as_org
        country_code
        city
        version
        error
        dnssec
        reliability
        checked_at
        created_at
        """
        items = []
        for line in lines[1:]:
            row = dict(zip(col_names, line.split(',')))
            ip = row['ip_address']
            if not ipv4_re.match(ip):
                continue
            if row.get('reliability') != '1.00':
                continue
            items.append(row)
        return items

    def _check(self, nameserver):
        resolver = Resolver(configure=False)
        resolver.nameservers = [nameserver['ip_address']]
        try:
            t = time()
            res: Answer = resolver.resolve(
                self.domain_to_resolve, lifetime=0.1)
            if len(res.rrset) > 0:
                nameserver['time'] = round((time() - t) * 1000)
        except:
            pass
        return nameserver

    def fastest(self, domain_to_resolve='ya.ru'):
        """Retrieves ipv4 dns nameservers,
        and get fastest (<100ms) for your location/network."""
        self.domain_to_resolve = domain_to_resolve
        nameservers = self._get_nameservers()
        with ThreadPoolExecutor() as executor:
            results = []
            for res in tqdm(executor.map(self._check, nameservers), total=len(nameservers)):
                tim = res.get('time')
                if tim:
                    results.append(res)

        for res in sorted(results, key=lambda row: row['time']):
            ip = res.get('ip_address')
            name = res.get('name') or '-'
            tim = res.get('time') or '-'
            print(f'{ip:<15} {tim:>3} ms {name}')
