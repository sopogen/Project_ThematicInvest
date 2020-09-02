import csv
import platform
import os


class Writer(object):
    def __init__(self, category_name, date):
        self.user_operating_system = str(platform.system())

        self.category_name = category_name

        self.date = date
        self.save_year = self.date['year']
        self.save_month = None
        self.save_day = None
        self.initialize_month()
 
        self.file = None
        self.initialize_file()

        self.wcsv = csv.writer(self.file)

    def initialize_month(self):
        if len(str(self.date['month'])) == 1:
            self.save_month = "0" + str(self.date['month'])
        else:
            self.save_month = str(self.date['month'])
        if len(str(self.date['day'])) == 1:
            self.save_day = "0" + str(self.date['day'])
        else:
            self.save_day = str(self.date['day'])

    def initialize_file(self):
        #Window
        if self.user_operating_system == "Windows":
            self.file = open(''
                             + self.category_name + '_' + str(self.save_year) + str(self.save_month)
                             + str(self.save_day) + '.csv', 'w', encoding='euc-kr', newline='')
        # Other OS uses utf-8
        else:
            self.file = open('/Users/jungyulyang/programming/Project_ThematicInvest/data/today_news_data/'
                             + self.category_name + '_' + str(self.save_year) + str(self.save_month)
                             + str(self.save_day) + '.csv', 'w', encoding='utf-8',
                             newline='')

    def get_writer_csv(self):
        return self.wcsv
    
    def get_file_name(self):
        fname = '/Users/jungyulyang/programming/Project_ThematicInvest/data/today_news_data/'\
            + self.category_name + '_' + str(self.save_year) + str(self.save_month)\
            + str(self.save_day) + '.csv'
        return fname

    def close(self):
        self.file.close()

