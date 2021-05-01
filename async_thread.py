# import requests
# import time
#
# while True:
#     data = requests.post("URL_HERE", json={
#         "api_key":"XXXX",
#         "concat": 1,
#         "messages": "HI"
#     })
#     time.sleep(60)

import time, requests
import datetime
import xml.etree.ElementTree as ET


import sys
import argparse

def send_post():
    response = requests.get("https://www.cbr-xml-daily.ru/daily_utf8.xml")
    string_xml = response.content
    # root = ET.fromstring(string_xml)
    # print(root)
    # tree = ET.parse('new.xml')
    # root = tree.getroot()
    # # for child in tree:
    # #     print(child.tag, child.attrib)
    # data1 = root.findall(".")
    # data2 = root.findall(".//year/..[@name='Singapore']")
    # data3 = root.findall(".//*[@name='Singapore']/year")

    root = ET.fromstring(string_xml)
    data1 = root.findall(".*[NumCode='840']/CharCode")[0].text
    data2 = root.findall(".*[NumCode='978']/CharCode")[0].text
    data3 = root.findall(".*[NumCode='840']/Value")[0].text
    data4 = root.findall(".*[NumCode='978']/Value")[0].text
    print('print', data1, data3, data2, data4)


# parser = argparse.ArgumentParser()
# parser.add_argument("echo")
# args = parser.parse_args()
# print(args.echo)
def start_schedul():
    while True:
        send_post()
        time.sleep(10 - datetime.datetime.now().second % 10)




def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name')
    return parser


if __name__ == '__main__':
    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])
    start_schedul()

