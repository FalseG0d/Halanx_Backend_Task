import re


def parse_campaign_code(s):
    k = re.findall('utm_source=([\w-]+)&', s)
    if len(k):
        return k[0]
    else:
        return ''
