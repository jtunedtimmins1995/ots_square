from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow,Flow
from google.auth.transport.requests import Request

import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from boto import get_google_secret

import pandas as pd
import os 
import pickle

scopes = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']


def get_spread_sheet(spreadsheet_id, spreadsheet_range):
    
    creds = Credentials.from_service_account_info(get_google_secret(), scopes=scopes)
    

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result_input = sheet.values().get(spreadsheetId=spreadsheet_id,
                                range=spreadsheet_range).execute()
    values_input = result_input.get('values', [])



    
    df=pd.DataFrame(values_input[1:], columns=values_input[0])

    return df

def get_raw_spread_sheet(spreadsheet_id, spreadsheet_range):
    
    creds = Credentials.from_service_account_info(get_google_secret(), scopes=scopes)
    

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result_input = sheet.values().get(spreadsheetId=spreadsheet_id,
                                range=spreadsheet_range).execute()
    # values_input = result_input.get('values', [])



    
    # df=pd.DataFrame(values_input[1:], columns=values_input[0])

    return result_input



def append_to_sheet(sheet_name, spreadhseet_id, df):
    
    credentials = Credentials.from_service_account_info(get_google_secret(), scopes=scopes)

    gc = gspread.authorize(credentials)

    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)

    # # open a google sheet
    service = build('sheets', 'v4', credentials=credentials)

    # Call the Sheets API
    sheet = service.spreadsheets()
    SAMPLE_SPREADSHEET_ID_input = '1K_uXqI1eiguBMr0uH3Tu7xDzePAIi3uAsDrAWukyBq8'
    SAMPLE_RANGE_NAME = 'Square Subs!A:G'
    df_values = df.values.tolist()
    data = {'values':df_values}
    sheet.values().append(spreadsheetId=SAMPLE_SPREADSHEET_ID_input,
                                range=SAMPLE_RANGE_NAME, body=data, valueInputOption='USER_ENTERED').execute()
    # # select a work sheet from its name
    
    # sheet.values_append(sheet_name, {'valueInputOption': 'RAW'}, {'values': df_values})



def append_to_sheet_temp(SAMPLE_RANGE_NAME, SAMPLE_SPREADSHEET_ID_input, df):
    
    credentials = Credentials.from_service_account_info(get_google_secret(), scopes=scopes)

    gc = gspread.authorize(credentials)

    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)

    # # open a google sheet
    service = build('sheets', 'v4', credentials=credentials)

    # Call the Sheets API
    sheet = service.spreadsheets()
    df_values = df.values.tolist()
    data = {'values':df_values}
    sheet.values().append(spreadsheetId=SAMPLE_SPREADSHEET_ID_input,
                                range=SAMPLE_RANGE_NAME, body=data, valueInputOption='USER_ENTERED').execute()
    # # select a work sheet from its name
    
    # sheet.values_append(sheet_name, {'valueInputOption': 'RAW'}, {'values': df_values})

if __name__=='__main__':
    SAMPLE_SPREADSHEET_ID_input = '1K_uXqI1eiguBMr0uH3Tu7xDzePAIi3uAsDrAWukyBq8'
    SAMPLE_RANGE_NAME = 'Square Subs!A:G'
    df=get_spread_sheet(SAMPLE_SPREADSHEET_ID_input, SAMPLE_SPREADSHEET_ID_input)
    print(df.head(1))
