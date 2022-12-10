#!/usr/bin/env python3

from bs4 import BeautifulSoup
import sqlite3
import aiohttp
import asyncio
conn = sqlite3.connect('../database/students.db')
c = conn.cursor()

headers = {
    "Referer": "https://oa.cc.iitk.ac.in/Oa/Jsp/OAServices/IITK_Srch.jsp?typ=stud"
}

headers1 = {
    "Referer": "https://oa.cc.iitk.ac.in/Oa/Jsp/OAServices/IITk_SrchStudRoll_new.jsp"
}
def get_payload(i):
    payload = {
        'k4': 'oa',
        'numtxt': '',
        'recpos': i,
        'str': '',
        'selstudrol': '',
        'selstuddep': '',
        'selstudnam': '',
        'txrollno': '',
        'Dept_Stud': '',
        'selnam1': '',
        'mail': ''
    }
    return payload
def get_payload1(i):
    payload1 = {
        'typ': ['stud'] * 12,
        'numtxt': i,
        'sbm': ['Y'] * 12
    }
    return payload1

TOTAL = 8385

def process_response_soup(soup1,roll,c):
        name = ''
        program = ''
        dept = ''
        hall = ''
        room = ''
        username = ''
        blood_group = ''
        gender = ''
        hometown = ''

        for para in soup1.select('.TableContent p'):
            body = para.get_text().strip()
            field = body.split(':')
            key = field[0].strip()
            value = field[1].strip()
            if key == 'Name':
                name = value.lower().title()
            elif key == 'Program':
                program = value
            elif key == 'Department':
                dept = value.lower().title()
            elif key == 'Hostel Info':
                if len(value.split(',')) > 1:
                    hall = value.split(',')[0].strip()
                    room = value.split(',')[1].strip()
            elif key == 'E-Mail':
                if len(value.split('@')) > 1:
                    username = value.split('@')[0].strip()
            elif key == 'Blood Group':
                blood_group = value
            elif key == 'Gender':
                if len(value.split('\t')) > 1:
                    gender = value.split('\t')[0].strip()
            else:
                print("{} {}".format(key, value))

        body = soup1.prettify()
        if len(body.split('Permanent Address :')) > 1:
            address = body.split('Permanent Address :')[1].split(',')
            if len(address) > 2:
                address = address[len(address) - 3: len(address) - 1]
                hometown = "{}, {}".format(address[0], address[1])

        c.execute('REPLACE INTO students VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  (roll, username, name, program, dept, hall, room,
                   blood_group, gender, hometown))


# r = s.post("https://oa.cc.iitk.ac.in/Oa/Jsp/OAServices/IITk_SrchStudRoll_new.jsp", headers=headers, data=payload)
# soup = BeautifulSoup(r.text, 'html.parser')
# for link in soup.select('.DivContent'):
#     substituted = re.sub(r'\s+', ' ', link.text)
#     pattern = re.compile(r'\s*You are viewing 1 to 12 records out of (\d+) records\s*')
#     match = pattern.match(substituted)
#     TOTAL = int(match.group(1))
#     print("Total: {}".format(TOTAL))
# process_response_soup(soup, c)
# print("Processed 12")
async def get_rolls():    
    roll_list = []
    async with aiohttp.ClientSession(trust_env = True) as session:
        await session.get("https://oa.cc.iitk.ac.in/Oa/Jsp/Main_Frameset.jsp")
        await session.get("https://oa.cc.iitk.ac.in/Oa/Jsp/Main_Intro.jsp?frm='SRCH'")
        await session.get("https://oa.cc.iitk.ac.in/Oa/Jsp/OAServices/IITK_Srch.jsp?typ=stud")
        pages = []
        TOTAL = 100
        payloads = list(map(get_payload,[i for i in range(0,TOTAL+1,12)]))
        for payload in payloads:
            pages.append(asyncio.create_task(session.post("https://oa.cc.iitk.ac.in/Oa/Jsp/OAServices/IITk_SrchStudRoll_new.jsp",data=payload,headers=headers, ssl = False)))
        responses = await asyncio.gather(*pages)
        for res in responses:
            soup = BeautifulSoup(await res.text(), 'html.parser')
            for link in soup.select('.TableText a'):
                roll_list.append(link.get_text().strip())
        print(roll_list)
        return roll_list
    # conn.commit()
# conn.close()
async def get_individual():
    roll_list = await get_rolls()
    async with aiohttp.ClientSession(trust_env = True) as session:
        await session.get("https://oa.cc.iitk.ac.in/Oa/Jsp/Main_Frameset.jsp")
        await session.get("https://oa.cc.iitk.ac.in/Oa/Jsp/Main_Intro.jsp?frm='SRCH'")
        await session.get("https://oa.cc.iitk.ac.in/Oa/Jsp/OAServices/IITK_Srch.jsp?typ=stud")
        payload1s = list(map(get_payload1,roll_list))
        pages = []
        for payload1 in payload1s:
            pages.append(asyncio.create_task(session.post("https://oa.cc.iitk.ac.in/Oa/Jsp/OAServices/IITk_SrchRes_new.jsp", headers=headers1, data=payload1,ssl=False)))
        responses = await(asyncio.gather(*pages))
        i = 0
        for res in responses:
            roll = roll_list[i]
            soup1 = BeautifulSoup(await res.text(), 'html.parser')
            process_response_soup(soup1,roll,c)
            i+=1
        conn.commit()

asyncio.run(get_individual())