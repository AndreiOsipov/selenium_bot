from wrappers import FieldWrapper
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

class PageWrapper:
    def __init__(self,
                driver,
                person_info: dict,
                usual_fields_wrappers:dict[str,FieldWrapper] = None, 
                groupped_fields: dict[str,list[FieldWrapper]] = None,
                states:dict[str,str] = None) -> None:
        
        self.driver = driver
        self.usual_fields_wrappers = usual_fields_wrappers
        self.groupped_fields = groupped_fields
        self.person_info = person_info
        self.current_state = None
        self.states = states

    def _fill_groupped_fields(self):
        for field_group in self.groupped_fields.keys():
            fields_values = self.person_info[field_group].split()
            for field, field_value in zip(self.groupped_fields[field_group], fields_values):
                field.input_into_field(field_value)

    def _fill_usually_fields(self):
        for field in self.usual_fields_wrappers.keys():
            if self.current_state == self.usual_fields_wrappers[field].required_state or self.usual_fields_wrappers[field].required_state is None:
                if field in  self.person_info.keys():    
                    self.usual_fields_wrappers[field].input_into_field(self.person_info[field])
                else:
                    self.usual_fields_wrappers[field].input_into_field()
            if not(self.states is None) and self.person_info[field] in self.states.keys():
                self.current_state = self.states[self.person_info[field]]
            
    def fill_all_fields(self):
        if self.usual_fields_wrappers:
            self._fill_usually_fields()
        if self.groupped_fields:
            self._fill_groupped_fields()
        
class MainPAgeWrapper(PageWrapper):
    def __init__(self, driver, person_info: dict, usual_fields_wrappers: dict[str, FieldWrapper] = None, groupped_fields: dict[str, list[FieldWrapper]] = None, states: dict[str, str] = None) -> None:
        super().__init__(driver, person_info, usual_fields_wrappers, groupped_fields, states)
    
    def go_to_login_page(self):
        waiter = WebDriverWait(self.driver, 5)
        cookie = waiter.until(EC.element_to_be_clickable((By.ID, 'allowAllCookiesBtn')))
        cookie.click()
        enter_elem = waiter.until(EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn-primary mb-2 sm-input-btn']")))
        enter_elem.click()

class PersonalAreaPageWrapper(PageWrapper):
    def __init__(self, driver, person_info: dict, usual_fields_wrappers: dict[str, FieldWrapper] = None, groupped_fields: dict[str, list[FieldWrapper]] = None, states: dict[str, str] = None) -> None:
        super().__init__(driver, person_info, usual_fields_wrappers, groupped_fields, states)
    
    def go_to_questionnaire_page(self):
        waiter = WebDriverWait(self.driver, 5)
        questionnaire_elem = waiter.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="dj-megamenu202"]/li[1]/a/span')))
        questionnaire_elem.click()
        
class LoginPageWrapper(PageWrapper):
    def __init__(self, driver, person_info: dict, usual_fields_wrappers: dict[str, FieldWrapper]=None, groupped_fields: dict[str, list[FieldWrapper]]=None, states: dict[str, str] = None) -> None:
        super().__init__(driver, person_info, usual_fields_wrappers, groupped_fields, states)
    
    def try_login(self):
        while True:
            waiter = WebDriverWait(self.driver, 5)
            try: 
                waiter.until(EC.presence_of_element_located((By.ID, 'loginFormSubmitButton')))
            except: return

class FirstQuestionnairePageWrapper(PageWrapper):
    def __init__(self, driver, person_info: dict, usual_fields_wrappers: dict[str, FieldWrapper] = None, groupped_fields: dict[str, list[FieldWrapper]] = None, states: dict[str, str] = None) -> None:
        super().__init__(driver, person_info, usual_fields_wrappers, groupped_fields, states)

    def click_to_btnContinue(self):
        waiter = WebDriverWait(self.driver, 5)
        questionnaire_elem = waiter.until(EC.element_to_be_clickable((By.ID, "btnContinue")))
        questionnaire_elem.click()

class BasicQuestPageWrapper(PageWrapper):
        def __init__(self, driver, person_info: dict, usual_fields_wrappers: dict[str, FieldWrapper] = None, groupped_fields: dict[str, list[FieldWrapper]] = None, states: dict[str, str] = None) -> None:
            super().__init__(driver, person_info, usual_fields_wrappers, groupped_fields, states)

        def to_next_quest_page(self, path):
            waiter = WebDriverWait(self.driver, 5)
            to_next_elem = waiter.until(EC.element_to_be_clickable((By.XPATH, path)))
            to_next_elem.click()