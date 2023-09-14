from collections.abc import Callable, Iterable, Mapping
import json
import time
import datetime
import threading
from typing import Any

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from page_wrappers import (MainPageWrapper, LoginPageWrapper, PersonalAreaPageWrapper, FirstQuestionnairePageWrapper, BasicQuestPageWrapper,ImagePafeWrapper,CalendarPageWraper)
from wrappers import (TextFieldWrapper, SelectFieldWrapper, DateFieldWrapper, CalendarWrapper)
from google_sheets_parser import ClientsBuilder, Client

#TODO
#сделать класс для получения driver
#чтобы убрать передачу драйвера по всей программе
#таким образом, любой элемент, которому реально нужен драйвер сможет его запросить САМ
#тогда можно будет закиунть инициализацию страниц в отдельный модуль без передачи туда driver


class PortugalSiteWrapper:
    '''
    - представляет собой обертку над сайтом, сосьтоит из оберток над страницами
    - каждая обертка над страницей, в свою очередь, состоит из оберток над web-элементами
    - экземпляр этого класса, как и экземпляры всех оберток, которые он создает является обзим для всех потоков
    - благодаря тому, что не содержит потоко-зависимых элементов
    - потокозависимые части: person_info, webwaiter т.к. работает правило: один поток -- одна запись
    - person_info, webwaiter передаются в методы fill_all() и методы go_to()
    - пока что, для всех web-оберток используется один и тот же web_waiter 
    '''
    def _init_main_page(self):
        self.main_page_wrapper = MainPageWrapper()
    
    def _init_personal_area_page(self):
        self.personal_area_page_wrapper = PersonalAreaPageWrapper()

    def _init_login_page(self):
        self.login_wrappers = {
            'логин от E-VISA':TextFieldWrapper('username',''),
            'пароль от E-VISA':TextFieldWrapper('password',''),
        }
        self.login_page = LoginPageWrapper(self.login_wrappers)

    def _init_first_questionnaire_page(self, international_codes: dict, states: dict):
        first_questionnaire_wrappers = {
            'язык':SelectFieldWrapper('NONE', default_value='русский', international_codes=international_codes['LANG CODES'],field_id='language-select-d'),
            'страна проживания':SelectFieldWrapper('cb_pais_residencia', international_codes=international_codes['COUNTRY'],field_id='cb_question_21'),
            'тип паспорта':SelectFieldWrapper('cb_tipo_passaporte', international_codes=international_codes['PASSPORTS TYPES']),
            'намерены остаться':SelectFieldWrapper('cb_qt_dias', default_value='более 90',international_codes=international_codes["DAYS NUMBER"]),
            'намерены проживать вместе':SelectFieldWrapper('cb_estabelecer_residencia', default_value='нет',international_codes=international_codes['WANT LIVE TOGETHER']),
            'намерены остаться дней':SelectFieldWrapper('cb_pretende_ficar', default_value="более года",international_codes=international_codes["WANT STAY AFTER"]),
            'цель пребывания':SelectFieldWrapper('cb_motivo_estada_mais1ano', international_codes=international_codes['GOAL'],setup_states=states["GOALS"]),
            'каков вид работы':SelectFieldWrapper('cb_tipo_trabalho_mais1ano',international_codes=international_codes["WORK TYPES"],required_state='work'),
            'укажите цель обучения':SelectFieldWrapper('cb_obj_estudo_mais1ano',international_codes=international_codes["STUDY GOALS"],  required_state='study',setup_states=states["STUDY GOALS"]),
            'программа':SelectFieldWrapper('cb_ensino_superior',international_codes=international_codes["PROGRAMS"], required_state='university')
        }
        self.first_questionnaire_page = FirstQuestionnairePageWrapper(usual_fields_wrappers=first_questionnaire_wrappers)
    
    def _init_identity_page(self, international_codes: dict):
        identity_wrappers = {
            'посольство':SelectFieldWrapper('f0sf1',default_value='москва',international_codes=international_codes["EMBASSY"]),
            'Фамилия до брака': TextFieldWrapper('f2',filler_value='+'),
            'место рождения':TextFieldWrapper('f6',filler_value='+'),
            'страна рождения':SelectFieldWrapper('f6sf1',international_codes=international_codes['COUNTRY'],default_value='россия'),
            'гражданство при рождении':SelectFieldWrapper('f8',international_codes=international_codes['COUNTRY'],default_value='россия'),
            'семейное положение':SelectFieldWrapper('f10',international_codes=international_codes["FAMILY_STATE"],default_value='холост/не замужем'),
            'номер паспорта':TextFieldWrapper('f5','+'),
            'фамилия родителя/опекуна':TextFieldWrapper('txtApelidoPaternal',filler_value=''),
            'имя родителя/опекуна':TextFieldWrapper('txtNomePaternal',filler_value=''),
            'адрес родителя/опекуна':TextFieldWrapper('txtEnderecoPaternal',filler_value=''),
            'телефон родителя/опекуна':TextFieldWrapper('txtTelefonePaternal',filler_value=''),
            'e-mail родителя/опекуна':TextFieldWrapper('txtEmailPaternal',filler_value=''),
            'гражданство родителя/опекуна':SelectFieldWrapper('cmbNacionalidadePaternal',international_codes=international_codes['COUNTRY'])
        }
        self.identity_quest_page = BasicQuestPageWrapper(identity_wrappers)
    
    def _init_personal_data_page(self, international_codes: dict):
        personal_data_wrappers = {
            'дата выдачи':DateFieldWrapper('f16'),
            'действителен до':DateFieldWrapper('f17'),
            'кем выдан':SelectFieldWrapper('f15',international_codes=international_codes['COUNTRY'],default_value='россия'),
            'постоянное место жительства':TextFieldWrapper('f45',filler_value='+'),
            'телефон':TextFieldWrapper('f46','0'),
        }
        self.personal_info_page = BasicQuestPageWrapper(personal_data_wrappers)

    def _init_trip_page(self, international_codes: dict):
        trip_wrappers = {
            'текущая профессия':SelectFieldWrapper('f19',international_codes=international_codes['PROFESSIONS']),
            'место работы / учебы':TextFieldWrapper('f20sf1',filler_value='+'),
            'адрес / телефон места работы или учебы':TextFieldWrapper('f20sf2',filler_value='+'),
            'дополнительные цели поездки':SelectFieldWrapper('f29sf2',international_codes=international_codes['OTHER GOALS']),
            'дополнительная информация о цели пребывания':TextFieldWrapper('txtInfoMotEstada',filler_value='+',default_value='Residence'),
            'граница первого въезда или транзитного маршрута':SelectFieldWrapper('f32',international_codes=international_codes['COUNTRY'])
        }
        self.trip_page = BasicQuestPageWrapper(trip_wrappers)
    
    def _init_visa_page(self):
        today = datetime.datetime.now()
        arrive_date = today + datetime.timedelta(days=180)
        visa_wrappers = {
            'дата приезда не из таблицы':DateFieldWrapper('f30',default_value=f'{arrive_date.year}/{arrive_date.month}/{arrive_date.day}')
        }
        self.visa_page = BasicQuestPageWrapper(visa_wrappers)
    
    def _init_inviting_page(self, international_codes: dict, states: dict):
        inviting_wrappers = {
            'контакты приглашающей стороны':SelectFieldWrapper('cmbReferencia',international_codes=international_codes['INVITING'],setup_states=states["INVITING"]),
            'имя приглашающего лица или отеля':TextFieldWrapper('f34',filler_value='+',required_state='individual'),
            'адрес приглашающего лица или отеля':TextFieldWrapper('f34sf2',filler_value='+',required_state='individual'),
            'округ приглашающего лица или отеля':SelectFieldWrapper('f34sf5',international_codes=international_codes['DISTRICTS'],default_value='Lisboa',required_state='individual'),
            'телефон приглашающего лица или отеля': TextFieldWrapper('f34sf3',filler_value='+',required_state='individual'),
            'e-mail приглашающего лица или отеля':TextFieldWrapper('f34sf4',filler_value='+',required_state='individual'),
            'название приглашающей организации':TextFieldWrapper('txtNomeEmpresa',filler_value='+',required_state='company'),
            'адрес приглашающей организации':TextFieldWrapper('txtEnderecoEmpresa',filler_value='+',required_state='company'),
            'округ приглашающей организации':SelectFieldWrapper('cmbConcelhoEmpresa',international_codes=international_codes['DISTRICTS'],default_value='Lisboa',required_state='company'),
            'телефон приглашающей организации':TextFieldWrapper('txtTelefoneEmpresa',filler_value='+',required_state='company'),
            'адрес электронной почты приглашающей организации':TextFieldWrapper('txtEmailEmpresa',filler_value='+',required_state='company'),
        }
        sponsors_wrappers = {
            'расходы заполняющего':[
                SelectFieldWrapper('cmbDespesasRequerente_1',international_codes=international_codes["OWN MONEY"],default_value='наличные деньги')
            ],
            'расходы со стороны спонсора':[
                SelectFieldWrapper('cmbDespesasPatrocinador_1',international_codes=international_codes["SPONSORS MONEY"],default_value='средства')
            ]
        }
        self.inviting_page = BasicQuestPageWrapper(inviting_wrappers, sponsors_wrappers,states=states['INVITING'])

    def _init_images_page(self):
        images_wrappers = {
            'photo_path':TextFieldWrapper(name='foto',filler_value=''),        
            'attachment_path_1':TextFieldWrapper(name='file1',filler_value=''),
            'attachment_path_2':TextFieldWrapper(name='file2',filler_value=''),
            'attachment_path_3':TextFieldWrapper(name='file3',filler_value=''),
            'attachment_path_4':TextFieldWrapper(name='file4',filler_value='')
            }
        self.image_page = ImagePafeWrapper(images_wrappers)

    def _init_calendar_page(self):
        calendar_page_wrpappers = {
            'calendar':CalendarWrapper(name='f_trigger_c'),
            'time':SelectFieldWrapper(name='cmbPeriodo',first=True)
        }
        self.calendar_page = CalendarPageWraper(calendar_page_wrpappers)

    def __init__(self, international_codes: dict, states: dict):
        self._init_main_page()
        self._init_personal_area_page()
        self._init_login_page()
        self._init_first_questionnaire_page(international_codes, states)
        self._init_personal_data_page(international_codes)
        self._init_trip_page(international_codes)
        self._init_visa_page()
        self._init_inviting_page(international_codes, states)
        self._init_images_page()
        self._init_calendar_page()

    def make_an_appointment(self, client: Client, web_waiter: WebDriverWait):
        '''
        - производит запись клиента (client) с помощью web_waiter 
        '''
        self.main_page_wrapper.go_to_login_page(web_waiter)

        self.login_page.fill_all_fields(client, web_waiter)
        self.login_page.try_login(web_waiter)

        self.personal_area_page_wrapper.go_to_questionnaire_page(web_waiter)

        self.first_questionnaire_page.fill_all_fields(client, web_waiter)
        self.first_questionnaire_page.click_to_btnContinue(web_waiter)
        
        self.identity_quest_page.fill_all_fields(client, web_waiter)
        self.identity_quest_page.to_next_quest_page(web_waiter)
        self.personal_info_page.fill_all_fields(client, web_waiter)
        self.personal_info_page.to_next_quest_page(web_waiter)
        self.trip_page.fill_all_fields(client, web_waiter)
        self.trip_page.to_next_quest_page(web_waiter)
        self.visa_page.fill_all_fields(client, web_waiter)
        self.visa_page.to_next_quest_page(web_waiter)
        self.inviting_page.fill_all_fields(client, web_waiter)
        self.inviting_page.to_next_quest_page(web_waiter)
        self.image_page.fill_all_fields(client, web_waiter)
        self.image_page.go_to_calendar_page(client)
        self.calendar_page.fill_all_fields(client, web_waiter)
        self.calendar_page.submit_form(web_waiter)


