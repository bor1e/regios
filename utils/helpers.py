from urllib.parse import urlparse

# connect scrapyd service
localhost = 'http://localhost:6800'


def get_domain_from_url(url):
    complete_domain = urlparse(url).netloc
    domain_split = complete_domain.split('.')
    common_prefixes = ['www', 'en', 'fr', 'de', 'er', ]
    while domain_split[0] in common_prefixes:
        domain_split = domain_split[1:]

    domain = '.'.join(domain_split)
    return domain


def clean_url(url):
    _https = url[:5]
    https = (_https == 'https')
    _www = urlparse(url).netloc.split('.')[0]
    www = (_www == 'www')
    domain = get_domain_from_url(url)
    clean_url = 'https://' if https else 'http://'
    if www:
        clean_url += 'www.' + domain + '/'
    else:
        clean_url += domain + '/'
    return clean_url
