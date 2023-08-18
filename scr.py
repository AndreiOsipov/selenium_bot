import json
import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from page_wrappers import (MainPAgeWrapper, LoginPageWrapper, PersonalAreaPageWrapper, FirstQuestionnairePageWrapper, BasicQuestPageWrapper)
from wrappers import (TextFieldWrapper, SelectFieldWrapper, DateFieldWrapper)
from google_sheets_parser import GoogleParser


class PortugalBot:
    def _get_driver(self):
        
        o = Options()
        o.add_experimental_option("detach", True)
        driver = webdriver.Chrome(options=o)
        driver.get(self.url)
        return driver

    def __init__(self, person_info) -> None:
        self.url = 'https://pedidodevistos.mne.gov.pt/VistosOnline/'
        self.driver = self._get_driver()
        self.person_info = person_info


        self.login_wrappers = {
            'логин от E-VISA':TextFieldWrapper('username', self.driver, 5, ''),
            'пароль от E-VISA':TextFieldWrapper('password',self.driver, 5, ''),
        }
        with open("international_codes.json", encoding='utf-8') as file:
            self.international_codes = json.load(file)
        with open("states.json", encoding='utf-8') as file:
            self.states = json.load(file)
        #доделать ветвеление
        #деделать выбор языка
        #
        self.first_questionnaire_wrappers = {
            'язык':SelectFieldWrapper('NONE', self.driver, 5,default_value='русский', international_codes=self.international_codes['LANG CODES'],field_id='language-select-d'),
            'страна проживания':SelectFieldWrapper('cb_pais_residencia', self.driver, 5,international_codes=self.international_codes['COUNTRY'],field_id='cb_question_21'),
            'тип паспорта':SelectFieldWrapper('cb_tipo_passaporte', self.driver, 5,international_codes=self.international_codes['PASSPORTS TYPES']),
            'намерены остаться':SelectFieldWrapper('cb_qt_dias', self.driver, 5,default_value='более 90',international_codes=self.international_codes["DAYS NUMBER"]),
            'намерены проживать вместе':SelectFieldWrapper('cb_estabelecer_residencia', self.driver, 5,default_value='нет',international_codes=self.international_codes['WANT LIVE TOGETHER']),
            'намерены остаться дней':SelectFieldWrapper('cb_pretende_ficar', self.driver, 5,default_value="более года",international_codes=self.international_codes["WANT STAY AFTER"]),
            'цель пребывания':SelectFieldWrapper('cb_motivo_estada_mais1ano', self.driver, 5,international_codes=self.international_codes['GOAL'],setup_states=self.states["GOALS"]),
            'каков вид работы':SelectFieldWrapper('cb_tipo_trabalho_mais1ano',self.driver,international_codes=self.international_codes["WORK TYPES"],required_state='work'),
            'укажите цель обучения':SelectFieldWrapper('cb_obj_estudo_mais1ano',self.driver,international_codes=self.international_codes["STUDY GOALS"],  required_state='study',setup_states=self.states["STUDY GOALS"]),
            'программа':SelectFieldWrapper('cb_ensino_superior',self.driver,international_codes=self.international_codes["PROGRAMS"], required_state='university')
        }

        self.identity_wrappers = {
            'посольство':SelectFieldWrapper('f0sf1',self.driver,5,default_value='москва',international_codes=self.international_codes["EMBASSY"]),
            'Фамилия до брака': TextFieldWrapper('f2',self.driver,5,filler_value='+'),
            'место рождения':TextFieldWrapper('f6',self.driver,5,filler_value='+'),
            'страна рождения':SelectFieldWrapper('f6sf1',self.driver,5,international_codes=self.international_codes['COUNTRY']),
            'гражданство при рождении':SelectFieldWrapper('f8',self.driver,5,international_codes=self.international_codes['COUNTRY']),
            'семейное положение':SelectFieldWrapper('f10',self.driver,5,international_codes=self.international_codes["FAMILY_STATE"]),
            'номер паспорта':TextFieldWrapper('f5',self.driver,5,'+'),
        }

        self.personal_data_wrappers = {
            'дата выдачи':DateFieldWrapper('f16',self.driver,5,5,default_value='0000/00/00'),
            'действителен до':DateFieldWrapper('f17',self.driver,5,5,default_value='0000/00/00'),
            'кем выдан':SelectFieldWrapper('f15',self.driver,5,international_codes=self.international_codes['COUNTRY']),
            'постоянное место жительства':TextFieldWrapper('f45',self.driver,5,filler_value='+'),
            'телефон':TextFieldWrapper('f46',self.driver,5,''),
        }

        self.trip_wrappers = {
            'текущая профессия':SelectFieldWrapper('f19',self.driver,5,international_codes=self.international_codes['PROFESSIONS']),
            'место работы / учебы':TextFieldWrapper('f20sf1',self.driver,5,filler_value='+'),
            'адрес / телефон места работы или учебы':TextFieldWrapper('f20sf2',self.driver,5,filler_value='+'),
            'дополнительная информация о цели пребывания':SelectFieldWrapper('f29sf2',self.driver,5,international_codes=self.international_codes['OTHER GOALS']),
            'еще информация':TextFieldWrapper('txtInfoMotEstada',self.driver,5,filler_value='+',default_value='Residence'),
            'граница первого въезда или транзитного маршрута':SelectFieldWrapper('f32',self.driver,5,international_codes=self.international_codes['COUNTRY'])
        }
        today = datetime.datetime.now()
        arrive_date = today + datetime.timedelta(days=180)

        self.visa_wrappers = {
            'дата приезда не из таблицы':DateFieldWrapper('f30',self.driver,5,5,default_value=f'{arrive_date.year}/{arrive_date.month}/{arrive_date.day}')
        }
        self.inviting_wrappers = {
            'контакты приглашающей стороны':SelectFieldWrapper('cmbReferencia',self.driver,5,international_codes=self.international_codes['INVITING'],setup_states=self.states["INVITING"]),
            'имя приглашающего лица или отеля':TextFieldWrapper('f34',self.driver,5,filler_value='+',required_state='individual'),
            'адрес приглашающего лица или отеля':TextFieldWrapper('f34sf2',self.driver,5,filler_value='+',required_state='individual'),
            'округ приглашающего лица или отеля':SelectFieldWrapper('f34sf5',self.driver,5,international_codes=self.international_codes['DISTRICTS'])
        }

        self.sponsors_wrappers = {
            'расходы заполняющего':[
                SelectFieldWrapper('cmbDespesasRequerente_1',self.driver,5,international_codes=self.international_codes["OWN MONEY"])
            ],
            'расходы со стороны спонсора':[
                SelectFieldWrapper('cmbDespesasPatrocinador_1',self.driver,5,international_codes=self.international_codes["SPONSORS MONEY"])
            ]
        }
        self.main_page_wrapper = MainPAgeWrapper(self.driver, {})
        self.personal_area_page_wrapper = PersonalAreaPageWrapper(self.driver, {})
        self.login_page = LoginPageWrapper(self.driver, self.person_info, self.login_wrappers)

        self.first_questionnaire_page = FirstQuestionnairePageWrapper(self.driver, self.person_info, usual_fields_wrappers=self.first_questionnaire_wrappers)

        self.identity_quest_page = BasicQuestPageWrapper(self.driver, self.person_info, self.identity_wrappers)
        self.personal_info_page = BasicQuestPageWrapper(self.driver, self.person_info, self.personal_data_wrappers)
        self.trip_page = BasicQuestPageWrapper(self.driver, self.person_info, self.trip_wrappers)
        self.visa_page = BasicQuestPageWrapper(self.driver,self.person_info, self.visa_wrappers)
        self.inviting_page = BasicQuestPageWrapper(self.driver, self.person_info, self.inviting_wrappers, self.sponsors_wrappers,states=self.states['INVITING'])


    def go(self):
        self.main_page_wrapper.go_to_login_page()

        self.login_page.fill_all_fields()
        self.login_page.try_login()

        self.personal_area_page_wrapper.go_to_questionnaire_page()
        time.sleep(30)
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
        print(f'логин прошел успешно')

def run():
    parser = GoogleParser()
    data = parser.get_all_user_data(3,4)
    bot = PortugalBot(data[0])
    bot.go()
    print('конец')


if __name__ == '__main__' :
    run()