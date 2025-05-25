# main.py

import sys
from PyQt6.QtWidgets import QApplication
from gui import WelcomeScreen

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for better look
    
    # Show welcome screen
    welcome = WelcomeScreen()
    welcome.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
