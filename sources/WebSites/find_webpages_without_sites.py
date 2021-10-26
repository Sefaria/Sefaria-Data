from sefaria.model.webpage import *


def find_webpages_without_websites(test=True, hit_threshold=50, last_linker_activity_day=20):
    from datetime import datetime, timedelta
    webpages = WebPageSet()
    new_active_sites = Counter()   # WebSites we don't yet have in DB, but we have corresponding WebPages accessed recently
    unactive_unacknowledged_sites = {}  # WebSites we don't yet have in DB, and we have correpsonding WebPages but they have not been accessed recently
    last_active_threshold = datetime.today() - timedelta(days=last_linker_activity_day)

    bad_regexes = WebPage.excluded_pages_url_regex()[:-1] + "|\d{3}\.\d{3}\.\d{3}\.\d{3})"  #delete any page that matches the regex produced by excluded_pages_url_regex() or in IP form
    for i, webpage in enumerate(webpages):
        if i % 100000 == 0:
            print(i)
        updated_recently = webpage.lastUpdated > last_active_threshold
        website = webpage.get_website(dict_only=True)
        if website == {} and len(webpage.domain.strip()) > 0 and re.search(bad_regexes, webpage.url) is None:
            if updated_recently:
                new_active_sites[webpage.domain] += 1
            else:
                if webpage.domain not in unactive_unacknowledged_sites:
                    unactive_unacknowledged_sites[webpage.domain] = []
                unactive_unacknowledged_sites[webpage.domain].append(webpage)

    sites_added = []
    for site, hits in new_active_sites.items():
        if hits > hit_threshold:
            newsite = WebSite()
            newsite.name = site
            newsite.domains = [site]
            newsite.is_whitelisted = True
            newsite.linker_installed = True
            if not test:
                newsite.save()
            print("Created new WebSite with name='{}'".format(site))
            sites_added.append(site)

    print(sites_added)
    print("****")
    for site, hits in unactive_unacknowledged_sites.items():
        if site not in sites_added:  # if True, site has not been updated recently
            print("Deleting {} with {} pages".format(site, len(unactive_unacknowledged_sites[site])))
            for webpage in unactive_unacknowledged_sites[site]:
                if not test:
                    webpage.delete()