class PortugalBot:
    '''
    - является связующим звеном между Client и PortugalSiteWrapper
    - при инициализациии создает driver и WebDriverWaite
    - запускает метод make_an_appointment() обертки PortugalSiteWrapper
    '''

    def _get_driver(self):
        o = Options()
        o.add_experimental_option("detach", True)
        driver = webdriver.Chrome(options=o)
        driver.get(self.url)
        return driver

    def __init__(self, person_info: Client, site_wrapper: PortugalSiteWrapper) -> None:
        self.url = 'https://pedidodevistos.mne.gov.pt/VistosOnline/'
        self.driver = self._get_driver()
        self.web_waiter = WebDriverWait(self.driver,5.0)
        self.person_info = person_info
        self.portugal_site = site_wrapper
    
    def make_an_appointment(self):
        self.portugal_site.make_an_appointment(self.person_info, self.web_waiter)

def get_international_codes():
    with open("international_codes.json", encoding='utf-8') as file:
        international_codes = json.load(file)
    return international_codes

def get_states():
    with open("states.json", encoding='utf-8') as file:
        states = json.load(file)
    return states

class BotThread(threading.Thread):
    def __init__(self, person_info: Client, site_wrapper: PortugalSiteWrapper, thread_name: str = None) -> None:
        super().__init__(name=thread_name)
        self.person_info = person_info
        self.site_wrapper = site_wrapper
        self.bot = PortugalBot(self.person_info, self.site_wrapper)

    def run(self):
        self.bot.make_an_appointment()

def run(start_row, end_row):
    clients_builder = ClientsBuilder()
    clients = clients_builder.build_clients(start_row, end_row)
    bot_threads:list[BotThread] = []
    
    international_codes = get_international_codes()
    states = get_states()
    site_wrapper = PortugalSiteWrapper(international_codes, states)


    for i in range(len(clients)):
        site_wrapper = PortugalSiteWrapper(international_codes, states)
        bot_threads.append(BotThread(clients[i],site_wrapper, f'thread number {i}'))

    for bot_thread in bot_threads:
        bot_thread.start()

    # print(clients[0])
    # bot = PortugalBot(clients[0])
    # bot.go()
    # print('конец')

if __name__ == '__main__' :
    run(3,7)