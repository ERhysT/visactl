import sys, os

os.environ["QT_LOGGING_RULES"] = "qt.dbus.integration=false"

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import (
    QWidget, QLabel, QApplication, QMainWindow, QPushButton,
    QTabWidget, QGridLayout, QGroupBox, QComboBox, QLineEdit,
    QPushButton, QTableWidget, QVBoxLayout, QDialog, QFileDialog,
    QCheckBox
)

WINDOW_TITLE = "VISA device controller"

class Color(QWidget):
    """An empty, coloured placehoder widget for debugging"""
    def __init__(self, color):
        super(Color, self).__init__()

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)

class ConnectionsPage(QWidget):
    """The page to control device and data connections"""

    def __init__(self):
        super().__init__()
        
        self.layout = QGridLayout(self)

        self.layout.addWidget(VisaConnectionBox())
        self.layout.addWidget(SqlConnectionBox())
        self.layout.addWidget(LocalConnectionBox())
        
class ConnectionBox(QGroupBox):
    """Group box for connections with a grid layout"""
    def __init__(self, title):
        super().__init__(title)
        
        self.layout = QGridLayout(self)

class VisaConnectionBox(ConnectionBox):
    """VISA connection settings box"""

    signalVisaSettingsChanged = pyqtSignal(str)

    def __init__(self):
        super().__init__("VISA device connection")
        self._layout()
        self.connect()

    def _layout(self):
        ## Connection status
        self.lab_status = QLabel("Connection status:")
        self.lab_status_q = QLabel("Disconnected")

        self.layout.addWidget(self.lab_status, 0, 0)
        self.layout.addWidget(self.lab_status_q, 0, 1)

        ## Drop down for device
        self.lab_device = QLabel("Device:")
        self.dd_device = QComboBox()

        self.layout.addWidget(self.lab_device, 1, 0)
        self.layout.addWidget(self.dd_device, 1, 1)

    def connect(self):
        self.dd_device.currentTextChanged.connect(self.onVisaSettingsChanged)

    def onVisaSettingsChanged(self, device):
        """Emit signalDeviceChanged signal

        Provides device name string.
        """
        self.signalVisaSettingsChanged.emit(device)

class SqlConnectionBox(ConnectionBox):
    """SQL connection settings box"""

    signalSqlSettingsChanged = pyqtSignal(dict) # sql settings changed
    
    def __init__(self):
        super().__init__("SQL server connection")
        self._layout()
        self.connect()

    def _layout(self):
        ## Connection status
        self.lab_status = QLabel("Enable logging:")
        self.checkbox_status = QCheckBox()

        self.layout.addWidget(self.lab_status, 0, 0)
        self.layout.addWidget(self.checkbox_status, 0, 1)

        ## select the server address
        self.lab_server = QLabel("Server:")
        self.line_server = QLineEdit()

        self.layout.addWidget(self.lab_server, 1, 0)
        self.layout.addWidget(self.line_server, 1, 1)

        ## select the database
        self.lab_database = QLabel("Database:")
        self.line_database = QLineEdit()

        self.layout.addWidget(self.lab_database, 2, 0)
        self.layout.addWidget(self.line_database, 2, 1)

        ## select the table
        self.lab_table = QLabel("Table:")
        self.line_table = QLineEdit()

        self.layout.addWidget(self.lab_table, 3, 0)
        self.layout.addWidget(self.line_table, 3, 1)

    def settings(self):
        """Return a dictionary of the current sql settings"""
        return {
            "enabled": self.checkbox_status.checkState(),
            "server": self.line_server.text(),
            "database": self.line_database.text(),
            "table": self.line_table.text(),
        }

    def connect(self):
        self.checkbox_status.stateChanged.connect(self.onSqlSettingsChanged)
        self.line_server.editingFinished.connect(self.onSqlSettingsChanged)
        self.line_database.editingFinished.connect(self.onSqlSettingsChanged)
        self.line_table.editingFinished.connect(self.onSqlSettingsChanged)
            
    def onSqlSettingsChanged(self):
        """ Emit signalSqlSettings changed

        Provides a dictionary of the current settings.
        """
        self.signalSqlSettingsChanged.emit(self.settings())

