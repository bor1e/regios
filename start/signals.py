'''
def save_domain(sender, instance, **kwargs):
    if sender.fullscan and sender.infoscan and sender.externalscan:
        sender.fullscan = True
        sender.save()
'''
