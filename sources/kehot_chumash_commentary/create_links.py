
import django
django.setup()

from sefaria.model.text import Library

from sefaria.model import *
from sources.functions import *
from bs4 import BeautifulSoup
import pandas as pd
from sources.functions import eng_parshiot, heb_parshiot
from sefaria.tracker import modify_bulk_text
superuser_id = 171118


title = "The Kehot Chumash; A Chasidic Commentary"


if __name__ == "__main__":
    # Index().load({"title": title}).all_segment_refs()
    # al = Ref(f"{title}").autolinker()
    # Ref(f"{title}, Genesis").autolinker().refresh_links()
    Ref(f"{title}, Genesis").autolinker().rebuild_links()
    Ref(f"{title}, Exodus").autolinker().rebuild_links()
    Ref(f"{title}, Leviticus").autolinker().rebuild_links()
    Ref(f"{title}, Numbers").autolinker().rebuild_links()
    Ref(f"{title}, Deuteronomy").autolinker().rebuild_links()
    # all_segment_refs = Index().load({"title": title}).all_segment_refs()
    # commentary_segment_refs = []
    # for segment_ref in all_segment_refs:
    #     if "Overviews" in segment_ref.normal():
    #         continue
    #     parts = segment_ref.normal().rsplit(":", 1)
    #     result = parts[0] if len(parts) > 1 else segment_ref.normal()
    #     commentary_segment_refs.append(result)
    # commentary_segment_refs = list(set(commentary_segment_refs))

    print("hi")