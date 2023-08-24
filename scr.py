import json
import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from page_wrappers import (MainPAgeWrapper, LoginPageWrapper, PersonalAreaPageWrapper, FirstQuestionnairePageWrapper, BasicQuestPageWrapper,ImagePafeWrapper,CalendarPageWraper)
from wrappers import (TextFieldWrapper, SelectFieldWrapper, DateFieldWrapper, CalendarWrapper)
from google_sheets_parser import ClientsBuilder, Client


class PortugalBot:
    def _init_json_files(self):
        with open("international_codes.json", encoding='utf-8') as file:
            self.international_codes = json.load(file)
        with open("states.json", encoding='utf-8') as file:
            self.states = json.load(file)

    def _get_driver(self):
        o = Options()
        o.add_experimental_option("detach", True)
        driver = webdriver.Chrome(options=o)
        driver.get(self.url)
        return driver

    def __init__(self, person_info: list[Client]) -> None:
        self.url = 'https://pedidodevistos.mne.gov.pt/VistosOnline/'
        self.driver = self._get_driver()
        self._init_json_files()

        self.person_info = person_info
        self.login_wrappers = {
            'логин от E-VISA':TextFieldWrapper('username', self.driver,''),
            'пароль от E-VISA':TextFieldWrapper('password',self.driver,''),
        }
        first_questionnaire_wrappers = {
            'язык':SelectFieldWrapper('NONE', self.driver,default_value='русский', international_codes=self.international_codes['LANG CODES'],field_id='language-select-d'),
            'страна проживания':SelectFieldWrapper('cb_pais_residencia', self.driver,international_codes=self.international_codes['COUNTRY'],field_id='cb_question_21'),
            'тип паспорта':SelectFieldWrapper('cb_tipo_passaporte', self.driver,international_codes=self.international_codes['PASSPORTS TYPES']),
            'намерены остаться':SelectFieldWrapper('cb_qt_dias', self.driver,default_value='более 90',international_codes=self.international_codes["DAYS NUMBER"]),
            'намерены проживать вместе':SelectFieldWrapper('cb_estabelecer_residencia', self.driver,default_value='нет',international_codes=self.international_codes['WANT LIVE TOGETHER']),
            'намерены остаться дней':SelectFieldWrapper('cb_pretende_ficar', self.driver,default_value="более года",international_codes=self.international_codes["WANT STAY AFTER"]),
            'цель пребывания':SelectFieldWrapper('cb_motivo_estada_mais1ano', self.driver,international_codes=self.international_codes['GOAL'],setup_states=self.states["GOALS"]),
            'каков вид работы':SelectFieldWrapper('cb_tipo_trabalho_mais1ano',self.driver,international_codes=self.international_codes["WORK TYPES"],required_state='work'),
            'укажите цель обучения':SelectFieldWrapper('cb_obj_estudo_mais1ano',self.driver,international_codes=self.international_codes["STUDY GOALS"],  required_state='study',setup_states=self.states["STUDY GOALS"]),
            'программа':SelectFieldWrapper('cb_ensino_superior',self.driver,international_codes=self.international_codes["PROGRAMS"], required_state='university')
        }

        identity_wrappers = {
            'посольство':SelectFieldWrapper('f0sf1',self.driver,default_value='москва',international_codes=self.international_codes["EMBASSY"]),
            'Фамилия до брака': TextFieldWrapper('f2',self.driver,filler_value='+'),
            'место рождения':TextFieldWrapper('f6',self.driver,filler_value='+'),
            'страна рождения':SelectFieldWrapper('f6sf1',self.driver,international_codes=self.international_codes['COUNTRY'],default_value='россия'),
            'гражданство при рождении':SelectFieldWrapper('f8',self.driver,international_codes=self.international_codes['COUNTRY'],default_value='россия'),
            'семейное положение':SelectFieldWrapper('f10',self.driver,international_codes=self.international_codes["FAMILY_STATE"],default_value='холост/не замужем'),
            'номер паспорта':TextFieldWrapper('f5',self.driver,'+'),
            'фамилия родителя/опекуна':TextFieldWrapper('txtApelidoPaternal',self.driver,filler_value=''),
            'имя родителя/опекуна':TextFieldWrapper('txtNomePaternal',self.driver,filler_value=''),
            'адрес родителя/опекуна':TextFieldWrapper('txtEnderecoPaternal',self.driver,filler_value=''),
            'телефон родителя/опекуна':TextFieldWrapper('txtTelefonePaternal',self.driver,filler_value=''),
            'e-mail родителя/опекуна':TextFieldWrapper('txtEmailPaternal',self.driver,filler_value=''),
            'гражданство родителя/опекуна':SelectFieldWrapper('cmbNacionalidadePaternal',self.driver,international_codes=self.international_codes['COUNTRY'])
        }

        personal_data_wrappers = {
            'дата выдачи':DateFieldWrapper('f16',self.driver),
            'действителен до':DateFieldWrapper('f17',self.driver),
            'кем выдан':SelectFieldWrapper('f15',self.driver,international_codes=self.international_codes['COUNTRY'],default_value='россия'),
            'постоянное место жительства':TextFieldWrapper('f45',self.driver,filler_value='+'),
            'телефон':TextFieldWrapper('f46',self.driver,'0'),
        }

        trip_wrappers = {
            'текущая профессия':SelectFieldWrapper('f19',self.driver,international_codes=self.international_codes['PROFESSIONS']),
            'место работы / учебы':TextFieldWrapper('f20sf1',self.driver,filler_value='+'),
            'адрес / телефон места работы или учебы':TextFieldWrapper('f20sf2',self.driver,filler_value='+'),
            'дополнительные цели поездки':SelectFieldWrapper('f29sf2',self.driver,international_codes=self.international_codes['OTHER GOALS']),
            'дополнительная информация о цели пребывания':TextFieldWrapper('txtInfoMotEstada',self.driver,filler_value='+',default_value='Residence'),
            'граница первого въезда или транзитного маршрута':SelectFieldWrapper('f32',self.driver,international_codes=self.international_codes['COUNTRY'])
        }
        today = datetime.datetime.now()
        arrive_date = today + datetime.timedelta(days=180)

        visa_wrappers = {
            'дата приезда не из таблицы':DateFieldWrapper('f30',self.driver,default_value=f'{arrive_date.year}/{arrive_date.month}/{arrive_date.day}')
        }
        inviting_wrappers = {
            'контакты приглашающей стороны':SelectFieldWrapper('cmbReferencia',self.driver,international_codes=self.international_codes['INVITING'],setup_states=self.states["INVITING"]),
            'имя приглашающего лица или отеля':TextFieldWrapper('f34',self.driver,filler_value='+',required_state='individual'),
            'адрес приглашающего лица или отеля':TextFieldWrapper('f34sf2',self.driver,filler_value='+',required_state='individual'),
            'округ приглашающего лица или отеля':SelectFieldWrapper('f34sf5',self.driver,international_codes=self.international_codes['DISTRICTS'],default_value='Lisboa',required_state='individual'),
            'телефон приглашающего лица или отеля': TextFieldWrapper('f34sf3',self.driver,filler_value='+',required_state='individual'),
            'e-mail приглашающего лица или отеля':TextFieldWrapper('f34sf4',self.driver,filler_value='+',required_state='individual'),
            'название приглашающей организации':TextFieldWrapper('txtNomeEmpresa',self.driver,filler_value='+',required_state='company'),
            'адрес приглашающей организации':TextFieldWrapper('txtEnderecoEmpresa',self.driver,filler_value='+',required_state='company'),
            'округ приглашающей организации':SelectFieldWrapper('cmbConcelhoEmpresa',self.driver,international_codes=self.international_codes['DISTRICTS'],default_value='Lisboa',required_state='company'),
            'телефон приглашающей организации':TextFieldWrapper('txtTelefoneEmpresa',self.driver,filler_value='+',required_state='company'),
            'адрес электронной почты приглашающей организации':TextFieldWrapper('txtEmailEmpresa',self.driver,filler_value='+',required_state='company'),
        }

        sponsors_wrappers = {
            'расходы заполняющего':[
                SelectFieldWrapper('cmbDespesasRequerente_1',self.driver,international_codes=self.international_codes["OWN MONEY"],default_value='наличные деньги')
            ],
            'расходы со стороны спонсора':[
                SelectFieldWrapper('cmbDespesasPatrocinador_1',self.driver,international_codes=self.international_codes["SPONSORS MONEY"],default_value='средства')
            ]
        }
        images_wrappers = {
            'photo_path':TextFieldWrapper(name='foto',driver=self.driver,wait_time=5,filler_value=''),        
            'attachment_path_1':TextFieldWrapper(name='file1',driver=self.driver,filler_value=''),
            'attachment_path_2':TextFieldWrapper(name='file2',driver=self.driver,filler_value=''),
            'attachment_path_3':TextFieldWrapper(name='file3',driver=self.driver,filler_value=''),
            'attachment_path_4':TextFieldWrapper(name='file4',driver=self.driver,filler_value='')
            }
        calendar_page_wrpappers = {
            'calendar':CalendarWrapper(name='f_trigger_c',driver=self.driver),
            'time':SelectFieldWrapper(name='cmbPeriodo',driver=self.driver,first=True)
        }

        self.main_page_wrapper = MainPAgeWrapper(self.driver, {})
        self.personal_area_page_wrapper = PersonalAreaPageWrapper(self.driver, {})
        self.login_page = LoginPageWrapper(self.driver, self.person_info, self.login_wrappers)

        self.first_questionnaire_page = FirstQuestionnairePageWrapper(self.driver, self.person_info, usual_fields_wrappers=first_questionnaire_wrappers)

        self.identity_quest_page = BasicQuestPageWrapper(self.driver, self.person_info, identity_wrappers)
        self.personal_info_page = BasicQuestPageWrapper(self.driver, self.person_info, personal_data_wrappers)
        self.trip_page = BasicQuestPageWrapper(self.driver, self.person_info, trip_wrappers)
        self.visa_page = BasicQuestPageWrapper(self.driver,self.person_info, visa_wrappers)
        self.inviting_page = BasicQuestPageWrapper(self.driver, self.person_info, inviting_wrappers, sponsors_wrappers,states=self.states['INVITING'])
        self.image_page = ImagePafeWrapper(self.driver, self.person_info, images_wrappers)
        self.calendar_page = CalendarPageWraper(self.driver, self.person_info,calendar_page_wrpappers)
    def go(self):
        self.main_page_wrapper.go_to_login_page()

        self.login_page.fill_all_fields()
        self.login_page.try_login()

        self.personal_area_page_wrapper.go_to_questionnaire_page()
        # time.sleep(30)
        self.first_questionnaire_page.fill_all_fields()
        self.first_questionnaire_page.click_to_btnContinue()
        
        self.identity_quest_page.fill_all_fields()
        self.identity_quest_page.to_next_quest_page('//*[@id="tblIdentificacao"]/tbody/tr[18]/td[2]/a')
        self.personal_info_page.fill_all_fields()
        self.personal_info_page.to_next_quest_page('//*[@id="tblDadosViagem"]/tbody/tr[8]/td[2]/a')
        self.trip_page.fill_all_fields()
        self.trip_page.to_next_quest_page('//*[@id="tblDadosContacto"]/tbody/tr[8]/td[2]/a')
        self.visa_page.fill_all_fields()
        self.visa_page.to_next_quest_page('//*[@id="tblFinanciamento"]/tbody/tr[4]/td[2]/a')
        self.inviting_page.fill_all_fields()
        self.inviting_page.to_next_quest_page('//*[@id="td_prox_tab5"]/a')
        self.image_page.fill_all_fields()
        self.image_page.go_to_calendar_page('//*[@id="btnSubmit"]')
        self.calendar_page.fill_all_fields()
        self.calendar_page.submit_form()
        # print(f'логин прошел успешно')

def run():
    clients_builder = ClientsBuilder()
    clients = clients_builder.build_clients(3, 5)
    print(clients[0])
    bot = PortugalBot(clients[0])
    bot.go()
    print('конец')

if __name__ == '__main__' :
    run()