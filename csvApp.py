import csv
import os.path

class CsvData:
    # BU CLASS DISARIDAN __INIT__ FONKSİYONUNDA ZAMAN BİLGİSİNİ ALIP GEREKLİ OLAN ORTAMI OLUŞTURMAK İÇİN CSV DOSYALARINI
    # VE DİZİN İŞLEMLERİNİ YAPACAKTIR
    def __init__(self, dateTime):
        # Csv dosyasında kullanılacak coloumn isimlerini buradan istediğiniz kadar ayarlıyorsunuz. Göndermek istediğiniz
        # kadar coloumn ismi yazınız.
        self.columnNames = ["bir", "iki", "uc", "dort", "bes", "altı", "yedi", "sekiz", "dokuz", "on", "onbir", "oniki",
                            "onuc", "ondort", "onbes", "onaltı", "onyedi", "onsekiz", "ondokuz", "yirmi","yirmibir", "yirmiki",
                            "yirmiuc", "yirmidort", "yirmibes", "yirmialtı", "yirmiyedi", "yirmisekiz", "yirmidokuz", "otuz", "otuzbir"]

        # Csv dosyalarını isimlerini değişken içine atıyoruz. Dışarıdan gelen programın başlama zamanının değerini ve
        # ana csv dosyasının isimlerini belirliyoruz. Ana dosyanın icinde \data isimli path yolunu da belirliyoruz.
        self.dateTime = dateTime
        self.mainCsvName = r".\data\mainRecords.csv"
        self.inputCsv = rf".\data\{self.dateTime}.csv"
        self.new_path = r'.\data'

        # Os kütüphanesi ile path sorgulaması yapıyoruz eğer csv dosyalarımız belirlediğimiz path de yoksa yenilerini
        # oluşturuyoruz.

        self.check_file_main = os.path.isfile(self.mainCsvName)
        self.check_file_current = os.path.isfile(self.inputCsv)

        if not os.path.exists(self.new_path):
            os.makedirs(self.new_path)

        if not self.check_file_main:
            with open(self.mainCsvName, 'w', newline='') as csvFile:
                self.writer = csv.DictWriter(csvFile, fieldnames=self.columnNames, delimiter=';')
                self.writer.writeheader()
                csvFile.flush() # flush ile beklemede olan işlemi hemen yapmasını sağlıyoruz

        if not self.check_file_current:
            with open(self.inputCsv, 'w', newline='',) as csvIFile:
                self.writer = csv.DictWriter(csvIFile, fieldnames=self.columnNames, delimiter=';')
                self.writer.writeheader()
                csvIFile.flush() # flush ile beklemede olan işlemi hemen yapmasını sağlıyoruz

    def csvdatainput(self,listOfDatas):
        # Dışarıdan datalarının listesini alıyoruz. Aldığımız datalar coloumn isimleri ile aynı sayıda elemanı olmalı!
        self.listOfDatas = listOfDatas
        if len(self.listOfDatas[0]) == len(self.columnNames):
            with open(self.inputCsv, 'a', newline='') as csvIFile, open(self.mainCsvName, 'a', newline='') as csvFile:
                self.writerToInput = csv.DictWriter(csvIFile, fieldnames=self.columnNames, delimiter=";")
                self.writerToMain = csv.DictWriter(csvFile, fieldnames=self.columnNames, delimiter=";")
                self.writerToInput.writerows(self.listOfDatas)
                self.writerToMain.writerows(self.listOfDatas)
                csvFile.flush()
                csvIFile.flush()



"""
'execution_time','data1', 'data2', 'data3', 'data4', 'data5','data6', 'data7', 'data8', 'data9', 'data10',
                            'data11', 'data12', 'data13', 'data14', 'data15','data16', 'data27', 'data18', 'data19',
                            'data20'
"time_ms","velocity_km","b_C","TBV_V","energy_left_WH","MDT_C"
"""