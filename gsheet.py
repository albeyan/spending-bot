from __future__ import print_function

import os.path
import prettytable as pt

""""
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
"""
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

# The ID of the spreadsheet.
SPREADSHEET_ID = '1fcliNUUDbhKN3Ua7HYGng4mtm-vwQhUtOGCYLP-JQf8'


def get_sheet():
    scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    # 'https://www.googleapis.com/auth/drive'
    ]
    credentials = service_account.Credentials.from_service_account_file('credentials-google.json', scopes=scopes)
    gsheet_service = build('sheets', 'v4', credentials=credentials, cache_discovery=False)
    sheet = gsheet_service.spreadsheets()
    return sheet


def get_data():
    sheet = get_sheet()

    # column_names_range = 'Sheet1!A1:F1'
    data_range = 'Sheet1!A2:F'
    try:
        # column_names_result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
        #                             range=column_names_range).execute()
        # column_names = column_names_result.get('values', [])

        data_result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=data_range).execute()
        data = data_result.get('values', [])

        if not data:
            print('No data found.')
            return
    except HttpError as err:
        print(err)

    # return column_names, data
    return data


def print_last_items():
    data = get_data()

    table = pt.PrettyTable(['Id', 'Date', 'Payer', 'Item', 'Cost', 'Beneficiary'])
    table.align['Id'] = 'r'
    table.align['Date'] = 'l'
    table.align['Payer'] = 'l'
    table.align['Item'] = 'l'
    table.align['Cost'] = 'r'
    table.align['Beneficiary'] = 'l'

    for row in data[-10:]:
        id = row[0]
        if len(row) == 1:
            table.add_row([id, '', '', '', '', ''])
        else:
            date = row[1]
            payer = row[2]
            item = row[3]
            cost = row[4]
            beneficiary = row[5]
            table.add_row([id, date, payer, item[:12], f'{float(cost):.0f}', beneficiary])

    return table


# def print_track_list():a
#     column_names, data = get_data()
#     table = ""
#     table += ('%s\t %s\t %s\t %s\t %s\n' % (column_names[0][0],
#                                 column_names[0][1],
#                                 column_names[0][2],
#                                 column_names[0][3],
#                                 column_names[0][4]))
#     for row in data[-10:]:
#         table += ('%s\t %s\t %s\t %s\t %s\n' % (row[0],
#                                     row[1],
#                                     row[2],
#                                     row[3],
#                                     row[4]))
#     return table


def delete_item(id):
    sheet = get_sheet()
    range = f'Sheet1!B{id}:G{id}'
    sheet.values().clear(spreadsheetId=SPREADSHEET_ID, range=range).execute()


def add_item(date, payer, item, cost, beneficiary):
    sheet = get_sheet()
    last_id = list(get_sheet().values().get(spreadsheetId=SPREADSHEET_ID, range='Sheet1!A2:A').execute().values())[2][-1][0]
    print(last_id)
    id = str(int(last_id) + 1)
    notes = ''

    body = {
        "majorDimension": "ROWS",
        "values": [[id, date, payer, item, cost, beneficiary, notes]],
    }
    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet1!A1:G1",
        valueInputOption='USER_ENTERED',
        body=body).execute()


if __name__ == '__main__':
    # add_item('2022-02-09', 'Herni', 'Vuelos', '240500', 'Both')
    # print(print_track_list())
    pass