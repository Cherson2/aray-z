import csvApp
import sqlApp
import datetime
import logging
import serial
import serial.tools.list_ports
import subprocess
import sys
import traceback
import pyqtgraph as pg
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QHBoxLayout, \
    QGroupBox, QTabWidget, QSizePolicy, QTextEdit, QComboBox


class GraphWindow(QWidget):
    def __init__(self, title, name, parent):
        super().__init__()
        self.setWindowTitle(name.replace(":", ""))
        self.setWindowIcon(QIcon(r'.\icon\icon.png'))
        self.setGeometry(150, 150, 400, 300)
        self.parent = parent
        self.title = title
        self.name = name
        layout = QVBoxLayout()

        self.graph_widget = pg.PlotWidget()
        self.set_graph_style(self.graph_widget)
        layout.addWidget(self.graph_widget)

        self.pen = pg.mkPen(color='w', width=3)
        self.plot = self.graph_widget.plot([], [], pen=self.pen)

        self.setLayout(layout)

    def set_graph_style(self, graph):
        # X ve Y eksen renklerini ayarla
        graph.setLabel(
            "left",
            f'<span style="color: white; font-size: 18px">{self.name.replace(":", "")}</span>'
        )
        graph.setLabel(
            "bottom",
            '<span style="color: white; font-size: 18px">Time (s)</span>'
        )
        graph.setXRange(0, 200)
        graph.setYRange(0, 100)
        graph.getPlotItem().getAxis('bottom').setPen(pg.mkPen(color='w', width=3))
        graph.getPlotItem().getAxis('left').setPen(pg.mkPen(color='w', width=3))
        graph.setStyleSheet(
            "border: 5px solid white; border-width : 1px 1px;"
            "qproperty-alignment: 'AlignCenter'; ")
        graph.setBackground("#333333")
        graph.enableAutoRange()

    def update_graph(self, time, data):
        self.plot.setData(time, data)  # Grafiği güncelle

    def closeEvent(self, event):
        event.accept()
        self.parent.remove_window(self.name)


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_color = "border: 5px solid white;background-color: #333333; border-width : 1px 1px;" \
                          "font-size : 10pt; qproperty-alignment: 'AlignCenter'; border-radius: 15px;"
        self.text_change = "border: 5px solid yellow;background-color: #333333; border-width : 1px 1px;" \
                           "font-size : 10pt; qproperty-alignment: 'AlignCenter'; border-radius: 15px;"

        self.default_palette = self.palette()
        self.setStyleSheet(self.text_color)
        self.setFixedSize(150, 50)

    def mousePressEvent(self, event):
        self.clicked.emit()
        self.set_effect()

    def set_effect(self):
        self.setStyleSheet(self.text_change)

    def reset_effect(self):
        self.setStyleSheet(self.text_color)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Yılkat Electromobile Data Interface")
        self.setWindowIcon(QIcon(r'.\icon\icon.png'))

        # Alt fonksiyonlarda kullanılacak değişkenleri init sınıfında None atamasını yapıyoruz
        self.sqlSave = None
        self.disconnect_ports = None
        self.text_port_name = None
        self.ser = None
        self.current_second = None
        self.current_date_time = None
        self.csvSave = None
        self.timerOfdata = None
        self.timerOfconnection = None
        self.myports = None
        self.list_ports_new = None
        self.dataNumber = None
        self.esik_degerleri_list = None
        self.esik_main_degerler = None
        self.data_list = None
        self.line = None
        self.append_text = None
        self.icon_pixmap = None
        self.ana_label = None
        self.icon_label = None
        self.sequence = None
        self.all_data = None
        self.say = None
        self.buttons = {}
        self.windows = {}

        # Comboboxlarda kullanılacak seceneklerin listeleri. Port isimleri ilk başta default None değeri olacak sonradan
        # aşağıda ki işlemler ile elemanları değieşecek. Baudrate ise kendimiz buradan hangi değerleri olacağını ayarlac
        # ağız
        self.list_ports = ['None']
        self.list_of_baudrates = ["4800", "9600", "115200"]

        # Port sorgusu icin gerekli olan cmd komudunu variable atıyoruz
        self.command = "python -m serial.tools.list_ports"

        self.connect_text = "Connect"
        self.port_name_label = QLabel("Port Name:")
        self.port_name_label.setFont(QFont("SansSerif", 8))
        self.port_name_label.setStyleSheet("color: white;")

        self.connection_status_label = QLabel("Connection Status: Integrity warning!")
        self.connection_status_label.setFont(QFont("SansSerif", 8))
        self.connection_status_label.setStyleSheet("color: white;")

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet("""
        QPushButton {
            background-color: #800080; 
            border: 1px solid black;
        }
        QPushButton:hover {
            background-color: grey;
        }
    """)  # Mor rengi
        self.refresh_button.clicked.connect(self.refresh_port_name_lists)
        # Port comboboxını oluşturuyoruz ve list_ports listesine bağlıyoruz.
        self.combobox_port = QComboBox()
        self.combobox_port.addItems(self.list_ports)
        self.combobox_port.setStyleSheet("border: 2px solid white")
        # Baudrate comboboxını oluşturuyoruz ve list_of_baudrate listesine bağlıyoruz.
        self.combobox_baudrate = QComboBox()
        self.combobox_baudrate.addItems(self.list_of_baudrates)
        self.combobox_baudrate.setStyleSheet("border: 2px solid white")
        self.combobox_baudrate.setCurrentIndex(self.list_of_baudrates.index('9600'))  # Default item

        self.combobox_baudrate_name = QLabel("Baudrate:")
        self.combobox_baudrate_name.setFont(QFont("SansSerif", 8))
        self.combobox_baudrate_name.setStyleSheet("color: white;")

        self.port_status_frame = QFrame()
        self.port_status_frame.setStyleSheet("background-color: #333333; border-radius: 5px; padding: 5px;")
        self.port_status_layout = QHBoxLayout()

        self.port_status_layout.addWidget(self.port_name_label)
        self.port_status_layout.addWidget(self.combobox_port)
        self.port_status_layout.addWidget(self.combobox_baudrate_name)
        self.port_status_layout.addWidget(self.combobox_baudrate)
        self.port_status_layout.addWidget(self.connection_status_label)
        self.port_status_layout.addWidget(self.refresh_button)
        self.port_status_frame.setLayout(self.port_status_layout)

        # SEKMELER İCİN YAZILAN KODLARIN BASI
        self.tabs = QTabWidget()

        # Main tab sekmesi icin gerekli olan atamaları yapıyoruz genel layout oluşturup onu QVBoxLayout olarak atıyoruz.
        # Üst taraftaki layout ile main tabın layout arasına 50 boşluk atıyoruz.
        # Son olarak main tabın layoutunu kendisine ekliyoruz.
        self.main_tab = QWidget(self)

        self.layout_of_main = QVBoxLayout()
        self.layout_of_main.addSpacing(50)
        self.main_tab.setLayout(self.layout_of_main)

        # Bağlantı sağlanın değerler ve alarm ikonu eklemek için oluşturacağımız widgetları saklayacak bir liste
        # oluşturuyoruz. Bunun yanında genel olarak QLabel oluşturuyoruz ve listeye atıyoruz.
        self.all_mainisAlarm = []
        self.all_mainicon_labels = []
        # Burada tabların içindeki ilk 2 labeli oluşturup isim ve değer atamaları için liste oluşturuyoruz.
        # İsim ve değer değişikliği buradan yapabilirsin.
        self.inner_labes_names_lists = [['First:', 'Second:', 'Third:', 'Fourth:'], ['Fifth:', 'Sixth:', 'Seventh:']]
        self.inner_labes_value_names_lists = [[QLabel(title, self) for title in self.inner_labes_names_lists[0]],
                                              [QLabel(title, self) for title in self.inner_labes_names_lists[1]]]

        self.main_labels_lists = [[ClickableLabel() for _ in range(4)],
                                  [ClickableLabel() for _ in range(3)]]

        self.inner_labes_values_lists = [['0', '0', '0', '0'], ['0', '0', '0']]
        self.inner_labes_values_q = [[QLabel(value, self) for value in self.inner_labes_values_lists[0]],
                                     [QLabel(value, self) for value in self.inner_labes_values_lists[1]]]

        # Eşik değeri gecince alarm ikonu eklemek için üçüncü labeli oluşturuyoruz ve bu labelları sonra kullanmak için
        # liste içine alıyoruz.
        self.main_inner_icons = [QLabel(self) for _ in range(7)]
        self.all_mainicon_labels = []

        # İcerideki 3 labelin dış borderlarını kaldırıyoruz. İstenildiği durumda buradan stil değişikliği yapılabilir
        for index, _ in enumerate(self.main_labels_lists):
            for index_2, label in enumerate(_):
                name = self.inner_labes_names_lists[index][index_2]
                label.clicked.connect(lambda name_in=name, button=label: self.label_clicked(button, name_in))
                self.buttons[name] = label

        for label in self.inner_labes_value_names_lists + self.inner_labes_values_q:
            for label_inner in label:
                label_inner.setStyleSheet("border: none;")
                label_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for label in self.main_inner_icons:
            label.setStyleSheet("border: none;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.all_mainicon_labels = [[self.main_inner_icons[i] for i in range(4)], [self.main_inner_icons[i] for i in
                                                                                   range(4, 7)]]
        self.main_inner_layouts = [QHBoxLayout() for _ in range(2)]

        for index, inner in enumerate(self.main_inner_layouts):
            for i in range(4):
                if i != 3 or index != 1:
                    row_layout = QHBoxLayout()
                    row_layout.addWidget(self.inner_labes_value_names_lists[index][i])
                    row_layout.addWidget(self.inner_labes_values_q[index][i])
                    say = index * 4 + i
                    row_layout.addWidget(self.main_inner_icons[say])
                    self.main_labels_lists[index][i].setLayout(row_layout)
                    inner.addWidget(self.main_labels_lists[index][i])
                    inner.addSpacing(20)
                self.layout_of_main.addLayout(inner)
                self.layout_of_main.addSpacing(10)

        # Detail tabını oluşturuyoruz ve gerekli layout , widget atamalarını yapıyoruz. Üstteki layout ile arasın boşluk
        # koyuyoruz
        self.detail = QWidget(self)
        self.layout_detail = QVBoxLayout()
        self.layout_detail.addSpacing(50)
        self.detail.setLayout(self.layout_detail)

        # Diğer fonksiyonlarda kullanılması için liste içine atama yapıyoruz
        self.all_main_labels = []
        self.all_inner_labels_2 = []
        self.all_icon_label = []
        self.all_isAlarm = []

        # Deger isimleri icindeki labelların isim atamasını yapıyoruz.
        self.inner_labels_names = [['Eighth:', 'Ninth:', 'Tenth:', 'Eleventh:'],
                                   ['Twelfth:', 'Thirteenth:', ' Fourteenth:', 'Fifteenth:'],
                                   ['Fifteenth:', 'Seventeenth:', 'Eighteenth:', 'Nineteenth:'],
                                   ['Twentieth:', 'Twenty-First:', 'Twenty-Second:', 'Twenty-Third:'],
                                   ['Twenty-Fourth:', 'Twenty-Fifth:', 'Twenty-Sixth:', 'Twenty-Sixth:'],
                                   ['Twenty-Eighth:', 'Twenty-Ninth:', 'Thirtieth:', 'Thirty-First:'], ]

        # Her bir satırın dış labellarını oluşturuyouz. Ayrıca stillerini de ayarlıyoruz. Her bir label için default
        # değer atıyoruz. Bütün labelları hepsini yukarıda oluşturuduğumuz listenin içine atıyoruz ki sonradan ulaşıp
        # oynama yapılabilsin
        for _ in range(6):
            self.detail_labels = [ClickableLabel() for _ in range(4)]

            for index, label in enumerate(self.detail_labels):
                label.setFixedSize(200, 50)
                name = self.inner_labels_names[_][index]
                label.clicked.connect(lambda name_in=name, button=label: self.label_clicked(button, name_in))
                self.buttons[name] = label

            self.detail_inner_labels_1 = [QLabel(title, self) for title in self.inner_labels_names[_]]

            self.inner_labels_values = ['0', '0', '0', '0']
            self.detail_inner_labels_2 = [QLabel(value, self) for value in self.inner_labels_values]
            self.detail_inner_icons = [QLabel(self) for _ in range(24)]

            for label in self.detail_inner_labels_1 + self.detail_inner_labels_2 + self.detail_inner_icons:
                label.setStyleSheet("border: none;")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Dizilere ekleme
            self.all_main_labels.append(self.detail_labels)
            self.all_inner_labels_2.append(self.detail_inner_labels_2)
            self.all_icon_label.append(self.detail_inner_icons)
            # Layout oluşturma ve QLabel'leri ekleme
            self.detail_layout = QHBoxLayout()
            for i in range(4):
                self.row_layout = QHBoxLayout()
                self.row_layout.addWidget(self.detail_inner_labels_1[i])
                self.row_layout.addWidget(self.detail_inner_labels_2[i])
                self.row_layout.addWidget(self.detail_inner_icons[i])
                self.detail_labels[i].setLayout(self.row_layout)
                self.detail_layout.addWidget(self.detail_labels[i])
                self.detail_layout.addSpacing(30)

            self.layout_detail.addLayout(self.detail_layout)
            self.layout_detail.addSpacing(30)
        self.time = []

        self.tabs.addTab(self.main_tab, 'Main')
        self.tabs.addTab(self.detail, 'Detail')

        self.tabs.setStyleSheet("QTabWidget::pane { border: none; background-color: #CCCCCC; }"
                                "QTabBar::tab { background-color: black; color: white; border: 2px solid #AAAAAA; borde"
                                "r-bottom-color: #DDDDDD; border-radius: 4px; padding: 5px; }"
                                "QTabBar::tab:selected { background-color: #FF69B4; border: 2px solid #4CAF50; border-b"
                                "ottom-color: #4CAF50; }")

        # SEKMLERİN KODLARININ SONU
        self.main_layout = QVBoxLayout()  # Ana düzeni dikey olarak ayarla
        self.main_layout.addWidget(self.tabs)

        # Connect butonunu text ve renk ayarlarını yapıyoruz ve tıkladığında connection_to_port fonksiyonuna bağlıyoruz
        self.connect_button = QPushButton(self.connect_text)
        self.connect_button.setStyleSheet("background-color: #800080;")  # Mor rengi
        self.connect_button.clicked.connect(self.connection_to_port)

        self.transferred_data_package = QGroupBox("Transferred Data Package")
        self.transferred_data_layout = QVBoxLayout()
        self.transferred_data_package.setLayout(self.transferred_data_layout)
        self.transferred_data_package.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Output textleri icin QTextEdit adlı widget kullanıyoruz. Bu widget salt okunu hale getiriyoruz. Sadece komut
        # yoluyla input alacak sekilde ayarlıyoruz
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)  # SALT OKUNUR HALE GETİRİYORUZ
        self.transferred_data_layout.addWidget(self.output_text)

        self.vertical_layout = QVBoxLayout()  # Ana düzeni dikey olarak ayarla
        self.vertical_layout.addWidget(self.port_status_frame)
        self.vertical_layout.addLayout(self.main_layout)
        self.layout_of_main.addWidget(self.connect_button)
        self.layout_of_main.addWidget(self.transferred_data_package)

        self.setLayout(self.vertical_layout)
        self.setStyleSheet("background-color: #111111; color: white;")  # Arka plan rengi
        self.showMaximized()

    def label_clicked(self, title, name):
        sender = self.sender()
        QTimer.singleShot(250, sender.reset_effect)  # Reset effect after 500ms

        pencere = GraphWindow(title, name, self)
        pencere.show()
        self.windows[name] = pencere

    def remove_window(self, title):
        if title in self.windows:
            del self.windows[title]

    def refresh_port_name_lists(self):
        # Refresh butonuna tıklandığı zaman buraya gelip en başta ayarladığım python port kontrol komudunu kullanıyor.
        # Eğer yeni bir port girişi olduğunu tespit ederse bunu Port comboboxına ekleme yapıyor.
        self.list_ports = subprocess.check_output(self.command, shell=True).decode('UTF-8').split()
        if not self.list_ports:
            self.list_ports = ["None"]
            self.output_text.append("\nBağlı cihaz bulunamadı !!")
        else:
            self.text_port_name = f"\n{len(self.list_ports)} tane port bulundu: "
            for i in self.list_ports:
                self.text_port_name += f"{i} "
            self.output_text.append(self.text_port_name)
            self.combobox_port.clear()
            self.combobox_port.addItems(self.list_ports)

    def connection_to_port(self):
        # Connection butonuna tıkladığında bu fonksiyona geliyor. Comboboxdaki secilen baudrate ve port ismine göre
        # bağlantı oluşturuyor. Eğer bağlantı başarısız olursa bağlantı kurulamadı hatasını yazıyor.

        self.ser = serial.Serial()
        self.ser.baudrate = self.combobox_baudrate.currentText()
        self.ser.port = self.combobox_port.currentText()
        self.ser.timeout = 0
        logging.basicConfig(level=logging.DEBUG)

        try:  # Bağlantı kurulmadıysa hata verecektir. Eğer hata verirse bağlantı kurulmadıği için text yazacaktır
            self.ser.open()

        except Exception as ex:
            print(ex)
            self.output_text.append(f"\n{self.combobox_port.currentText()} adlı porta bağlantı kurulamadı !!")
            self.combobox_port.clear()
            self.combobox_port.addItems(["None"])

        if self.ser.is_open:
            self.output_text.append(f'\n{self.ser.port} adlı port ile bağlantı kuruldu.')
            self.connection_status_label.setText("Connection Status: Connected!")
            self.all_data = [[] for _ in range(31)]
            self.all_isAlarm = [[False for _ in range(4)] for _ in range(6)]
            self.all_mainisAlarm = [[False for _ in range(4)], [False for _ in range(3)]]
            self.current_second = 0
            self.combobox_baudrate.setEnabled(False)
            self.combobox_port.setEnabled(False)
            self.refresh_button.setEnabled(False)
            self.refresh_button.setStyleSheet("""
                QPushButton {
                    background-color: grey; 
                    border: 1px solid black;
                }
            """)
            self.connect_button.clicked.disconnect(self.connection_to_port)
            self.connect_button.setText("Disconnect")
            self.connect_button.clicked.connect(self.initial_form)

            # Bağlantı kurulduğu anın zaman ve tarih bilgilerini alıp vairable içine atıyoruz. Bu bilgiyi csvApp içinede
            # ki CsvData sınıfına gönderiyoruz bunu da bir variable atıyoruz.
            self.current_date_time = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

            self.csvSave = csvApp.CsvData(self.current_date_time)
            self.sqlSave = sqlApp.SqlData(self.current_date_time)

            # Ayarlanan aralıklar ile connection devam ediyor mu diye kontrol edecek timer ayalarını yapıyoruz.
            self.timerOfdata = QTimer()
            self.timerOfdata.setInterval(500)  # 1000 ms = 1 s
            self.timerOfdata.timeout.connect(self.check_presence)

            # Ayarlanan aralıklar ile data girdisi yapıcak timerın ayarlarını yapıyoruz.
            self.timerOfconnection = QTimer()
            self.timerOfconnection.setInterval(1000)  # 1000 ms = 1 s
            self.timerOfconnection.timeout.connect(self.data_receiver)

            # Timerlara start veriyoruz
            self.timerOfdata.start()
            self.timerOfconnection.start()

    def check_presence(self):
        # Bu fonksiyonda tam çağrıldığı sırada takılı olan portları python komudu ile calıştırıyor. Eğer bağlantı
        # kurduğumuz port ismi bağlı olan portların içinde yoksa bağlantı kesildiğini anlıyoruz ve programı initial
        # forma getiriyoruz.
        # self.list_ports_new = subprocess.check_output(self.command, shell=True).decode('UTF-8').split()
        self.myports = [tuple(p) for p in list(serial.tools.list_ports.comports())]
        try:
            self.list_ports_new = [port for port in self.myports if self.ser.port in port][0]
            if self.ser.port not in self.list_ports_new:
                self.initial_form()
        except Exception as ex:
            print(ex)
            self.list_ports_new = subprocess.check_output(self.command, shell=True).decode('UTF-8').split()
            self.initial_form()

    def data_receiver(self):

        try:
            self.dataNumber = 31  # Gelecek datanın sayısının bir fazlasını yazıyoruz cünkü son index check indexi olup
            # datanın accurate geldiğini kontrol etmek için var

            self.esik_degerleri_list = [[0, 100], [0, 100], [0, 100], [0, 100], [0, 100], [0, 100], [0, 100], [0, 100],
                                        [0, 100], [0, 100],
                                        [0, 100], [0, 100], [0, 100], [0, 100], [0, 100], [0, 100], [0, 100], [0, 100],
                                        [0, 100], [0, 100], [0, 100], [0, 100], [0, 100], [0, 100]]

            self.esik_main_degerler = [[0, 100], [0, 100], [0, 100], [0, 100], [0, 100], [0, 100], [0, 100]]

            # Seri porttan gelen değerleri readline komudu ile okuyoruz. Gelen bilgileri decode ediyoru ve split komudu
            # ile liste haline getiriyoruz . En cok zaman kayıbı olan yer burası!
            self.line = self.ser.readline().decode('windows-1252').replace("\r\n", "").split("*")
            if (len(self.line) != self.dataNumber or "!" != self.line[-1]) and len(self.line) != 1:
                self.line.pop(-1)
                while len(self.line) <= self.dataNumber:
                    self.line.append("--")
            elif self.line == ['']:
                self.line.clear()
                self.line.append("PASS")

            if self.line != ["PASS"]:
                self.data_list = [dict(bir=self.line[0], iki=self.line[1], uc=self.line[2], dort=self.line[3],
                                       bes=self.line[4], altı=self.line[5], yedi=self.line[6], sekiz=self.line[7],
                                       dokuz=self.line[8], on=self.line[9], onbir=self.line[10], oniki=self.line[11],
                                       onuc=self.line[12], ondort=self.line[13], onbes=self.line[14],
                                       onaltı=self.line[15], onyedi=self.line[16], onsekiz=self.line[17],
                                       ondokuz=self.line[18],
                                       yirmi=self.line[19], yirmibir=self.line[20], yirmiki=self.line[21],
                                       yirmiuc=self.line[22],
                                       yirmidort=self.line[23], yirmibes=self.line[24], yirmialtı=self.line[25],
                                       yirmiyedi=self.line[26],
                                       yirmisekiz=self.line[27], yirmidokuz=self.line[28], otuz=self.line[29],
                                       otuzbir=self.line[30])]
                print(self.line)
                self.csvSave.csvdatainput(self.data_list)
                self.sqlSave.sqldatainput(self.data_list)

                self.say = 0
                for a, lab in enumerate(self.inner_labes_values_q):
                    for b, label in enumerate(lab):
                        label_text_new = self.line[self.say]
                        if label_text_new == "--":
                            label.setText(label_text_new)
                        else:
                            try:
                                if int(label_text_new) > self.esik_main_degerler[self.say][1]:
                                    if not self.all_mainisAlarm[a][b]:
                                        self.exclamation_mark([a, b], self.all_mainicon_labels, self.main_labels_lists)
                                    self.all_mainisAlarm[a][b] = True

                                elif int(label_text_new) < self.esik_main_degerler[self.say][1]:
                                    if self.all_mainisAlarm[a][b]:
                                        self.main_labels_lists[a][b].setStyleSheet(
                                            "border: 5px solid white;background-color: #333333; border-width : 1px 1px;"
                                            "font-size : 10pt;qproperty-alignment: 'AlignCenter'; border-radius: 15px;")
                                        self.all_mainicon_labels[a][b].clear()
                                    self.all_mainisAlarm[a][b] = False
                            except Exception as ex:
                                print(ex)
                                self.exclamation_mark([a, b], self.all_mainicon_labels, self.main_labels_lists)
                                self.all_mainisAlarm[a][b] = True
                            label.setText(label_text_new)
                        self.say += 1
                for i in range(6):
                    for a, label in enumerate(self.all_inner_labels_2[i]):
                        label_text_new = self.line[self.say]
                        if self.line[self.say] == "--":
                            label.setText("--")
                        else:
                            try:
                                if int(label_text_new) > self.esik_degerleri_list[self.say - 7][1]:
                                    if not self.all_isAlarm[i][a]:
                                        self.exclamation_mark([i, a], self.all_icon_label,
                                                              self.all_main_labels)
                                    self.all_isAlarm[i][a] = True
                                elif int(label_text_new) < self.esik_degerleri_list[self.say - 7][1]:
                                    if self.all_isAlarm[i][a]:
                                        self.all_main_labels[i][a].setStyleSheet(
                                            "border: 5px solid white;background-color: #333333; border-width : 1px 1px;"
                                            "font-size : 10pt;qproperty-alignment: 'AlignCenter'; border-radius: 15px;")
                                        self.all_icon_label[i][a].clear()
                                    self.all_isAlarm[i][a] = False
                            except Exception as ex:
                                print(ex)
                                self.exclamation_mark([i, a], self.all_icon_label,
                                                      self.all_main_labels)
                                self.all_isAlarm[i][a] = True
                            label.setText(label_text_new)
                        self.say += 1

                self.say = 0
                self.append_text = f"\nBir = {self.line[0]} | Iki = {self.line[1]} | Uc = {self.line[2]} | Dort = " \
                                   f"{self.line[3]} | Bes = {self.line[4]} | Altı = {self.line[5]} | Yedi = " \
                                   f"{self.line[6]} | Sekiz = {self.line[7]} | Dokuz = {self.line[8]} | On = " \
                                   f"{self.line[9]} | Onbir = {self.line[10]}, Oniki = {self.line[11]} | Onuc = " \
                                   f"{self.line[12]} | Ondort = {self.line[13]} | Onbes = {self.line[14]} | Onaltı = " \
                                   f"{self.line[15]} | Onyedi = {self.line[16]} | Onsekiz = {self.line[17]}, Ondokuz " \
                                   f"= {self.line[18]} | Yirmi = {self.line[19]} |Yirmibir = {self.line[20]} | " \
                                   f"Yirmiki = {self.line[21]} | Yirmiuc = {self.line[22]} | Yirmidort =" \
                                   f" {self.line[23]} |Yirmibes = {self.line[24]} | Yirmialtı = {self.line[25]}," \
                                   f" Yirmiyedi = {self.line[26]} | Yirmisekiz = {self.line[27]} |" \
                                   f"Yirmidokuz = {self.line[28]} | Otuz = {self.line[29]} | Otuzbir = {self.line[30]} "
                self.output_text.append(self.append_text)

                self.time.append(self.current_second)
                for index, data in enumerate(self.line):
                    if index != 31:
                        if "" == data or "--" == data:
                            self.all_data[index].append(0)
                        elif "" != data or "--" != data:
                            self.all_data[index].append(int(data))
                if self.windows:
                    for dict_key in self.windows.keys():
                        self.say = 0
                        for _ in self.inner_labes_names_lists:
                            for name in _:
                                if dict_key == name:
                                    self.windows.get(name).update_graph(self.time, self.all_data[self.say])
                                self.say = self.say + 1
                        for _ in self.inner_labels_names:
                            for name in _:
                                if dict_key == name:
                                    self.windows.get(name).update_graph(self.time, self.all_data[self.say])
                                self.say = self.say + 1
                self.current_second += 1
                self.say = 0

        except Exception as error:  # Eğer hata verilse hatanın türüne göre text yazıyor ve inital forma alıyor.
            if "invalid continuation byte" in str(error) and "list index out of range" in str(error):
                self.output_text.append("\nYANLIS BAUDRATE!")
            print(error)
            print(traceback.format_exc())
            self.initial_form()

    def exclamation_mark(self, sequence, icon_label, ana_label):
        self.sequence = sequence
        self.icon_label = icon_label
        self.ana_label = ana_label

        self.ana_label[self.sequence[0]][self.sequence[1]].setStyleSheet(
            "border: 5px solid red;background-color: #333333; border-width : 1px 1px; font-size : 10pt; "
            "qproperty-alignment: 'AlignCenter'; border-radius: 15px;")
        self.icon_pixmap = QPixmap(r'icon/unlem.png')
        self.icon_label[self.sequence[0]][self.sequence[1]].setPixmap(self.icon_pixmap)
        self.icon_label[self.sequence[0]][self.sequence[1]].setStyleSheet("border : none;")

    # BUTUN TIMERLARI VE PORT BAGLANTISINI KESIYOR ARAYUZU DEFAULT HALE GETİRİYOR
    def initial_form(self):
        self.ser.close()
        self.timerOfconnection.stop()
        self.timerOfdata.stop()
        self.timerOfconnection.stop()
        self.all_isAlarm = []
        self.all_mainisAlarm = []
        self.combobox_baudrate.setEnabled(True)
        self.combobox_port.setEnabled(True)
        self.all_data.clear()
        self.time.clear()
        self.current_second = 0
        self.sqlSave.connection_close()
        self.refresh_button.setEnabled(True)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #800080; 
                border: 1px solid black;
            }
            QPushButton:hover {
                background-color: grey;
            }
        """)
        self.disconnect_ports = subprocess.check_output(self.command, shell=True).decode('UTF-8').split()

        self.connect_button.setText("Connect")
        self.connect_button.clicked.disconnect(self.initial_form)
        self.connect_button.clicked.connect(self.connection_to_port)
        self.combobox_port.clear()
        if not self.list_ports_new:
            self.combobox_port.addItems(["None"])
        else:
            print(self.disconnect_ports)
            self.combobox_port.addItems(self.disconnect_ports)

        self.connection_status_label.setText("Connection Status : Connection Lost!")

        self.output_text.append("\nCihaz ile bağlantı kesildi!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
