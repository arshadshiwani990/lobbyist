
import requests
from bs4 import BeautifulSoup
import re
import sqlite3




def create_database(database_name):
    try:
        conn = sqlite3.connect(database_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lobbyists (
                FilerID TEXT,
                FirstName TEXT,
                LastName TEXT,
                Address TEXT,
                Phone TEXT,
                Email TEXT,
                EthicsCourseCompletionDate TEXT,
                RegistrationDate TEXT,
                Status TEXT,
                Entity TEXT,
                TypeOfRelationship TEXT,
                EffectiveDate TEXT,
                TerminationDate TEXT,
                ProfileURL TEXT
            )
        ''')
        conn.commit()
        print("Database created successfully.")
    except sqlite3.Error as e:
        print("Error creating database:", e)
    finally:
        if conn:
            conn.close()

create_database("lobbyist_data.db")
conn = sqlite3.connect("lobbyist_data.db")
cursor = conn.cursor()


def insert_data(conn, cursor, data):
    try:
        # Prepare a list of values to insert, replacing missing values with None
        values = [
            data.get('Filer ID', None),
            data.get('First Name', None),
            data.get('Last Name', None),
            data.get('Address', None),
            data.get('Phone', None),
            data.get('Email', None),
            data.get('Ethics Course Completion Date', None),
            data.get('Registration Date', None),
            data.get('Status', None),
            data.get('Entity', None),
            data.get('Type of Relationship', None),
            data.get('Effective Date', None),
            data.get('Termination Date', None),
            data.get('ProfileURL', None)
        ]

        # Insert data into the table
        cursor.execute('''
            INSERT INTO lobbyists (FilerID, FirstName, LastName, Address, Phone, Email, EthicsCourseCompletionDate, RegistrationDate, Status, Entity, TypeOfRelationship, EffectiveDate, TerminationDate, ProfileURL)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', values)
        conn.commit()
        print("Data inserted successfully. id="+str(data.get('Filer ID', None)))
    except sqlite3.Error as e:
        print("Error inserting data:", e)
        

def send_request(url, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url,timeout=30)
            response.raise_for_status()
            return response
        except ConnectionError as e:
         
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                print("Retrying...")
                time.sleep(2)  
                continue
            else:
                raise e
            
           
def check_filer_id_exists(conn, cursor, filer_id):
    try:
        cursor.execute('SELECT COUNT(*) FROM lobbyists WHERE FilerID = ?', (filer_id,))
        row_count = cursor.fetchone()[0]
        return row_count > 0
    except sqlite3.Error as e:
        print("Error checking filer_id existence:", e)
        return False
    
    
def scrape_profile(url,filer_id,conn,cursor):
    
    
    try:
        item={}
        item['Filer ID']=filer_id
        response=send_request(url)
        soup=BeautifulSoup(response.content,'html.parser')
        
        name=soup.find('span',{'id':'lblFilerName'}).text
        if ',' in name:
            name=soup.find('span',{'id':'lblFilerName'}).text.split(',')
            first_name=name[0].strip()
            last_name=name[1].strip()
        else:
            first_name=name
            last_name=''
        
        
    
        item['First Name']=first_name
        item['Last Name']=last_name
        
        table = soup.find('table', bgcolor="#7183c6")

        if table:

            rows = table.find_all('tr')
            address_row = rows[1]
            address=''
            phone=''
            email=''
            address_text = address_row.find('span', class_='txt7').text.split('\n')
            for i in address_text:
                if 'Phone' not in i and 'Email' not in i.strip():
                    address=address+" "+i.strip()
                elif 'Phone' in i and 'Email' not in i.strip():
                    phone=phone+" "+i.strip().replace('Phone:','')
                    phone=phone.strip()
                elif 'Phone' not in i and 'Email' in i.strip():
                    email=email+" "+i.strip().replace('Email:','')
                    email=email.strip()
                    
                    
            address=address.strip() 
   
            # print(address)
            # print(phone)
            # print(email)
            # address_match = re.search(r'(.+\, [A-Za-z]+ [a-z\d]+)', address_text, re.MULTILINE)
            # phone_match = re.search(r'Phone: ([\d\-\(\\ )]+)', address_text)
            # email_match = re.search(r'Email: ([\w.-]+@[\w.-]+)', address_text)

     

        #     if address_match:
        #         address=address_match.group(1).strip()
        #     else:
        #         address=''
        #     if phone_match:
        #         phone=phone_match.group(1)
        #     else:
        #         phone=''
        #     if email_match:
        #         email=email_match.group(1)
        #     else:
        #         email=''        
        # else:
        #     print("Table not found.")
        
        
        
        table = soup.find('table', class_='txt7')
        if table:
            ethics_course_completion_date = []
            registration_date = []
            status = []

            rows = table.find_all('tr')
            for row in rows[1:]:
                cells = row.find_all('td')
                ethics_course_completion_date.append(cells[0].get_text(strip=True))
                registration_date.append(cells[1].get_text(strip=True))
                status.append(cells[2].get_text(strip=True))
            
            ethics_course_completion_date=ethics_course_completion_date[0]
            registration_date=registration_date[0]
            status=status[0]
        else:
            print("Table not found.")
            

        item['Address']=address
        item['Phone']=phone
        item['Email']=email
        
        item['Ethics Course Completion Date']=ethics_course_completion_date
        item['Registration Date']=registration_date
        item['Status']=status

        
        tables = soup.find_all('table',{"bordercolor":'#3149aa'})
        for table in tables:
            if 'LOBBYIST RELATIONSHIPS' in table.text:
                
                rows = table.find_all('tr')
                for row in rows[2:]:
                    cells = row.find_all('td')
                    ENTITY=cells[0].get_text(strip=True)
                    TYPE_OF_RELATIONSHIP=cells[1].get_text(strip=True)
                    EFFECTIVE_DATE=cells[2].get_text(strip=True)
                    TERMINATION_DATE=cells[3].get_text(strip=True)
            
                    item['Entity']=ENTITY
                    item['Type of Relationship']=TYPE_OF_RELATIONSHIP
                    item['Effective Date']=EFFECTIVE_DATE
                    item['Termination Date']=TERMINATION_DATE
        
        item['ProfileURL']=url
        insert_data(conn, cursor, item)

    except Exception as e:
        print(e)




# url='https://cal-access.sos.ca.gov/Lobbying/Lobbyists/Detail.aspx?id=1148748&session=2023'
# scrape_profile(url,'1148748',conn,cursor)      
def scrape_filter_page(url):

    response=send_request(url)
    soup=BeautifulSoup(response.content,'html.parser')
    table=soup.find('table',{'id':'lobbyists'})
    trs=table.find_all('tr')
    for tr in trs:
        tds=tr.find_all('td')
        slug=tds[0].find('a')['href']
        filer_id=tds[1].text
        base_url='https://cal-access.sos.ca.gov/Lobbying/Lobbyists/'
        link=f'{base_url}{slug}'
        if filer_id != 'FILER ID':
        
            
            if not check_filer_id_exists(conn, cursor, filer_id):
                scrape_profile(link,filer_id,conn,cursor)
            else:
                print(f"Filer ID {filer_id} already exists in the database. Skipping...")
            # break
     
base_url='https://cal-access.sos.ca.gov'
url='https://cal-access.sos.ca.gov/Lobbying/Lobbyists/'
response=send_request(url)
soup=BeautifulSoup(response.content,'html.parser')
filter_letters=soup.find('table',{"id":'letter'})
filter_letters=filter_letters.find_all('a',{'class':'sublink2'})
for td in filter_letters:
    slug=td['href']
    link=f'{base_url}{slug}'
    scrape_filter_page(link)
    
