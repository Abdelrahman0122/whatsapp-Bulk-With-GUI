from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QWidget,
    QTextEdit,
    QLineEdit,
)
from PyQt5.QtCore import QThread, pyqtSignal
import time
import sys

class SeleniumThread(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, country_code, message, numbers, image_path=None):
        super().__init__()
        self.country_code = country_code
        self.message = message
        self.numbers = numbers
        self.image_path = image_path

    def is_valid_number(self, num):
        return len(num) == 11 and num.startswith("01")

    def run(self):
        try:
            service = Service()
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--disable-popup-blocking')
            driver = webdriver.Chrome(service=service, options=chrome_options)

            self.update_signal.emit(f"Sending messages with image: {self.image_path}")

            login_time = 60
            action_time = 3
            image_path = self.image_path

            # Open browser with default link
            link = 'https://web.whatsapp.com'
            driver.get(link)
            wait = WebDriverWait(driver, login_time)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, '_3WByx')))
           # print("logged in")

            # Loop Through Numbers List
            for num in self.numbers.split('\n'):
                num = num.rstrip()
                if not num or not self.is_valid_number(num):
                    print(f"Skipping invalid number: {num}")
                    continue  # Skip empty lines or invalid numbers

                link = f'https://web.whatsapp.com/send/?phone={self.country_code}{num}'
                driver.get(link)
                #print(f"Opened the chat for number: {num}")
                time.sleep(2)
                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, '_3E8Fg')))
                   # print("Found the chatbox")
                    driver.execute_script("document.querySelector('div._3Uu1_').focus();")
                    time.sleep(2)
                   # print("Focused on the chatbox")

                    elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'CzM4m')))
                    
                    if image_path:
                       # print("Inside the image path")
                        attach_btn = driver.find_element(By.CSS_SELECTOR, '._1OT67')
                        attach_btn.click()
                        time.sleep(action_time)

                        # Find and send image path to input
                        msg_input = None
                        while msg_input is None:
                            try:
                                msg_input = driver.find_elements(By.CSS_SELECTOR, '._2UNQo input')[1]
                            except IndexError:
                                pass
                            time.sleep(1)

                        msg_input.send_keys(image_path)
                        time.sleep(action_time)

                    actions = ActionChains(driver)
                    for line in self.message.split('\n'):
                        actions.send_keys(line)
                        actions.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT)
                    actions.send_keys(Keys.ENTER)
                    actions.perform()

                   #print("Pressed enter and now checking")

                    time.sleep(1)

                except Exception as e:
                    print(f"Error in processing chat for number {num}: {e}")

        finally:
            driver.quit()
            self.finished.emit()

class WhatsAppMessengerGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.country_code = ""
        self.message = ""
        self.numbers = ""
        self.image_path = ""

        self.setWindowTitle("WhatsApp Messenger")

        central_widget = self.setup_gui()

        self.selenium_thread = SeleniumThread(self.country_code, self.message, self.numbers, self.image_path)
        self.selenium_thread.update_signal.connect(self.update_status)
        self.selenium_thread.finished.connect(self.selenium_thread.deleteLater)

        central_widget.setLayout(self.layout)

    def setup_gui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.layout = QVBoxLayout()

        self.label_country_code = QLabel("Enter Country Code:", self)
        self.layout.addWidget(self.label_country_code)

        self.line_edit_country_code = QLineEdit(self)
        self.layout.addWidget(self.line_edit_country_code)

        self.label_message = QLabel("Type your message:", self)
        self.layout.addWidget(self.label_message)

        self.text_edit_message = QTextEdit(self)
        self.layout.addWidget(self.text_edit_message)

        self.label_numbers = QLabel("Type numbers (one per line):", self)
        self.layout.addWidget(self.label_numbers)

        self.text_edit_numbers = QTextEdit(self)
        self.layout.addWidget(self.text_edit_numbers)

        self.label_image = QLabel("Select Image:", self)
        self.layout.addWidget(self.label_image)

        self.image_button = QPushButton("Browse", self)
        self.image_button.clicked.connect(self.browse_image)
        self.layout.addWidget(self.image_button)

        self.send_button = QPushButton("Send Messages", self)
        self.send_button.clicked.connect(self.start_selenium_thread)
        self.layout.addWidget(self.send_button)

        return central_widget

    def browse_image(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_dialog = QFileDialog()
        file_dialog.setOptions(options)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg)")

        if file_dialog.exec_():
            self.image_path = file_dialog.selectedFiles()[0]
            self.label_image.setText(f"Selected Image: {self.image_path}")

    def start_selenium_thread(self):
        self.country_code = self.line_edit_country_code.text()
        self.message = self.text_edit_message.toPlainText()
        self.numbers = self.text_edit_numbers.toPlainText()
        if self.image_path:
            self.selenium_thread = SeleniumThread(self.country_code, self.message, self.numbers, self.image_path)
        else:
            self.selenium_thread = SeleniumThread(self.country_code, self.message, self.numbers)

        self.selenium_thread.start()

    def update_status(self, status):
        print(status)

def main():
    app = QApplication(sys.argv)
    main_window = WhatsAppMessengerGUI()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


