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
    
    cred_dict = {
  "type": "service_account",
  "project_id": "ots-square",
  "private_key_id": "973d953dcf6cfcfaaf389db30f975be259ca7dfb",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCvhNaNskqhXm9G\ncpWliJa4zuDY149MytiG3KjcGH9CBrfOqWQ27FrgISAFB8UzX3oxuUkkPiySLcoN\nO4sNuCuRqnOfyeov8IrecSDbrWl64dvVoT8cIe2Sqi5tN7SNys4JBIE8BAq1vvH1\nQkaMeLYHPa1gD1ga509xtQk49Jc0wgq0L7CvbA89Ei304MB+85RoI6so5mXlmQ0r\ni9bVUwfW9ppUxfkA+tXHciv3sdXbFC8FZ0GjSoTmxHPWf7PmqifMm5FErSnr43DM\ntQeomXjIL13aH8hByxZ5H9qUxy5EUMD4oBMxqsNpWlcx0eXft44PbDREsfrWgB5q\n6/V1h8etAgMBAAECggEAGwJhFdr62wwyKXAWkSuMrhG/zf6V4aZRXad1ILFwW9O2\n00mDz2PdtCHE0KFaekZWAnLVy4r5xuDe99xS0KCnq7nEIzGqJQhqBkL4YHW2Bp/c\n+Wnf0U9zRJ+Fl278DNnJjN+xl2+zyjYA+9HgE1u7/y9Bj8essi8oLYJDUg1pe0ej\nkEa8fPnTkr+sHlC33Hv4Shy5JNA7oZna5zutGeGtuCmbocuWSevgJzQMHN5SNwjG\ny3WdJTPuutvToeMzbdQ7uKlDY8cZdZ72/5JhbXoyPQ4pql/qa8ipd+Xd9q6YNWH6\nPiZF3+AW/SAIiCkFTD630mPKCSKZstYvKpTkA/ufbQKBgQDgRJ74RaJHO2ZmZqLf\nwLPiAoy9qGuKc+6o6YA1SEpQ9J9kppMJGS/p8jK44afWWwKR7473WpXR4FGr4sJd\njJ5l98n92cBEjG/gtuHYx+FcUsCC8greL1pDv81PKIqVZUXhR6yYNNsDc7bAMzia\nEwFELp/KMVFvDlM4eLK3UjY8awKBgQDIWnAiC1nSpz8C7f7Eqb4duCOGRqUi1CTi\nFdy2ZxCX+F2pmZtXIVWk6E5rERp+5QwpDEpAAg8/IEZ/nUJ+tkACYtgFq8uI+zlD\n0UCj05rmsEN0hLAK5scZBibpoph3KVzf1x2rHL7sbWA6kMxICTpI76h8IDSVsjIT\nl82zMBiSRwKBgHzsfIjbcQuwwNelsHBnDUyGExPKby0OaxDYELydahgyS19rklft\nGc19RlfKCw3SYFoeUUrjwLTJ+XR/ubkWjV1La87lrr4AZImOFbwFizk8N1Q5s2gU\nhHlcq+a+NIQHh6d3n2KhfqYrnM7vOUZJ89ihCA0+75enKSA5y4NmXiPFAoGAfZB4\ncE2u2J+qlPp1TemX1eZelTvXKNHN38eV0NcdBjFI+g7j1SJ2G2jgJKfOdDK2gU9L\nhXwE9CoVJMt5LhKoYRZzjnJRmCLii8cr/MCUdvmG/RJfhiWGJ/+8CXa2mQ/aPgsC\ndAgK+/+8bFftP0RRO/6/GDPS4PKSAceEykVdUOcCgYEAwZliVwH8OOeGXaGRUOTA\nGBg+9ZnyvobQFysUM6EZlAA76LVGQVjsF9nWXSijdNQjYR+inMft77FxfzA3Sdm6\ndjBLVSoQXj0ZV9pwDnERa8k0tWEvRHq0ae9ZxfbHvep0zDRABWgHxAXDdHWmz26t\netqhZvDTkiftou+vtC0hte0=\n-----END PRIVATE KEY-----\n",
  "client_email": "timmins@ots-square.iam.gserviceaccount.com",
  "client_id": "118350745945740133931",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/timmins%40ots-square.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}


    creds = Credentials.from_service_account_info(cred_dict, scopes=scopes)
    print(creds)

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
