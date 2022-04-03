import pathlib
import tkinter as tk
import tkinter.ttk as ttk
from pygubu.widgets.tkscrolledframe import TkScrolledFrame
import json
import cv2
import pytesseract
from selenium.webdriver.common import keys
from selenium import webdriver
import sqlite3
import time
import datetime
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
import warnings
import numpy as np
import pyautogui
from threading import Thread
import csv
from csv import writer
from os.path import exists

warnings.filterwarnings('ignore')


class ScreenRecord:
    filename = str(datetime.datetime.now().isoformat(timespec='minutes')).replace(':', '-')
    SCREEN_SIZE = tuple(pyautogui.size())
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    fps = 30
    # out = cv2.VideoWriter('records/' + filename + ".mp4", fourcc, fps, (640, 480))  # (SCREEN_SIZE)
    stop = False

    def statrRecord(self):
        out = cv2.VideoWriter('records/' + self.filename + ".mp4", self.fourcc, self.fps,
                              (self.SCREEN_SIZE))  # (SCREEN_SIZE)
        i = 1
        while True:
            i = i + 1
            if self.stop == True:
                cv2.destroyAllWindows()
                break
            elif self.stop == 'pause':
                continue
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            out.write(frame)
        out.release()
        # print("endrecording")


def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if (gm > 2):
        gy2 = gy + 1
    else:
        gy2 = gy
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if (days > 365):
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if (days < 186):
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return [jy, jm, jd]


