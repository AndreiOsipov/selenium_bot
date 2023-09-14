from wrappers import FieldWrapper, SmartClickFieldWrapper
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from google_sheets_parser import Client
import time
#передавать driver и user_info в методы записи, а не в init 
#чтобы можно было сделать один-единственный SiteWrapper на все потоки 
#каждыа
#исправить названия field, field_name ......
#
class PageWrapper:
    def _check_state(self, field: str):
        return self.current_state == self.usual_fields_wrappers[field].required_state or self.usual_fields_wrappers[field].required_state is None
    
    def _get_feild_value_from_person(self,person_info:Client, field:str):
        if field in person_info.table_data.keys():
            return person_info.table_data[field]

    def __init__(self,
                usual_fields_wrappers:dict[str,FieldWrapper] = None, 
                groupped_fields: dict[str,list[FieldWrapper]] = None,
                states:dict[str,str] = None) -> None:
        
        self.usual_fields_wrappers = usual_fields_wrappers
        self.groupped_fields = groupped_fields
        self.current_state = None
        self.states = states

    def _fill_groupped_fields(self, person_info: Client, web_waiter: WebDriverWait):
        for field_group in self.groupped_fields.keys():
            fields_values = person_info.table_data[field_group].split()
            for field, field_value in zip(self.groupped_fields[field_group], fields_values):
                field.input_into_field(web_waiter, field_value)

    def _fill_usually_fields(self, person_info: Client, web_waiter: WebDriverWait):
        for field in self.usual_fields_wrappers.keys():
            if self._check_state(field):
                value = self._get_feild_value_from_person(person_info, field)
                self.usual_fields_wrappers[field].input_into_field(web_waiter, value)

            if not(self.states is None) and person_info.table_data[field] in self.states.keys():
                self.current_state = self.states[person_info.table_data[field]]
            
    def fill_all_fields(self, person_info: Client, web_waiter: WebDriverWait):
        if self.usual_fields_wrappers:
            self._fill_usually_fields(person_info, web_waiter)
        if self.groupped_fields:
            self._fill_groupped_fields(person_info, web_waiter)
        
class MainPageWrapper(PageWrapper):
    def __init__(self, usual_fields_wrappers: dict[str, FieldWrapper] = None, groupped_fields: dict[str, list[FieldWrapper]] = None, states: dict[str, str] = None) -> None:
        super().__init__(usual_fields_wrappers, groupped_fields, states)
        self.cookie_btn = SmartClickFieldWrapper(By.ID, 'allowAllCookiesBtn')
        self.enter_elem = SmartClickFieldWrapper(By.XPATH, "//button[@class='btn btn-primary mb-2 sm-input-btn']")

    def go_to_login_page(self, web_waiter: WebDriverWait):
        self.cookie_btn.smart_clikc(web_waiter)
        self.enter_elem.smart_clikc(web_waiter)
        
class PersonalAreaPageWrapper(PageWrapper):
    def __init__(self, usual_fields_wrappers: dict[str, FieldWrapper] = None, groupped_fields: dict[str, list[FieldWrapper]] = None, states: dict[str, str] = None) -> None:
        super().__init__(usual_fields_wrappers, groupped_fields, states)
        self.questionnaire_transition = SmartClickFieldWrapper(By.XPATH, '//*[@id="dj-megamenu202"]/li[1]/a/span')

    def go_to_questionnaire_page(self, web_waiter: WebDriverWait):
        self.questionnaire_transition.smart_clikc(web_waiter)

class LoginPageWrapper(PageWrapper):
    def __init__(self, usual_fields_wrappers: dict[str, FieldWrapper]=None, groupped_fields: dict[str, list[FieldWrapper]]=None, states: dict[str, str] = None) -> None:
        super().__init__(usual_fields_wrappers, groupped_fields, states)
        self.login_click_element = SmartClickFieldWrapper(By.ID, 'loginFormSubmitButton')

    def try_login(self, web_waiter):
        while True:
            try: 
                self.login_click_element.smart_clikc(web_waiter)
                time.sleep(1)
            except: return

class FirstQuestionnairePageWrapper(PageWrapper):
    def __init__(self, usual_fields_wrappers: dict[str, FieldWrapper] = None, groupped_fields: dict[str, list[FieldWrapper]] = None, states: dict[str, str] = None) -> None:
        super().__init__(usual_fields_wrappers, groupped_fields, states)
        self.questionnaire_click_elem = SmartClickFieldWrapper(By.ID, "btnContinue")

    def click_to_btnContinue(self, web_waiter):
        self.questionnaire_click_elem.smart_clikc(web_waiter)

class BasicQuestPageWrapper(PageWrapper):
        def __init__(
            self,
            usual_fields_wrappers: dict[str, FieldWrapper] = None, 
            groupped_fields: dict[str, list[FieldWrapper]] = None, 
            states: dict[str, str] = None,
            xpath:str = None) -> None:
            super().__init__(usual_fields_wrappers, groupped_fields, states)
            
            self.xpath = xpath
            self.to_next_elem_click_field = SmartClickFieldWrapper(By.XPATH, self.xpath)

        def to_next_quest_page(self, web_waiter: WebDriverWait):
            self.to_next_elem_click_field.smart_clikc(web_waiter)

class ImagePafeWrapper(BasicQuestPageWrapper):
    def __init__(self,
        usual_fields_wrappers: dict[str, FieldWrapper] = None, 
        groupped_fields: dict[str, list[FieldWrapper]] = None, 
        states: dict[str, str] = None, 
        xpath: str = None) -> None:        
        super().__init__(usual_fields_wrappers, groupped_fields, states, xpath)

    def go_to_calendar_page(self, web_waiter:WebDriverWait):
        self.to_next_quest_page(web_waiter)
        for i in range(2):
            try:
                self.to_next_elem_click_field.alert_click()        
            except:
                pass
        

class CalendarPageWraper(PageWrapper):
    def __init__(self, 
        usual_fields_wrappers: dict[str, FieldWrapper] = None, 
        groupped_fields: dict[str, list[FieldWrapper]] = None, 
        states: dict[str, str] = None) -> None:
        
        super().__init__(usual_fields_wrappers, groupped_fields, states)
        self.btn_sbmit = SmartClickFieldWrapper(By.ID, 'btnSubmit')
        self.first_checkbox = SmartClickFieldWrapper(By.ID, 'previstoCheckbox1')
        self.second_checkbox = SmartClickFieldWrapper(By.ID, 'previstoCheckbox2')
        self.last_submit_btn = SmartClickFieldWrapper(By.ID, 'previstoSubmit')

    def submit_form(self, web_waiter: WebDriverWait):
        self.btn_sbmit.smart_clikc(web_waiter)
        self.first_checkbox.smart_clikc(web_waiter)
        self.second_checkbox.smart_clikc(web_waiter)
        self.last_submit_btn.smart_clikc(web_waiter)
