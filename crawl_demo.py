from bs4 import BeautifulSoup
from config import *
from email.mime.text import MIMEText
import pymysql
from selenium import webdriver
import smtplib

# Init DB Connection
conn = pymysql.connect(host='localhost', user='root', password=get_gmail_pw(), db='bb', charset='utf8')
curs = conn.cursor()


# Init Chrome Webdriver
driver = webdriver.Chrome(get_chrome_driver())
driver.implicitly_wait(3)

driver.get(get_target_url())


# LogIn to target url
driver.find_element_by_name('id').send_keys(get_blackboard_id())
driver.find_element_by_name('pw').send_keys(get_blackboard_pw())
driver.find_element_by_xpath('//*[@id="entry-login"]').click()

driver.get('https://kulms.korea.ac.kr/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_2_1')

subject_list = [('130456_1', '2200239_1'), ('130455_1', 0), ('130904_1', 0), ('129758_1', '2197447_1'), ('128802_1', '2193627_1'), ('128798_1', 0), ('130469_1', '2200291_1')]
subject_url_1 = 'https://kulms.korea.ac.kr/webapps/blackboard/execute/announcement?method=search&context=course_entry&course_id=_'
subject_url_2 = '&handle=announcements_entry&mode=view'
subject_url_3 = 'https://kulms.korea.ac.kr/webapps/blackboard/content/listContent.jsp?course_id=_'
subject_url_4 = '&content_id=_'
subject_url_5 = '&mode=reset'


# Init Mail Service
smtp = smtplib.SMTP('smtp.gmail.com', 587)
smtp.ehlo()
smtp.starttls()
smtp.login(get_gmail_id(), get_gmail_pw())


# Get Existing Datas from DB
announcements_db = []
assignments_db = []

sql = "select * from announcement"
curs.execute(sql)
rows = curs.fetchall()
for a in rows:
    announcements_db.append(a[0])

sql = "select * from assignment"
curs.execute(sql)
rows = curs.fetchall()
for a in rows:
    assignments_db.append(a[0])


# Crawls DATA and check works
for subject in subject_list:
    # Get Announcements
    subject_announcement_url = subject_url_1 + subject[0] + subject_url_2
    driver.get(subject_announcement_url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    announcements = soup.select('li.clearfix')[10:]
    announcements.reverse()

    # Check DB & Send Mail of Announcements
    for ann in announcements:
        print(ann.attrs['id'])
        print('---------------')

        if ann.attrs['id'] not in announcements_db:
            sql_ann = 'insert into announcement values(\"' + ann.attrs['id'] + '\")'
            print(sql_ann)
            curs.execute(sql_ann)
            conn.commit()

            msg = MIMEText(ann.text)
            msg['Subject'] = 'Announcement for ' + subject[0]
            msg['To'] = get_user_mail()
            smtp.sendmail(get_gmail_id(), get_user_mail(), msg.as_string())

    # Get Assignments if exists
    if subject[1] != 0:
        subject_assignment_url = subject_url_3 + subject[0] + subject_url_4 + subject[1] + subject_url_5
        driver.get(subject_assignment_url)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        assignments = soup.select('ul.contentList > li')

        # Check DB & Send Mail of Assignments
        for ass in assignments:
            print(ass.attrs['id'])

            if ass.attrs['id'] not in assignments_db:
                sql_ass = "insert into assignment values(\"" + ass.attrs['id'] + '\")'
                curs.execute(sql_ass)
                conn.commit()

                msg = MIMEText(ass.text)
                msg['Subject'] = 'Assignment for ' + subject[0]
                msg['To'] = get_user_mail()
                smtp.sendmail(get_gmail_id(), get_user_mail(), msg.as_string())

smtp.quit()