def jalali_to_gregorian(jy, jm, jd):
    jy += 1595
    days = -355668 + (365 * jy) + ((jy // 33) * 8) + (((jy % 33) + 3) // 4) + jd
    if (jm < 7):
        days += (jm - 1) * 31
    else:
        days += ((jm - 7) * 30) + 186
    gy = 400 * (days // 146097)
    days %= 146097
    if (days > 36524):
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if (days >= 365):
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if (days > 365):
        gy += ((days - 1) // 365)
        days = (days - 1) % 365
    gd = days + 1
    if ((gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)):
        kab = 29
    else:
        kab = 28
    sal_a = [0, 31, kab, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    while (gm < 13 and gd > sal_a[gm]):
        gd -= sal_a[gm]
        gm += 1
    return [gy, gm, gd]


# security_captcha to text
def imagetostr(imagepath):
    path_exists1 = exists(r'C:\Program Files\Tesseract-OCR\tesseract.exe')
    path_exists2 = exists(r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe')

    if path_exists1:
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    elif path_exists2:
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
    else:
        print('plz install tesseract !!!')
    img = cv2.imread(imagepath)
    ret, img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)
    text = pytesseract.image_to_string(img).replace("\n", "").replace(' ', '''!()-[]{};:'"\,<>./?@#$%^&*_~''')
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
    no_punct = ""
    for char in text:
        if char not in punctuations:
            no_punct = no_punct + char
    return no_punct


# find img
def find_ca_im(driver):
    # get captcha image
    security_captcha_imgs = driver.find_elements_by_tag_name('img')
    for item in security_captcha_imgs:
        htmlout = item.get_attribute("outerHTML")
        captchalist = ["capcha", "captcha", "security", "security_captcha", "securitycaptcha"]
        if len([ii for ii in captchalist if ii in htmlout]) >= 1:
            security_captcha_img = item
            actions = ActionChains(driver)
            actions.move_to_element(security_captcha_img)
            actions.perform()
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    with open('data/security_captcha.png', 'wb') as file:
        file.write(security_captcha_img.screenshot_as_png)
    ckeys = imagetostr('data/security_captcha.png')
    return ckeys


# popup - splash-view
def rm_popup(driver):
    try:
        splash_container = driver.find_element_by_class_name('splash-close-button')
        splash_container.click()
    except:
        pass
    try:
        buttons = driver.find_elements_by_tag_name("button")
        for i in buttons:
            htmlout = i.get_attribute("outerHTML")
            if "ادامه" in htmlout:
                i.click()
    except:
        pass

    try:
        buttons = driver.find_elements_by_tag_name("button")
        for i in buttons:
            htmlout = i.get_attribute("outerHTML")
            if "بستن" in htmlout:
                i.click()
    except:
        pass


# singup
def singupform(driver, mobile_num, email, username, password):
    try:
        Mobile_num_label = driver.find_element_by_xpath("//*[text()='شماره تلفن همراه']/..")
        Mobile_num = Mobile_num_label.find_element_by_tag_name("input")
        data_format = Mobile_num.get_attribute('data-format')
        if mobile_num[0] == '0':
            mobile_num = mobile_num.replace("0", "", 1)
        if data_format == '++(+++)+++++++':
            mobile_num = '98' + mobile_num
        Mobile_num.clear()
        Mobile_num.click()
        Mobile_num.send_keys(mobile_num)
    except:
        pass

    #     try:
    #         Terms = driver.find_element_by_id('terms')
    #         Terms.click()
    #     except:
    #         pass

    try:
        Email_label = driver.find_element_by_xpath("//*[text()='ایمیل']/..")
        Email = Email_label.find_element_by_tag_name("input")
        Email.clear()
        Email.send_keys(email)
    except:
        pass

    try:
        Usename_label = driver.find_element_by_xpath("//*[text()='نام کاربری']/..")
        Usename = Usename_label.find_element_by_tag_name("input")
        Usename.clear()
        Usename.send_keys(username)
    except:
        pass

    try:
        Fname_label = driver.find_element_by_xpath("//*[text()='نام و نام خانوادگی']/..")
        Fname = Fname_label.find_element_by_tag_name("input")
        Fname.clear()
        Fname.send_keys(username)
    except:
        pass

    try:
        Password_label = driver.find_element_by_xpath("//*[text()='رمز عبور']/..")
        Password = Password_label.find_element_by_tag_name("input")
        Password.clear()
        Password.send_keys(password)
    except:
        pass

    try:
        Confirm_password_label = driver.find_element_by_xpath("//*[text()='تکرار رمز عبور']/..")
        Confirm_password = Confirm_password_label.find_element_by_tag_name("input")
        Confirm_password.clear()
        Confirm_password.send_keys(password)
    except:
        pass

    try:
        Captcha_label = driver.find_element_by_xpath("//*[text()='کد امنیتی']/..")
        Captcha = Captcha_label.find_element_by_tag_name("input")
        cod = find_ca_im(driver)
        Captcha.clear()
        Captcha.send_keys(cod)
    #         Captcha.send_keys(keys.Keys.ENTER)
    except:
        pass


def singup(address, driver, mobile_num, email, username, password):
    con = sqlite3.connect('data/db.sqlite3')
    cur = con.cursor()
    rm_popup(driver)
    singupurl = driver.find_element_by_xpath("//*[text()='ثبت نام']").get_attribute("href")
    driver.get(singupurl)
    c_url = driver.current_url
    issing = 1
    while (c_url == driver.current_url) and issing:
        rm_popup(driver)
        singupform(driver, mobile_num, email, username, password)
        #         time.sleep(3)
        buttons = driver.find_elements_by_tag_name("a")
        for button in buttons:
            btntxt = button.get_attribute('outerHTML')
            if btntxt.find("ثبت نام") >= 0 and btntxt.find('form-button') >= 0:
                button.click()
                time.sleep(2)
        singup_stoplist = ['ایمیل شما قبلا', 'نام کاربری (ایمیل) موجود می باشد']
        body = driver.find_element_by_tag_name('body').get_attribute('outerHTML')
        for item in singup_stoplist:
            issing = body.find(item)
            if issing > 0:
                cur.execute("update betscan_website set singin = 1 where address = '{}' ".format(address))
                con.commit()
                issing = 0
                break

    rm_popup(driver)
    if issing == 0:
        singin(driver, mobile_num, email, username, password)


def singin(driver, mobile_num, email, username, password):
    rm_popup(driver)
    a_urls = driver.find_elements_by_tag_name('a')
    for item in a_urls:
        try:
            item_txt = item.get_attribute('outerHTML')
            if item_txt.find('ورود') >= 0:
                driver.get(item.get_attribute('href'))
        except:
            pass
    c_url = driver.current_url
    while c_url == driver.current_url:
        singupform(driver, mobile_num, email, username, password)
        time.sleep(3)
        driver.find_element_by_tag_name('input').send_keys(keys.Keys.ENTER)

    rm_popup(driver)


time_driver = None
driver = None

# PROJECT_PATH = pathlib.Path(__file__).parent
# PROJECT_UI = PROJECT_PATH / "gui.ui"


class GuiApp:
    website_url = None
    group = 'A'
    address = None
    creat_at = datetime.datetime.now()
    username = 'userbet'
    fname = 'jamshidibet'
    password = 'Pass123456'
    mobile_num = None
    email = "alirezabet72_gmail@gmail.com"
    Payment_gateway = ""
    title = ""
    # cart
    cart_id = None
    cart_pass2 = None
    cart_cvv2 = None
    cart_month = None
    cart_year = None
    banckuser = None
    banckpass = None


    def __init__(self, master=None):
        # build ui
        self.main = tk.Frame(master)
        self.tkscrolledframe3 = TkScrolledFrame(self.main, scrolltype='both')
        self.informationFrame = tk.LabelFrame(self.tkscrolledframe3.innerframe)
        self.cartFrame = tk.LabelFrame(self.informationFrame)
        self.cart_idFrame = tk.Frame(self.cartFrame)
        self.cart_id_label = tk.Label(self.cart_idFrame)
        self.cart_id_label.configure(background='#ffffff', text=':  شماره کارت')
        self.cart_id_label.grid(column='2', row='1')
        self.cart_id = ttk.Entry(self.cart_idFrame)
        self.cart_id.configure(justify='center')
        self.cart_id.grid(column='0', row='1')
        self.cart_idFrame.grid(column='0', row='0')
        self.cart_cvv2_frame = tk.Frame(self.cartFrame)
        self.label4 = tk.Label(self.cart_cvv2_frame)
        self.label4.configure(background='#ffffff', font='TkDefaultFont', text=':  cvv2')
        self.label4.grid(column='2', row='1')
        self.cart_cvv2 = tk.Entry(self.cart_cvv2_frame)
        self.cart_cvv2.configure(cursor='arrow', justify='center', state='normal', width='6')
        self.cart_cvv2.grid(column='0', row='1')
        self.cart_cvv2_frame.grid(column='0', row='1')
        self.frame10 = tk.Frame(self.cartFrame)
        self.label5 = tk.Label(self.frame10)
        self.label5.configure(background='#ffffff', font='TkDefaultFont', text=':  پسورد دوم کارت')
        self.label5.grid(column='2', row='1')
        self.cart_pass2 = tk.Entry(self.frame10)
        self.cart_pass2.configure(cursor='arrow', justify='center', state='normal')
        self.cart_pass2.grid(column='0', row='1')
        self.frame10.grid(column='0', row='2')
        self.frame11 = tk.Frame(self.cartFrame)
        self.label6 = tk.Label(self.frame11)
        self.label6.configure(background='#ffffff', font='TkDefaultFont', text=':  ماه')
        self.label6.grid(column='2', row='1')
        self.cart_month = tk.Entry(self.frame11)
        self.cart_month.configure(cursor='arrow', justify='center', state='normal', width='5')
        self.cart_month.grid(column='1', row='1')
        self.label7 = tk.Label(self.frame11)
        self.label7.configure(background='#ffffff', font='TkDefaultFont', text=':  سال')
        self.label7.grid(column='4', row='1')
        self.cart_year = tk.Entry(self.frame11)
        self.cart_year.configure(cursor='arrow', justify='center', state='normal', width='6')
        self.cart_year.grid(column='3', row='1')
        self.frame11.grid(column='0', row='3')
        self.cartFrame.configure(background='#ffffff', labelanchor='n', relief='ridge', text='اطلاعات کارت')
        self.cartFrame.grid(column='0', row='0')
        self.labelframe7 = tk.LabelFrame(self.informationFrame)
        self.website_url = tk.Entry(self.labelframe7)
        self.website_url.configure(cursor='arrow', justify='center', state='normal', width='30')
        self.website_url.pack(side='top')
        self.labelframe8 = tk.LabelFrame(self.labelframe7)
        self.mobile_num = tk.Entry(self.labelframe8)
        self.mobile_num.configure(cursor='arrow', justify='center', state='normal', width='30')
        self.mobile_num.pack(side='top')
        self.labelframe8.configure(labelanchor='ne', background='#ffffff', relief='ridge', text='شماره مبايل',
                                   width='200')
        self.labelframe8.pack(padx='5', pady='10')
        self.labelframe7.configure(labelanchor='ne', background='#ffffff', relief='ridge', text='آدرس وب سايت')
        self.labelframe7.grid(column='2', row='0')
        self.majazi = tk.LabelFrame(self.informationFrame)
        self.frame1 = tk.Frame(self.majazi)
        self.label1 = tk.Label(self.frame1)
        self.label1.configure(anchor='n', background='#ffffff', text='نام کاربري')
        self.label1.grid(column='2', row='1')
        self.banckuser = ttk.Entry(self.frame1)
        self.banckuser.configure(justify='center', width='15')
        self.banckuser.grid(column='0', row='1')
        self.frame1.configure(background='#ffffff')
        self.frame1.grid(column='0', ipady='5', row='0')
        self.frame5 = tk.Frame(self.majazi)
        self.label10 = tk.Label(self.frame5)
        self.label10.configure(anchor='n', background='#ffffff', text='رمز ثابت')
        self.label10.grid(column='2', row='1')
        self.banckpass = ttk.Entry(self.frame5)
        self.banckpass.configure(justify='center', width='15')
        self.banckpass.grid(column='0', row='1')
        self.frame5.grid(column='0', row='1')
        self.majazi.configure(background='#ffffff', labelanchor='ne', padx='10', pady='10')
        self.majazi.configure(relief='ridge', text='بانک داري مجازي')
        self.majazi.grid(column='1', row='0')
        self.informationFrame.configure(background='#ffffff', height='200', labelanchor='ne', text='ورود اطلاعات',
                                        width='200')
        self.informationFrame.pack(expand='false', fill='x', ipadx='10', ipady='5', side='top')
        self.informationFrame.grid_anchor('s')
        self.labelframe9 = tk.LabelFrame(self.tkscrolledframe3.innerframe)
        self.frame20 = tk.Frame(self.labelframe9)
        self.banckbtn = tk.Button(self.frame20, command=self.banckbtn_command)
        self.banckbtn.configure(background='#0080ff', foreground='#ffffff', relief='raised', text='فرايند بانک')
        self.banckbtn.grid(column='0', padx='10', row='0')
        # self.gatewaybtn = tk.Button(self.frame20, command=self.gatewaybtn_command)
        # self.gatewaybtn.configure(background='#0080ff', foreground='#ffffff', relief='raised', text='فرايند پرداخت')
        # self.gatewaybtn.grid(column='1', padx='10', row='0')
        self.startbtn = tk.Button(self.frame20, command=self.startbtn_command)  #
        self.startbtn.configure(background='#0080ff', foreground='#ffffff', relief='raised', text='فرايند ورود')
        self.startbtn.grid(column='2', padx='10', row='0')
        self.frame20.configure(background='#ffffff', height='200', width='200')
        self.frame20.pack(side='top')
        # self.frame22 = tk.Frame(self.labelframe9)
        # self.smsbtn = tk.Button(self.frame22, command=self.smsbtn_command)
        # self.smsbtn.configure(background='#0080ff', foreground='#ffffff', relief='raised', text='ارسال کد ')
        # self.smsbtn.grid(column='0', padx='10', row='0')
        # self.label19 = tk.Label(self.frame22)
        # self.label19.configure(background='#ffffff', foreground='#000040', text=' : پيامک بانک ')
        # self.label19.grid(column='3', padx='10', row='0')
        # self.smscod = tk.Entry(self.frame22)
        # self.smscod.configure(background='#c0c0c0', justify='center', width='8')
        # self.smscod.grid(column='2', row='0')
        # self.frame22.configure(background='#ffffff', height='200', width='200')
        # self.frame22.pack(pady='10', side='right')
        self.labelframe9.configure(background='#ffffff', height='200', labelanchor='ne', text='فرايند ها')
        self.labelframe9.configure(width='200')
        self.labelframe9.pack(expand='false', fill='x', ipady='10', pady='10', side='top')
        self.labelframe14 = tk.LabelFrame(self.tkscrolledframe3.innerframe)
        self.labelframe14.configure(background='#ffffff', labelanchor='n', text='پيام سيستم')
        self.labelframe14.configure(width='200')
        self.labelframe14.pack(expand='false', fill='both', ipady='10', pady='10', side='top')
        self.labelframe14.grid_anchor('s')
        self.logmessage = tk.Message(self.labelframe14)
        self.logmessage.configure(aspect='10000000', background='#ffffff', foreground='#ff0000')
        self.logmessage.pack(expand='true', fill='x', side='top')
        self.tkscrolledframe3.innerframe.configure(background='#ffffff')
        self.tkscrolledframe3.configure(usemousewheel=False)
        self.tkscrolledframe3.pack(expand='true', fill='both', side='top')
        self.text1 = tk.Text(self.tkscrolledframe3.innerframe)
        self.text1.configure(autoseparators='false', background='#c0c0c0', blockcursor='false', height='2')
        self.text1.configure(insertunfocussed='solid', state='disabled', wrap='none')
        _text_ = '''1) pause recording by Control + P   2) continues recording by Control + R'''
        self.text1.configure(state='normal')
        self.text1.insert('0.0', _text_)
        self.text1.configure(state='disabled')
        self.text1.pack(expand='true', fill='x', side='top')
        self.main.configure(background='#ffffff', height='400', width='650')
        self.main.pack(expand='true', fill='both', side='top')
        self.main.pack_propagate(0)
        # Main widget
        self.mainwindow = self.main

    def eMessage(self, message):
        self.logmessage.configure(text=message)
        # self._rownum_ = self._rownum_ - 1
        # self.logmessage = tk.Message(self.labelframe14)
        # self.logmessage.configure(aspect='10000000', background='#ffffff', foreground='#ff0000', text=message)
        # self.logmessage.grid(row=str(self._rownum_), pady='3')  #

    def save_last_data(self):
        website_url = self.website_url.get()
        mobile_num = self.mobile_num.get()
        cart_id = self.cart_id.get()
        cart_pass2 = self.cart_pass2.get()
        cart_cvv2 = self.cart_cvv2.get()
        cart_month = self.cart_month.get()
        cart_year = self.cart_year.get()
        banckuser = self.banckuser.get()
        banckpass = self.banckpass.get()
        last_data = {
            'website_url': website_url,
            'mobile_num': mobile_num,
            'cart_id': cart_id,
            'cart_pass2': cart_pass2,
            'cart_month': cart_month,
            'cart_year': cart_year,
            'cart_cvv2': cart_cvv2,
            'banckuser': banckuser,
            'banckpass': banckpass,
        }

        with open('data/last_data.json', 'w') as fp:
            json.dump(last_data, fp)

    def load_last_data(self):
        last_data = open('data/last_data.json')
        last_data = json.load(last_data)
        self.website_url.insert('0', last_data['website_url'])  #
        self.mobile_num.insert('0', last_data['mobile_num'])
        self.cart_id.insert('0', last_data['cart_id'])
        self.cart_pass2.insert('0', last_data['cart_pass2'])
        self.cart_cvv2.insert('0', last_data['cart_cvv2'])
        self.cart_month.insert('0', last_data['cart_month'])
        self.cart_year.insert('0', last_data['cart_year'])
        self.banckpass.insert('0', last_data['banckpass'])
        self.banckuser.insert('0', last_data['banckuser'])

    def startbtn_command(self):
        self.save_last_data()
        website_url = self.website_url.get()
        mobile_num = self.mobile_num.get()
        if 'https://' in website_url:
            pass
        else:
            website_url = 'https://' + website_url

        self.address = website_url

        # time.ir
        global time_driver

        if not time_driver:
            time_driver = webdriver.Chrome(executable_path="data/chromedriver.exe")
            time_driver.get('https://www.time.ir/')
            time_driver.maximize_window()
            winwidth = time_driver.get_window_size()['width']
            winheight = time_driver.get_window_size()['width']
            time_driver.set_window_position(0, 0)
            time_driver.set_window_size(winwidth / 2, winheight)

        global driver

        if not driver:
            # s=Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(executable_path="data/chromedriver.exe")
            # driver = webdriver.Chrome(service=s)
            driver.set_window_position(winwidth / 2, 0)
            driver.set_window_size(winwidth / 2, winheight)
            try:
                driver.get(website_url)
                self.title: driver.title
            except:
                self.eMessage('خطا در دریافت سایت')

        con = sqlite3.connect('data/db.sqlite3')
        cur = con.cursor()

        rm_popup(driver)
        # check if exsist in db
        res = cur.execute('SELECT * FROM betscan_website where address = "{}"'.format(self.address))
        if len(res.fetchall()) <= 0:
            cur.execute(
                "insert into betscan_website (address, creat_at, password, sgroup, username, singin, title) values ('{}','{}','{}','{}','{}','{}','{}')".format(
                    self.address, self.creat_at, self.password, self.group, self.username, 0, self.title))
            con.commit()

        # check singin
        res = cur.execute('SELECT singin FROM betscan_website where address = "{}"'.format(self.address))
        res = int(res.fetchone()[0])
        con.close()
        # ScreenRecord
        global recordobj
        recordobj = ScreenRecord()

        def statrRecordFunction():
            recordobj.statrRecord()
            print('startrecord')
            # self.eMessage('startrecord')

        def stopRecordFunctionFunction():
            recordobj.stop = True
            print('stoprecord')
            # self.eMessage('stoprecord')

        def pauseRecordFunction():
            time.sleep(60)
            recordobj.stop = 'pause'
            print('pauserecord')
            # self.eMessage('pauserecord')

        def ContinuesFunction():
            time.sleep(10)
            recordobj.stop = False
            print('ontinuesrecord')
            # self.eMessage('ontinuesrecord')

        global STOP_R
        global PAUSE_R
        global Continues_R
        global START_R
        START_R = Thread(target=statrRecordFunction)
        STOP_R = Thread(target=stopRecordFunctionFunction)
        PAUSE_R = Thread(target=pauseRecordFunction)
        Continues_R = Thread(target=ContinuesFunction)
        START_R.start()

        try:
            rm_popup(driver)
            if res == 0:
                rm_popup(driver)
                singup(self.address, driver, mobile_num, self.email, self.username, self.password)
                rm_popup(driver)
            else:
                singin(driver, mobile_num, self.email, self.username, self.password)
                rm_popup(driver)
                cur.execute("update betscan_website set singin = 1 where address = '{}' ".format(self.address))
                con.commit()
        except:
            self.eMessage('خطا در فرایند ورود')

        try:
            rm_popup(driver)
            links = driver.find_elements_by_tag_name('a')
            for link in links:
                htmlout = link.get_attribute("outerHTML")
                txtlist = ['شارژ', 'افزایش موجودی', 'موجودی', 'شارژ حساب']
                for item in txtlist:
                    if htmlout.find(item) >= 0:
                        driver.get(link.get_attribute("href"))
        except:
            self.eMessage('خطا در پیدا کردن لینک شارژ حساب')

        rm_popup(driver)

        try:
            links = driver.find_elements_by_tag_name('a')
            rm_popup(driver)
            for link in links:
                htmlout = link.get_attribute("outerHTML")
                dargatext = ['وداپى', "درگاه مستقیم", "درگاه انلاین", "درگاه آنلاین(واریز از مبلغ 100 هزار تومان)",
                             'مستقيم', 'بانکی']
                for text in dargatext:
                    if htmlout.find(text) >= 0:
                        driver.get(link.get_attribute("href"))
        except:
            self.eMessage('خطا در پیدا کردن لینک درگاه')

        rm_popup(driver)

        c_url = driver.current_url

        try:
            while c_url == driver.current_url:
                time.sleep(3)
                try:
                    Captcha_label = driver.find_element_by_xpath("//*[text()='کد امنیتی']/..")
                    Captcha = Captcha_label.find_element_by_tag_name("input")
                    cod = find_ca_im(driver)
                    Captcha.clear()
                    Captcha.send_keys(cod)
                except:
                    pass
                Captcha_label = driver.find_element_by_xpath("//*[text()='کد امنیتی']/../..")
                Captcha_label.find_element_by_xpath("..//*[text()='شارژ حساب']").click()
        except:
            self.eMessage('خطا در ورود به درگاه')

        # self.gatewaybtn_command()

        PAUSE_R.start()

    # def gatewaybtn_command(self):
    #     time.sleep(10)
    #     self.Payment_gateway = driver.title
    #     if self.Payment_gateway.find('Master Pay') >= 0:
    #         while True:
    #             active_tab = driver.find_element_by_class_name('pg-tab-active').get_attribute('outerHTML')
    #
    #             if active_tab.find('تاییدیه') >= 0:
    #                 self.eMessage('پیامک بانکی را وارد کنید')
    #                 break
    #
    #             if active_tab.find('ثبت نام') >= 0:
    #                 try:
    #                     button_label = driver.find_element_by_xpath("//*[text()='متوجه شدم']/../..")
    #                     button = button_label.find_element_by_tag_name("button")
    #                     button.click()
    #                 except:
    #                     pass
    #
    #                 try:
    #                     # شماره کارت
    #                     input_label = driver.find_element_by_xpath("//*[text()='شماره کارت:']/../..")
    #                     Input = input_label.find_element_by_tag_name("input")
    #                     Input.clear()
    #                     Input.send_keys(self.cart_id.get())
    #                 except:
    #                     pass
    #
    #                 try:
    #                     # تلفن همراه
    #                     input_label = driver.find_element_by_xpath("//*[text()='تلفن همراه:']/../..")
    #                     Input = input_label.find_element_by_tag_name("input")
    #                     Input.clear()
    #                     mnum = self.mobile_num.get()
    #                     if mnum[0] == '0':
    #                         mnum = mnum.replace("0", "", 1)
    #                     Input.send_keys('0' + mnum)
    #                 except:
    #                     pass
    #
    #                 try:
    #                     # مرحله بعد
    #                     buttons = driver.find_elements_by_tag_name("button")
    #                     for button in buttons:
    #                         if 'مرحله بعد' in button.get_attribute('outerHTML'):
    #                             button.click()
    #                 except:
    #                     pass
    #
    #             if active_tab.find('اطلاعات پرداخت') >= 0:
    #
    #                 try:
    #                     inputs = driver.find_elements_by_tag_name("input")
    #                     for inp in inputs:
    #                         if 'cvv2' in inp.get_attribute('outerHTML'):
    #                             inp.clear()
    #                             inp.send_keys(self.cart_cvv2.get())
    #                     for inp in inputs:
    #                         if 'ماه' in inp.get_attribute('outerHTML'):
    #                             inp.clear()
    #                             inp.send_keys(self.cart_month.get())
    #                     for inp in inputs:
    #                         if 'سال' in inp.get_attribute('outerHTML'):
    #                             inp.clear()
    #                             inp.send_keys(self.cart_year.get()[2:])
    #
    #                     input_label = driver.find_element_by_xpath("//*[text()='دریافت رمز']/..")
    #                     Input = input_label.find_element_by_tag_name("input")
    #                     Input.clear()
    #                     Input.send_keys(self.cart_pass2.get())
    #
    #                     buttons = driver.find_elements_by_tag_name("button")
    #                     for button in buttons:
    #                         if 'پرداخت' in button.get_attribute('outerHTML'):
    #                             button.click()
    #                 except:
    #                     pass
    #                 time.sleep(50)
    #     else:
    #         self.eMessage('درگاه تعریف نشده ! به صورت دستی عملیات درگاه را انجام دهید')

    # def smsbtn_command(self):
    #     try:
    #         active_tab = driver.find_element_by_class_name('pg-tab-active').get_attribute('outerHTML')
    #         if active_tab.find('تاییدیه') >= 0:
    #             smscod = self.smscod.get()
    #             # sms کد ارسال شد به:
    #             Input = driver.find_element_by_tag_name("input")
    #             Input.clear()
    #             Input.send_keys(smscod)
    #
    #             # مرحله بعد
    #             buttons = driver.find_elements_by_tag_name("button")
    #             for button in buttons:
    #                 if 'مرحله بعد' in button.get_attribute('outerHTML'):
    #                     button.click()
    #
    #         time.sleep(30)
    #         while True:
    #             try:
    #                 paystate = driver.find_element_by_tag_name('body').get_attribute('outerHTML').find('کافی نیست')
    #                 if paystate >= 0:
    #                     # driver.quit()
    #                     break
    #             except:
    #                 self.eMessage('عملیات درگاه بانکی انجام شد')
    #     except:
    #         pass

    def banckbtn_command(self):
        website_url = self.website_url.get()
        mobile_num = self.mobile_num.get()
        cart_id = self.cart_id.get()
        cart_pass2 = self.cart_pass2.get()
        cart_cvv2 = self.cart_cvv2.get()
        cart_month = self.cart_month.get()
        cart_year = self.cart_year.get()
        banckuser = self.banckuser.get()
        banckpass = self.banckpass.get()
        self.Payment_gateway = driver.title
        # driver = webdriver.Chrome(executable_path="chromedriver.exe")
        driver.get('https://ib.bpi.ir/')

        Continues_R.start()

        c_url = driver.current_url
        while c_url == driver.current_url:
            try:
                driver.find_element_by_xpath('//*[@id="AgreementSecureKeyboard"]/div/div[2]/label').click()

                Username = driver.find_element_by_xpath('//*[@id="username"]')
                Username.clear()
                Username.send_keys(banckuser)

                Password = driver.find_element_by_xpath('//*[@id="password"]')
                Password.clear()
                Password.send_keys(banckpass)
                driver.find_element_by_xpath('//*[@id="imageBtn"]').click()

                time.sleep(3)
                security_captcha_img = driver.find_element_by_xpath('//*[@id="captchaImg"]/img')

                with open('data/security_captcha.png', 'wb') as file:
                    file.write(security_captcha_img.screenshot_as_png)
                ckeys = imagetostr('data/security_captcha.png')

                CaptchaTxt = driver.find_element_by_xpath('//*[@id="captchaTxt"]')
                CaptchaTxt.clear()
                CaptchaTxt.send_keys(ckeys)

                driver.find_element_by_xpath('//*[@id="btnLogin"]').click()
            except:
                pass

        sender_name = driver.find_element_by_xpath('//*[@id="ctl00_activePage_lblUsernameResponsiveTop"]').text
        driver.get('https://ib.bpi.ir/CardForms/TransactionCardReport.aspx')

        select = Select(driver.find_element_by_xpath('//*[@id="ctl00_activePage_ddlCard"]'))
        select.select_by_visible_text(cart_id)

        # set date for serch

        jdate = gregorian_to_jalali(self.creat_at.year, self.creat_at.month, self.creat_at.day)
        # from

        fromday = driver.find_element_by_xpath('//*[@id="ctl00_activePage_startDate_day"]')
        fromday.clear()
        fromday.send_keys(jdate[2])

        fromday = driver.find_element_by_xpath('//*[@id="ctl00_activePage_startDate_mounth"]')
        fromday.clear()
        fromday.send_keys(jdate[1])

        fromday = driver.find_element_by_xpath('//*[@id="ctl00_activePage_startDate_year"]')
        fromday.clear()
        fromday.send_keys(jdate[0])
        # to
        day = driver.find_element_by_xpath('//*[@id="ctl00_activePage_endDate_day"]')
        day.clear()
        day.send_keys(jdate[2])

        day = driver.find_element_by_xpath('//*[@id="ctl00_activePage_endDate_mounth"]')
        day.clear()
        day.send_keys(jdate[1])

        day = driver.find_element_by_xpath('//*[@id="ctl00_activePage_endDate_year"]')
        day.clear()
        day.send_keys(jdate[0])

        driver.find_element_by_xpath('//*[@id="ctl00_activePage_btnSearch"]').click()

        # get table data
        tbody = driver.find_element_by_xpath(
            '//*[@id="ctl00_activePage_grdCardTransactionsList"]').find_element_by_tag_name('tbody')

        rows = tbody.find_elements_by_tag_name('tr')  # get all of the rows in the table

        Transaction = {}
        for row in rows:
            cols = row.find_elements_by_tag_name('td')
            Transaction[cols[0].text] = {'time': cols[1].text, 'value': cols[4].text, 'Destination_card': cols[5].text,
                                         'Issue_Tracking': cols[6].text}

        # ?
        lastitem = [i for i in Transaction.keys()][-1]
        Destination_card = Transaction[lastitem]['Destination_card']
        transaction_value = Transaction[lastitem]['value']
        Issue_Tracking = Transaction[lastitem]['Issue_Tracking']
        date_time = Transaction[lastitem]['time'].split('\n')
        jdate = [int(i) for i in date_time[0].split('/')]
        jdate = jalali_to_gregorian(jdate[0], jdate[1], jdate[2])
        miladi_datetime = str(jdate[0]) + '-' + str(jdate[1]) + '-' + str(jdate[2]) + ' ' + date_time[1]

        #

        driver.get('https://ib.bpi.ir/Transfers/CardToCard.aspx')
        driver.find_element_by_xpath(
            '//*[@id="ctl00_ctl00_activePage_sourceInputPH_CardControl_txtCVV2_txtContent"]').send_keys(cart_cvv2)
        driver.find_element_by_xpath(
            '//*[@id="ctl00_ctl00_activePage_sourceInputPH_CardControl_txtMonthExpireDate_txtContent"]').send_keys(
            cart_month)
        driver.find_element_by_xpath(
            '//*[@id="ctl00_ctl00_activePage_sourceInputPH_CardControl_txtYearExpireDate_txtContent"]').send_keys(
            cart_year[2:])
        #
        driver.find_element_by_xpath(
            '//*[@id="ctl00_ctl00_activePage_simpleDestinationPH_DestCardControl_CardNumberControl_txtCardPart_1"]').send_keys(
            Destination_card)
        driver.find_element_by_xpath(
            '//*[@id="ctl00_ctl00_activePage_simpleDestinationPH_amount_txtContent"]').send_keys('10000')
        driver.find_element_by_xpath(
            '//*[@id="ctl00_ctl00_activePage_SendOtpPlaceHolder_sendOtpControl_txtcardPass_txtContent"]').send_keys(
            cart_pass2)
        driver.find_element_by_xpath('//*[@id="ctl00_ctl00_activePage_btnSeeDatail"]').click()

        # get subject name
        subject_name = driver.find_element_by_xpath(
            '/html/body/form/div[4]/div/div[2]/div[2]/div[3]/div[4]/div/div/div[7]/div[2]/span').text
        #
        BankName = driver.find_element_by_xpath(
            '//*[@id="ctl00_ctl00_activePage_TransferDetailFormPH_lblBankName"]').text
        time.sleep(5)

        STOP_R.start()

        exportdata = {}
        exportdata['subject_card'] = Destination_card
        exportdata['subject_name'] = subject_name
        exportdata['sender_cart_id'] = cart_id
        exportdata['sender_name'] = sender_name
        exportdata['date_time'] = str(Transaction[lastitem]['time'])
        exportdata['website_url'] = website_url
        exportdata['website_name'] = self.title
        exportdata['transaction_value'] = transaction_value
        exportdata['Payment_gateway'] = self.Payment_gateway
        exportdata['subject_card_BankName'] = BankName
        exportdata['Issue_Tracking'] = Issue_Tracking

        # filename = 'records/'+str(datetime.datetime.now().isoformat(timespec='minutes')).replace(':', '-')+'.csv'
        exportdata = [exportdata[i] for i in exportdata.keys()]
        with open('records/ExportData.csv', 'a', encoding='utf-8-sig') as f_object:
            writer_object = writer(f_object)
            writer_object.writerow(exportdata)
            f_object.close()

        con = sqlite3.connect('data/db.sqlite3')
        cur = con.cursor()

        res = cur.execute('select id from betscan_cart where cartid = ' + Destination_card)
        if len(res.fetchall()) <= 0:
            sql1 = "insert into betscan_cart (cartid, customer_name, creat_at, bank_name) values ('{}','{}','{}','{}')".format(
                Destination_card, subject_name, miladi_datetime, BankName)
            cur.execute(sql1)

        sql = "select id from betscan_cart where cartid = '{}' ".format(Destination_card)
        res = cur.execute(sql)
        Cart_id = res.fetchone()[0]

        sql = "select id from betscan_website where address = '{}' ".format(website_url)
        res = cur.execute(sql)
        Website_id = res.fetchone()[0]

        res = cur.execute(
            "select id from betscan_records where Cart_id = '{}' and Website_id = '{}' and creat_at = '{}' ".format(
                Cart_id, Website_id, miladi_datetime))
        if len(res.fetchall()) <= 0:
            sql2 = "insert into betscan_records(Cart_id, Website_id, creat_at, transaction_value, Issue_Tracking, Payment_gateway) values ('{}','{}','{}','{}','{}','{}')".format(
                Cart_id, Website_id, miladi_datetime, transaction_value, Issue_Tracking, self.Payment_gateway)
            cur.execute(sql2)

        con.commit()
        con.close()

        driver.quit()
        time_driver.quit()

    def run(self):
        self.load_last_data()
        self.mainwindow.mainloop()


if __name__ == '__main__':
    root = tk.Tk()
    root.title("Bet Scan")
    app = GuiApp(root)
    app.run()
