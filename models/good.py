import re

import requests

class Good:

    def __init__(self,
                 name,
                 brand,
                 shop,
                 price,
                 link,
                 photo_link):
        self.name = name
        self.brand = brand
        self.shop = shop
        self.price = price
        self.link = link
        self.photo_link = photo_link

    def get_current_prices(self):
        try:
            site_code = requests.get(self.link).text
            search_result = re.search(r'(\d{1,3}(?:[.,\s]\d{3})*(?:[.,\s]\d{2})?)\s?((Р|р)(уб)?\.|₽)', site_code)
            if search_result is not None:
                return search_result.groups()
            else:
                return None
        except Exception:
            pass
