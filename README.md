# regios

## installing regios
1. clone this repo with `git clone https://github.com/bor1e/regios.git`
2. `cd regios`
3. `pip install -r requirements.txt`
4. creating superuser `python3 manage.py createsuperuser`

## starting regios
1. first start the the scrapy server on `localhost:19860` with:
`cd scrapy_app/ && scrapyd`
2. go back to the regios folder and start the Django Server: 
`cd .. && python3 manage.py runserver`

If you wnat to change the port of `scrapyd`than you need to update the `http_port`value in `scrapy_app/scrapy.cfg` __and__ `api/views.py`

## TODO
- check if scrapyd is running (simple post for list)
- block in layout for errors
- ~~get the url if set in session inside start input~~
- ~~filter return back to display~~
- check the todos inside the code
- pandas on db
- include `kontakt`-sites for zip code findings
- ~~time required for fullscan update~~
- display strange behaviour (e.g. zero external links ) as black nodes in sigma graph
- try to get links from javascript `process_value` https://docs.scrapy.org/en/latest/topics/link-extractors.html
- analyse structure of website with most external links using [urllib](https://docs.python.org/3/howto/urllib2.html) for textanalyse / site classification
- selenium acceptance tests?!
