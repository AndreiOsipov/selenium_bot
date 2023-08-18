from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

class GoogleParser:
    def __init__(self) -> None:
        self.creds = self._auth()
        self._spreadsheet_id = '11Rkcs1I2RP1ne3NxLq6uWOZnhvr-tjlhlcYfP750klc'
        self.service = build('sheets', 'v4', credentials=self.creds)

    def _auth(self):
        """Shows basic usage of the Sheets API.
        Prints values from a sample spreadsheet.
        """
        creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds
    def get_all_user_data(self, begin_row_number, end_row_number):
        sheet_api = self.service.spreadsheets()
        colls_names = sheet_api.values().get(spreadsheetId=self._spreadsheet_id,
                                    range='A1:BD1').execute()
        cools_names_values = colls_names.get('values', [])[0]
        # print(cools_names_values)
        # Call the Sheets API
        persons = []
        for row in range(begin_row_number, end_row_number):
            person_range = f'A{row}:BD{row}'
            person_info = sheet_api.values().get(spreadsheetId=self._spreadsheet_id,
                                    range=person_range).execute()
            person_info_values = person_info.get('values', [])[0]
            persons.append({coll_name: value for coll_name, value in zip(cools_names_values, person_info_values)})
        print('=='*20)
        print(persons)
        return persons

if __name__ == '__main__':
    parser = GoogleParser()
    parser.get_all_user_data(19,20)