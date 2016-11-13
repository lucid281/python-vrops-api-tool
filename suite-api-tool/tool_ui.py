import sys
from os.path import isfile
from client import Client
from resource_table import ResourceTable
from resource_details import ResourceDetails
from PyQt5.QtWidgets import *
from PyQt5 import QtCore

class ToolUI(QMainWindow):

    def __init__(self, clipboard):
        super().__init__()
        self.resize(800,600)
        self.clipboard = clipboard
        self.__address_bar = QLineEdit()
        self.__adapter_type_combobox = QComboBox
        self.__adapter_instance_combobox = QComboBox
        self.__connect_button = QPushButton
        self.__resource_table = ResourceTable()
        self.__resource_table.doubleClicked.connect(self.getResourceDetails)
        self.__client = None
        self.initUI()

    def initUI(self):
        self.__main_widget = QWidget()
        self.__main_widget.setLayout(self.__createMainLayout())
        self.setCentralWidget(self.__main_widget)
        self.__assignClickActions()
        self.show()

    def __createMainLayout(self):
        vbox = QVBoxLayout()
        vbox.addLayout(self.__createAddressBar())
        vbox.addLayout(self.__createAdapterKindSelector())
        vbox.addLayout(self.__createResourceKindSelector())
        vbox.addLayout(self.__createAdapterInstanceSelector())
        vbox.addWidget(self.__resource_table)
        return vbox

    def __createAddressBar(self):
        address_bar_layout = QHBoxLayout()
        address_bar_label = QLabel()
        address_bar_label.setText("Hostname:")
        self.__address_bar = QLineEdit()
        self.__address_bar.setCompleter(QCompleter(self.__getCompleterListFromFile()))
        self.__connect_button = QPushButton()
        self.__connect_button.setText("Connect!")
        address_bar_layout.addWidget(address_bar_label)
        address_bar_layout.addWidget(self.__address_bar)
        address_bar_layout.addWidget(self.__connect_button)
        return address_bar_layout

    def __getCompleterListFromFile(self):
        if not isfile("completion_list"):
            return list()
        with open("completion_list", "r+") as f:
            lines = f.read().splitlines()
        return lines

    def __createAdapterKindSelector(self):
        adapter_kind_selector_layout = QHBoxLayout()
        label = QLabel("Adapter Type: ")
        self.__adapter_type_combobox = QComboBox()
        self.__adapter_type_combobox.setFixedSize(500,25)
        self.__adapter_type_combobox.activated.connect(self.__adapterKindComboBoxSelection)
        adapter_kind_selector_layout.addWidget(label)
        adapter_kind_selector_layout.addWidget(self.__adapter_type_combobox)
        return adapter_kind_selector_layout

    def __createResourceKindSelector(self):
        resource_kind_selector_layout = QHBoxLayout()
        label = QLabel("Resource Kind: ")
        self.__resource_kind_combobox = QComboBox()
        self.__resource_kind_combobox.setFixedSize(500,25)
        resource_kind_selector_layout.addWidget(label)
        resource_kind_selector_layout.addWidget(self.__resource_kind_combobox)
        return resource_kind_selector_layout

    def __createAdapterInstanceSelector(self):
        adapter_instance_selector_layout = QHBoxLayout()
        label = QLabel("Adapter Instance: ")
        self.__adapter_instance_combobox = QComboBox()
        self.__adapter_instance_combobox.setFixedSize(500,25)
        self.__adapter_instance_combobox.activated.connect(self.__adapterInstanceComboBoxSelection)
        adapter_instance_selector_layout.addWidget(label)
        adapter_instance_selector_layout.addWidget(self.__adapter_instance_combobox)
        return adapter_instance_selector_layout

    def __assignClickActions(self):
        self.__connect_button.clicked.connect(self.__connectClicked)

    def __connectClicked(self):
        try:
            self.__client = Client(self.__address_bar.text())
        except ValueError as error:
            QMessageBox.warning(self.__main_widget, "Warning", str(error), QMessageBox.Ok)
            return
        try:
            items = self.__client.getAdapterKinds()
            self.__addItemsToAdapterKinds(items)
            self.__addItemToCompletionList(self.__address_bar.text())
            self.__address_bar.setCompleter(QCompleter(self.__getCompleterListFromFile()))
        except Exception as error:
            QMessageBox.warning(self.__main_widget, "Warning", str(error), QMessageBox.Ok)

    def __addItemsToAdapterKinds(self, items):
        self.__adapter_type_combobox.clear()
        for item in items:
            self.__adapter_type_combobox.addItem(item[0], item[1])

    def __addItemToCompletionList(self, item):
        with open("completion_list", 'a+') as file:
            file.write(item+"\n")

    def __adapterKindComboBoxSelection(self):
        adapter_kind = self.__adapter_type_combobox.currentData()
        adapter_instances = self.__client.getAdapterInstances(adapter_kind)
        resource_kinds = self.__client.getResourceKindsByAdapterKind(adapter_kind)
        self.__addItemsToAdapterInstances(adapter_instances)
        self.__addItemsToResourceKinds(resource_kinds)

    def __addItemsToAdapterInstances(self, items):
        self.__adapter_instance_combobox.clear()
        for item in items:
            self.__adapter_instance_combobox.addItem(item[0], item[1])

    def __adapterInstanceComboBoxSelection(self):
        adapter_instance_id = self.__adapter_instance_combobox.currentData()
        resource_kind_id = self.__resource_kind_combobox.currentData()
        resources = self.__client.getResources(adapter_instance_id, resource_kind_id)
        self.__createResourceTable(resources)

    def __addItemsToResourceKinds(self, resource_kinds):
        self.__resource_kind_combobox.clear()
        for resource_kind in resource_kinds:
            self.__resource_kind_combobox.addItem(resource_kind[0], resource_kind[1])

    def __createResourceTable(self, resources):
        self.__resource_table.setColumnCount(0)
        self.__resource_table.setRowCount(0)
        self.__resource_table.reInit()
        self.__resource_table.addResources(resources)

    def keyPressEvent(self, key_event):
        if key_event.key() == QtCore.Qt.Key_C and key_event.modifiers().__eq__(QtCore.Qt.ControlModifier):
            self.copySelectedCellsToClipboard()

    def getResourceDetails(self):
        selected_items = self.__resource_table.selectedItems()
        all_same = all(e.row() == selected_items[0].row() for e in selected_items)
        if not all_same:
            QMessageBox.warning(self.__main_widget, "Warning", "Please only select one row.", QMessageBox.Ok)
            return
        # get uuid of row
        resource_id = None
        resource_name = None
        for item in self.__resource_table.selectedItems():
            if item.column() == 0:
                resource_name = item.text()
            if item.column() == 1:
                resource_id = item.text()
        if resource_id is None or resource_name is None:
            QMessageBox.warning(self.__main_widget, "Warning", "Could not find one or both of Name or UUID of resource selected.", QMessageBox.Ok)
            return
        metrics = self.__client.getMetricsByResourceUUID(resource_id)
        properties = self.__client.getPropertiesByResourceUUID(resource_id)
        resource_details = ResourceDetails(self, metrics, properties)
        resource_details.setWindowTitle(resource_name)
        resource_details.setWindowFlags(QtCore.Qt.Window)
        resource_details.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        resource_details.resize(600, 800)
        resource_details.show()

    def copySelectedCellsToClipboard(self):
        if len(self.__resource_table.selectedItems()) > 0:
            print("selected things on the table!!!")
            strings = list()
            row = list()
            last_row = None
            got_columns = False
            columns = list()
            for item in self.__resource_table.selectedItems():
                current_row = item.row()
                if(last_row is not None and last_row < current_row):
                    if(not got_columns):
                        strings.append('\t'.join(columns))
                        strings.append('\n')
                        got_columns = True
                    strings.append('\t'.join(row))
                    strings.append('\n')
                    row.clear()
                if(not got_columns):
                    str(self.__resource_table.horizontalHeaderItem(item.column()))
                    columns.append(str(self.__resource_table.horizontalHeaderItem(item.column()).text()))
                row.append(str(item.text()))
                last_row = item.row()
            self.clipboard.setText(''.join(strings))

if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = ToolUI(app.clipboard())
    sys.exit(app.exec_())