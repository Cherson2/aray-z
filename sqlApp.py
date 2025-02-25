import sqlite3
import os.path

class SqlData:
    def __init__(self, dateTime):

        self.columnNames = "bir integer, iki integer, uc integer, dort integer, bes integer, altı integer, " \
                           "yedi integer, sekiz integer, dokuz integer, ten integer, onbir integer, oniki integer, " \
                           "onuc integer, ondort integer, onbes integer, onaltı integer, onyedi integer, " \
                           "onsekiz integer, ondokuz integer, yirmi integer,yirmibir integer, yirmiki integer, " \
                           "yirmiuc integer, yirmidort integer, yirmibes integer, yirmialtı integer, " \
                           "yirmiyedi integer, yirmisekiz integer, yirmidokuz integer, otuz integer, otuzbir integer"


        self.dateTime = str(dateTime)
        self.dateTime = "sql" + self.dateTime
        self.dateTime = self.dateTime.replace("-", "a")
        self.sqlName = r".\sql\mainSql.db"
        self.new_path = r'.\sql'

        self.check_file_main = os.path.isfile(self.sqlName)
        if not os.path.exists(self.new_path):
            os.makedirs(self.new_path)


        self.con = sqlite3.connect(self.sqlName)
        self.cur = self.con.cursor()
        self.cur.execute(f"""CREATE TABLE IF NOT EXISTS main ({self.columnNames})""")
        self.cur.execute(f"""CREATE TABLE IF NOT EXISTS {self.dateTime} ({self.columnNames})""")
        self.con.commit()

    def sqldatainput(self,listOfDatas):
        # Dışarıdan datalarının listesini alıyoruz. Aldığımız datalar coloumn isimleri ile aynı sayıda elemanı olmalı!
        self.listOfDatas = list(listOfDatas[0].values())

        text_list = ["INSERT INTO main VALUES (",f"INSERT INTO {self.dateTime} VALUES("]
        if len(self.listOfDatas) != 31:
            for _ in range(31 - len(self.listOfDatas)):
                self.listOfDatas.append(0)

        for i in text_list:
            for a in self.listOfDatas:
                if a == "--" or a == '':
                    i = i + "0" + ","
                else:
                    i = i + a + ","
            i = i[:len(i)-1]
            i = i + ")"
            print(i)
            self.cur.execute(i)
        self.con.commit()
    def connection_close(self):
        self.con.close()

"""
'execution_time','data1', 'data2', 'data3', 'data4', 'data5','data6', 'data7', 'data8', 'data9', 'data10',
                            'data11', 'data12', 'data13', 'data14', 'data15','data16', 'data27', 'data18', 'data19',
                            'data20'
"time_ms","velocity_km","b_C","TBV_V","energy_left_WH","MDT_C"
"""