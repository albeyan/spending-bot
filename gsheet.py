import prettytable as pt
import json
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

with open("config.json", "r") as read_file:
        config = json.load(read_file)

SPREADSHEET_ID = config['spreadsheet_id']
PLAYER_1 = config['player_1']
PLAYER_2 = config['player_2']


def get_sheet():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = service_account.Credentials \
        .from_service_account_file('credentials-google.json', scopes=scopes)
    gsheet_service = build('sheets', 'v4',
                            credentials=credentials, cache_discovery=False)
    sheet = gsheet_service.spreadsheets()
    return sheet


def get_data():
    sheet = get_sheet()
    data_range = 'Sheet1!A1:F'

    try:
        data_result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=data_range).execute()
        data = data_result.get('values', [])

        if not data:
            print('No data found.')
            return
    except HttpError as err:
        print(err)

    return data


def print_last_items():
    data = get_data()[1:]

    table = pt.PrettyTable(['Id', 'Date', 'Payer', 'Item',
                            'Cost', 'Beneficiary'])
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
            table.add_row([id, date, payer, item[:12],
                            f'{float(cost):.0f}', beneficiary])

    return table


def calculate_debt():
    debt = {}
    df = pd.DataFrame(get_data())
    df.columns = df.iloc[0]
    df = df[1:]
    df['Cost'] = pd.to_numeric(df['Cost'])

    paid = df.groupby('Payer')['Cost'].sum()
    benefit = df.groupby('Beneficiary')['Cost'].sum()

    for player in [PLAYER_1, PLAYER_2]:
        player_debt = benefit[player] + benefit['Both']/2 - paid[player]
        if player_debt > 0:
            debt[player] = player_debt

    return debt


def delete_item(id):
    row = int(id) + 1
    sheet = get_sheet()
    range = f'Sheet1!B{row}:G{row}'
    sheet.values().clear(spreadsheetId=SPREADSHEET_ID, range=range).execute()


def delete_last():
    sheet = get_sheet()
    last_id = (list(get_sheet().values()
        .get(spreadsheetId=SPREADSHEET_ID, range='Sheet1!A2:A')
        .execute().values())[2][-1][0])
    row = int(last_id) + 1
    range = f'Sheet1!A{row}:G{row}'
    sheet.values().clear(spreadsheetId=SPREADSHEET_ID, range=range).execute()


def add_item(date, payer, item, cost, beneficiary):
    sheet = get_sheet()
    last_id = (list(get_sheet().values()
        .get(spreadsheetId=SPREADSHEET_ID, range='Sheet1!A2:A')
        .execute().values())[2][-1][0])
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
    pass
