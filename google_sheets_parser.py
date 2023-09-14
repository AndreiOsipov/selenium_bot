import os.path
import os
import io

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive']

class GoogleAPILogin:
    def __init__(self) -> None:
        # self.creds = self._auth()
        pass
        # drive_parser = GoogleDriveParser(self.creds)
    def get_auth_creds(self):
        """возвращает разрешения на использование гугл-таблиц и гугл-диска"""
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
                flow = InstalledAppFlow.from_client_secrets_file(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'credentials.json'), SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds

# If modifying these scopes, delete the file token.json.

class GoogleDriveParser:
    def __init__(self, creds) -> None:
        self.creds = creds
        self.google_drive_service = build('drive', 'v3', credentials=self.creds)
    
    def get_resource_id_from_url(self, url:str):
        if url == '' or url == None or not('=' in url):
            return None
        return url[url.index('=')+1:]
    
    def download_file(self, file_id, file_ext: str):
        if file_id == '' or file_id is None:
            return None
        
        request = self.google_drive_service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        file_name = f'{file_id}.{file_ext}'
        this_dir = os.path.dirname(os.path.realpath(__file__))
        current_dir = os.path.join(this_dir, 'passports')
        
        full_file_name = os.path.join(current_dir, file_name) 
        with open(full_file_name, 'wb') as local_file:
            local_file.write(file.getvalue())
        return full_file_name

class GoogleSheetsParser:
    def __init__(self, creds) -> None:
        self.creds = creds
        self.service = build('sheets', 'v4', credentials=self.creds)
        self._spreadsheet_id = '11Rkcs1I2RP1ne3NxLq6uWOZnhvr-tjlhlcYfP750klc'
        
    def get_all_user_info(self, row_number: int) -> list[dict[str,str]]:
        sheet_api = self.service.spreadsheets()
        colls_names = sheet_api.values().get(spreadsheetId=self._spreadsheet_id,range='A1:BE1').execute()
        cools_names_values = colls_names.get('values', [])[0]

        person_range = f'A{row_number}:BE{row_number}'

        person_info = sheet_api.values().get(spreadsheetId=self._spreadsheet_id,range=person_range).execute()
        person_info = person_info.get('values', [])
        if len(person_info) > 0:
            person_info_values = person_info[0]
            return {coll_name: value for coll_name, value in zip(cools_names_values, person_info_values)}
        return {coll_name: '' for coll_name in cools_names_values}
    
class Client:
    def __init__(self, table_data: dict[str, str]) -> None:
        
        self.table_data = table_data
    
    def __repr__(self) -> str:
        repr_str = super().__repr__()
        return repr_str+'\n'+self.__str__()+'\n'

    def __str__(self) -> str:
        printing_str = ''
        lines = 4
        current_line_number = 0
        for key in self.table_data.keys():
            if current_line_number == lines:
                return printing_str+'......'
            printing_str += f'{key} | {self.table_data[key]}\n'
            current_line_number += 1
        return printing_str

class ClientsBuilder:
    def __init__(self) -> None:
        pass

    def build_clients(self, begin_row_number, end_row_number):
        clients:list[Client] = []
        google_api_login = GoogleAPILogin()
        creds = google_api_login.get_auth_creds()

        google_sheets_parser = GoogleSheetsParser(creds)
        google_drive_parser = GoogleDriveParser(creds)

        for row in range(begin_row_number, end_row_number):
            client_table_data = google_sheets_parser.get_all_user_info(row)
            if client_table_data['already_registred'] != 'FALSE':
                continue
            
            url_to_photo = client_table_data['фотография паспортного образца']
            photo_path = google_drive_parser.download_file(google_drive_parser.get_resource_id_from_url(url_to_photo), 'jpg')
            client_table_data['photo_path'] = photo_path

            client = Client(client_table_data)
            for i in range(4):
                url_to_attachment = client_table_data[f'вложение № {i+1}']

                attachment_path = google_drive_parser.download_file(google_drive_parser.get_resource_id_from_url(url_to_attachment), 'pdf')
                client_table_data[f'attachment_path_{i}'] = attachment_path
            clients.append(client)
        return clients

if __name__ == '__main__':
    cl_builder = ClientsBuilder()
    clients = cl_builder.build_clients(2, 20)
    print(clients)