class LocalConnectionBox(ConnectionBox):
    """Local settings connection box"""

    signalLocalSettingsChanged = pyqtSignal(str)

    def __init__(self):
        super().__init__("Local settings")
        self._layout()
        self.connect()
    
    def _layout(self):
        ## state file
        self.lab_statefile = QLabel("State file:")
        self.button_statefile = QPushButton("Browse...")
        self.line_statefile = QLineEdit()

        self.layout.addWidget(self.lab_statefile, 0, 0)
        self.layout.addWidget(self.button_statefile, 0, 2)
        self.layout.addWidget(self.line_statefile, 0, 1)

        ## backup directory
        self.lab_dir = QLabel("Fallback directory:")
        self.button_dir = QPushButton("Browse...")
        self.line_dir = QLineEdit()

        self.layout.addWidget(self.lab_dir, 1, 0)
        self.layout.addWidget(self.button_dir, 1, 2)
        self.layout.addWidget(self.line_dir, 1, 1)

    def connect(self):
        self.button_statefile.clicked.connect(self.onStatefileButtonClicked)
        self.button_dir.clicked.connect(self.onDirectoryButtonClicked)
        self.line_dir.editingFinished.connect(self.onLocalSettingsChanged)

    def onLocalSettingsChanged(self):
        self.signalLocalSettingsChanged.emit(self.line_dir.text())
        
    def onDirectoryButtonClicked(self):
        """Select folder interactively"""
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        self.line_dir.setText(folder)

    def onStatefileButtonClicked(self):
        """Select statefile interactively"""
        file_name = QFileDialog.getOpenFileName(self, "Select statefile")[0]
        self.line_statefile.setText(file_name)

class StatefilePage(QWidget):
    """The page to control scan route"""
    def __init__(self):
        super().__init__()
        
        self.layout = QVBoxLayout(self)

        self.box_source = StatefileSourceBox()
        self.table_statefile = StatefileTable()

        self.layout.addWidget(self.box_source)
        self.layout.addWidget(self.table_statefile)

class StatefileTable(QGroupBox):
    """Display and edit the device state"""
    def __init__(self):
        super().__init__("Scan Route")

        self.layout = QVBoxLayout(self)
        
        self.table = QTableWidget(0, 4)
        headers = [ "Description", "Units", "Scan", "Configure" ]
        self.table.setHorizontalHeaderLabels(headers)

        self.layout.addWidget(self.table)

class StatefileSourceBox(ConnectionBox):
    """State file settings"""
    def __init__(self):
        super().__init__("State file settings")

        self.lab_src = QLabel("State file source:")
        self.dd_src = QComboBox()
        self.button_src_reload = QPushButton("Reload")
        
        self.layout.addWidget(self.lab_src, 0, 0)
        self.layout.addWidget(self.dd_src, 0, 1)
        self.layout.addWidget(self.button_src_reload, 0, 2)

class AquisitionPage(QWidget):
    """The page to start and stop aquisition"""
    def __init__(self):
        super().__init__()
        
        self.layout = QVBoxLayout(self)
        self.button_nextrun = QPushButton("Guess meta data")
        self.button_load = QPushButton("Set load")
        self.button_start = QPushButton("Start")
        self.box_metadata = MetadataBox()

        self.layout.addWidget(self.button_nextrun)
        self.layout.addWidget(self.button_load)
        self.layout.addWidget(self.button_start)
        self.layout.addWidget(self.box_metadata)
        
class MetadataBox(QGroupBox):
    """Box for entering metadata"""
    def __init__(self):
        super().__init__("Metadata")

        self.layout = QGridLayout(self)

        self.label_part = QLabel("Part number")
        self.line_part = QLineEdit()

        self.label_number = QLabel("Run number")
        self.line_number = QLineEdit()

        self.layout.addWidget(self.label_part, 0, 0)
        self.layout.addWidget(self.line_part, 0, 1)
        self.layout.addWidget(self.label_number, 1, 0)
        self.layout.addWidget(self.line_number, 1, 1)

class TabWidget(QTabWidget):
    """Fixed navigation tabs"""
    def __init__(self):
        super().__init__()

        # Create fixed tab bar at the top
        self.setTabPosition(QTabWidget.TabPosition.North)
        self.setMovable(False)

        # create each page
        self.page_connections = ConnectionsPage()
        self.page_statefile = StatefilePage()
        self.page_aquisition = AquisitionPage()

        # add each page as a tab 
        self.addTab(self.page_connections, "Connections")
        self.addTab(self.page_statefile, "Route")
        self.addTab(self.page_aquisition, "Aquisition")

class ConfigurePopup(QDialog):
    """A popup modal window to configure the device"""
    def __init__(self, parent):
        super().__init__(parent)
        
    
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(WINDOW_TITLE)

        self._layout()
        self.connect()

        # Set the central widget of the Window.
        self.setCentralWidget(self.tabs)

    def _layout(self):
        """Define layout of all widgets"""
        self.tabs = TabWidget()

    def connect(self):
        """Connect signals to slots"""
        pass
    
app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
