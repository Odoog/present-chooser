import logging
from models.good import Good
import pygsheets


class SheetsClient:

    def __init__(self, table_key):
        self.client = pygsheets.authorize(service_file='account_credentials.json')
        self.sheet = self.client.open_by_key(table_key)
        self.db_sheet = self.sheet.worksheet_by_title('База товаров (чек боксы)')

    def get_all_goods(self):
        values = self.db_sheet.get_all_values(returnas='matrix')
        for key, row in enumerate(values[1:]):
            good = Good(row[0], row[1], row[2], row[3], row[4], row[5])
            current_prices = good.get_current_prices()
            if current_prices is not None:
                for price_key, price in enumerate(current_prices):
                    self.db_sheet.update_value((key + 2, 31 + price_key), price)

    def add_operation(self,
                      date,
                      worker_id,
                      worker_full_name,
                      product,
                      article,
                      operation,
                      operation_count,
                      defect_count,
                      defect_types,
                      operation_price,
                      start_time,
                      hold_time,
                      end_time,
                      oper_target,
                      work_time):
        self.template_sheet.insert_rows(row=self.find_last_free_row_id_in_operations_sheet() - 1,
                                        number=1,
                                        values=[[
                                            date,
                                            worker_id,
                                            worker_full_name,
                                            product,
                                            article,
                                            operation,
                                            operation_count,
                                            defect_count,
                                            defect_types,
                                            operation_price,
                                            '=G{}*J{}'.format(self.find_last_free_row_id_in_operations_sheet(),
                                                              self.find_last_free_row_id_in_operations_sheet()),
                                            start_time,
                                            hold_time,
                                            end_time,
                                            int(work_time),
                                            int(work_time) / int(oper_target),
                                            '=G{}-P{}'.format(self.find_last_free_row_id_in_operations_sheet(),
                                                              self.find_last_free_row_id_in_operations_sheet())
                                        ]])

    def get_possible_products(self):
        products_names = set()
        values = self.operations_sheet.get_all_values(returnas='matrix')
        for row in values[1:]:
            if row[0] != "":
                products_names.add(row[0])
        return list(products_names)

    def get_possible_operations_by_product(self, product_name):
        operations_names = set()
        values = self.operations_sheet.get_all_values(returnas='matrix')
        for row in values[1:]:
            if row[0] == product_name:
                operations_names.add(row[1])
        print(list(operations_names))
        return list(operations_names)

    def get_operation_price(self, product_name, operation_name):
        values = self.operations_sheet.get_all_values(returnas='matrix')
        for row in values[1:]:
            if row[0] == product_name and row[1] == operation_name:
                return row[2]
        return -1

    def get_operation_target(self, product_name, operation_name):
        values = self.operations_sheet.get_all_values(returnas='matrix')
        for row in values[1:]:
            if row[0] == product_name and row[1] == operation_name:
                return row[3]
        return -1

    def get_possible_articles_by_product(self, product_name):
        articles = set()
        logging.info('Getting all articles by product <{}>'.format(product_name))
        values = self.articles_sheet.get_all_values(returnas='matrix')

        for row in values[1:]:
            logging.info('For product with name <{}>'.format(row[0]))
            if row[0] == product_name:
                articles.add(row[1])
                logging.info('Add article {}'.format(row[1]))
        return list(articles)

    def get_possible_defects_by_product(self, product_name):
        defects = set()
        values = self.defects_sheet.get_all_values(returnas='matrix')
        for row in values[1:]:
            if row[0] == product_name:
                defects.add(row[1])
        return list(defects)

    def check_auth_code(self, auth_code):
        values = self.codes_sheet.get_all_values(returnas='matrix')
        for key, row in enumerate(values):
            if row[0] == auth_code:
                self.codes_sheet.delete_rows(key + 1)
                return True
        return False
