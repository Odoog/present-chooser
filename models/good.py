import re

import requests

class Good:

    def __init__(self,
                 ind,
                 name,
                 brand,
                 shop,
                 price_actual,
                 link,
                 photo_link,
                 is_local_brand,
                 is_universal,
                 category,
                 price,
                 age,
                 sex,
                 age2,
                 receiver,
                 is_universal_reason,
                 reason,
                 price_parsing,
                 rating):
        self.ind = ind
        self.name = name
        self.brand = brand
        self.shop = shop
        self.price_actual = price_actual
        self.link = link
        self.photo_link = photo_link
        self.is_local_brand = is_local_brand
        self.is_universal = is_universal
        self.category = category
        self.price = price
        self.age = age.split(';')
        self.sex = sex.split(';')
        self.age2 = age2.split(';')
        self.receiver = receiver.split(';')
        self.is_universal_reason = is_universal_reason
        self.reason = reason.split(';')
        self.price_parsing = price_parsing
        try:
            self.rating = int(rating)
        except ValueError:
            self.rating = 0

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
