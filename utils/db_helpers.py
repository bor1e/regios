from start.models import Domains as D
import re

keys = ['medical', 'health', 'gesund', 'pharma', 'clinic']
start = 90000
end = 92000


def pks_of_domains_within_ziprange_and_keys(zip_start, zip_end, keys):
    plz = [d.pk for d in D.objects.all()
           if d.has_related_info() and d.info.zip and
           d.info.zip > zip_start and d.info.zip < zip_end and
           not d.info.is_suspicious]
    fs = [d.pk for d in D.objects.filter(pk__in=plz)
          if not d.is_suspicious]

    pattern = r'(' + '|'.join(keys) + ')'
    # test_domains = ['bayern-design.de', 'tanzzentrale.de']
    ds = list()
    for d in D.objects.all():
        if not d.has_related_info():
            continue
        text = ''
        args = ['name', 'title', 'desc', 'keywords']
        for i in args:
            if d.info.__dict__[i]:
                text += ' ' + d.info.__dict__[i]
        # append = False
        if re.search(pattern, text, flags=re.IGNORECASE):
            ds.append(d.pk)
        #    append = True

        # if d.domain in test_domains:
        #     print(d.domain, '\n', text, '\n', append)

    set_fs = set(fs)
    result = set_fs.intersection(set(ds))

    return list(result)


print(pks_of_domains_within_ziprange_and_keys(start, end, keys))

'''
def to_pandas(pks):
    ds = D.objects.filter(pk__in=pks)
    keywords = ['zip', 'tip', 'fullscan']  # 'externals', 'referenced_counter']
    mylist = [[] for _ in range(len(keywords))]
    domains = list()
    for d in ds:
        domains.append(d.domain)
        mylist['zip'] = d.info.zip
        mylist['tip'] = d.info.tip
        mylist['fullscan'] = d.fullscan
        for i, k in enumerate(keywords):
            if k in value and value[k]:
                if not isinstance(value[k], int):
                    mylist[i].append(value[k][:20])
                else:
                    mylist[i].append(value[k])
            else:
                mylist[i].append(None)

    d = {}
    d['domains'] = domains
    for i, k in enumerate(keywords):
        d[k] = mylist[i]

    length_of_elems = len(domains)
    for n, i in enumerate(mylist):
        if len(mylist[n]) != length_of_elems:
            # self.logger.error('wrong: %s', keywords[n])
            pass
    return d
'''
# pks = suggested_pk(90000,92000,['medical','pharma','klinik','clini', 'health','gesund'])
# not_scanned = [d.pk for d in D.objects.filter(pk__in=pks) if not d.fullscan]
# (122, 34)
