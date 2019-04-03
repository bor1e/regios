from urllib.parse import urlparse


def get_domain_from_url(url):
    complete_domain = urlparse(url).netloc
    domain_split = complete_domain.split('.')
    common_prefixes = ['www', 'en', 'fr', 'de', 'er', ]
    while domain_split[0] in common_prefixes:
        domain_split = domain_split[1:]

    domain = '.'.join(domain_split)
    return domain
