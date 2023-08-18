import time
import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from abc import ABC, abstractmethod

def try_execute(input_into_field_func):
        
        def wrapper(*args):
            for i in range(6):
                try:
                    input_into_field_func(*args)
                    return
                except:
                    time.sleep(3)
        return wrapper


class FieldWrapper(ABC):
    def __init__(self, name, driver, wait_time,default_value=None, required_state=None,setup_states=None, field_id=None) -> None:
        self.name = name
        self.driver = driver
        self.wait_time = wait_time
        self.required_state = required_state
        self.setup_states = setup_states
        self.default_value = default_value
        self.field_id = field_id
        self.waiter = WebDriverWait(self.driver, self.wait_time)
    # @property
    # @abstractmethod
    # def wait_time():
    #     "время ожидания"

    # @property
    # @abstractmethod
    # def name():
    #     "имя поля"
    # @property
    # @abstractmethod
    # def required_state():
    #     "необходимое состояние страницы"
    # @property
    # @abstractmethod
    # def setup_states():
    #     "словарь состояний в которые может попасть страница"
    @abstractmethod
    def input_into_field(value = None):
        "ввести значение в поле ввода"

class TextFieldWrapper(FieldWrapper):
    '''
    Обертка над текстовым полем
    ввод в текстовое поле:
    1) есть значение по умолчанию
    2) есть значение из таблицы
    3) поле обязательное(filler != "")
    '''
    def __init__(self, name,driver,wait_time, filler_value, default_value=None,required_state=None) -> None:
        super().__init__(name,driver,wait_time, default_value, default_value,required_state)       
        self.filler_value = filler_value

    @try_execute
    def input_into_field(self, value=None):
        field = self.waiter.until(EC.element_to_be_clickable((By.NAME, self.name)))
        if self.default_value:
            field.send_keys(self.default_value)
        elif value and value != '':
            field.send_keys(value)
        elif self.filler_value != '':
            field.send_keys(self.filler_value)
        return

    def get_international_code(self, value):
        return None
    
class DateFieldWrapper(FieldWrapper):
    '''
    обертка над полем даты
    default value -- нужно для поля "дата прилета"
    дата вводится если:
    1) если есть значение по умолчанию
    2) если дата -- не None и  не пустая строка
    '''
    def __init__(self, name, driver, wait_time, alert_wait_time, default_value = None) -> None:
        super().__init__(name,driver,wait_time, default_value, default_value)
        self.alertwaiter = WebDriverWait(self.driver,alert_wait_time)

    @try_execute
    def _input_into_field(self, str_date = None):

        field = self.waiter.until(EC.element_to_be_clickable((By.NAME, self.name)))
        if self.default_value:
            # print(f'default value: {self.default_date}')
            field.send_keys(self.default_value)
        else:
            if (str_date is None) or (str_date == ''):
                return
            date_elements = str_date.split('.')
            field.send_keys(f'{date_elements[2]}/{date_elements[1]}/{date_elements[0]}')
        # print('----------------дата введена----------------')
    
    
    def input_into_field(self, str_date=None):
        # print(f'попытка заполнить поле даты {self.name}')
        self._input_into_field(str_date)
        ActionChains(self.driver).move_by_offset(150, 150).click()#необходимо увести курсор от места появления календаря
        
        for i in range(6):
            try:
                alert = self.alertwaiter.until(EC.alert_is_present())
                alert.accept()
                self._input_into_field(str_date)
                ActionChains(self.driver).move_by_offset(150, 150).click()
                time.sleep(1)
                # print(f'-----------alert was detected-----------')
            except:
                return
        try:
                alert = self.alertwaiter.until(EC.alert_is_present())
                alert.accept()
        except:
            return
        
class SelectFieldWrapper(FieldWrapper):
    '''
    обертка нал полем выбора
    выбор происходит по значению value у поля на странице
    поэтому нужны international_codes -- словарь словарей из json-а
    выбор происходит так:
    1) если value -- не None оно и вводится
    2) если default_value -- вводится оно
    если ввод провалится, будет выведена ошибка и бот пойдет дальше
    '''
    def __init__(self, name, driver, wait_time=5, default_value=None, required_state=None, setup_states=None,international_codes={},option_index=1,field_id=None) -> None:
        super().__init__(name, driver, wait_time, default_value, required_state, setup_states,field_id)
        self.option_index = option_index
        self.international_codes = international_codes
        
    @try_execute
    def input_into_field(self, value=None):
        if self.field_id is None:
            field = self.waiter.until(EC.visibility_of_element_located((By.NAME, self.name)))
        else:
            field = self.waiter.until(EC.visibility_of_element_located((By.ID, self.field_id)))
        if value:
            Select(field).select_by_value(self.international_codes[value])
        else:
            if self.default_value:
                    Select(field).select_by_value(self.international_codes[self.default_value])
    @try_execute
    def set_first_value(self):
        '''
        выберает первое свободное значение
        нужен для выбора времени записи в посольство
        работает, только если возможных вариантов больше 1, так как первый --- пустое время("----")
        сначала пытается выставить нужное время прием(так как одновременно записывается несколько человек)
        если не выйдет -- попытается выбрать первое свободное время
        '''
        field = self.waiter.until(EC.element_to_be_clickable((By.NAME, self.name)))
        available_options = list(field.find_elements(By.TAG_NAME, 'option'))
        if len(available_options)>self.option_index:
            value = available_options[self.option_index].get_attribute('value')
            Select(field).select_by_value(value)
            return
        else:
            if len(available_options) > 1:
                value = available_options[1].get_attribute('value')
                Select(field).select_by_value(value)
                return

class CalendarWrapper:
    '''
    обертка над последнем каледнарем для выбора даты записи в посольство
    логика поиска:
    1) найти календарь и кликнуть на него
    2) подождать 2 секунда пока он окончательно подгрузиться
    3) найти на нем кнопку со стрелками вправо
    4) нажать на нее 6 раз, чтобы сдвинуть месяц
    5) найти все стркои календаря по xpath
    6) пробежаться по ним и найти строку в которой будут не занятые дни
    7) кликнуть на незанятый день
    8) подождать 1 секунду, чтобы календатрь нормально закрылся
    '''
    def __init__(self, name) -> None:
        self.name = name

    def _get_all_free_days(self, waiter, driver: WebDriver):
        days = []
        trs = driver.find_elements(By.XPATH, "//div[@class='calendar']/table/tbody/tr")
        print(f'--------------------- всего календарных строк: {len(trs)} ---------------------')
        for tr in trs:
            all_days_in_tr = tr.find_elements(By.TAG_NAME, 'td')
            print(f'>>>> len of days in tr: {len(days)} ')
            days = tr.find_elements(By.CLASS_NAME, 'false')
            if len(days) != 0:
                return days
        return days
    
    def _get_all_free_dates_from_current_month(self, driver: WebDriver):
        days = []
        trs = driver.find_elements(By.XPATH, "//div[@class='calendar']/table/tbody/tr")
        after_urrent_day = False
        for tr in trs:
            all_days_in_tr = tr.find_elements(By.TAG_NAME, 'td')
            
            for day in all_days_in_tr:
                print(day.get_attribute('class'))
                if not(after_urrent_day):
                    if day.get_attribute('class') == 'day false selected today':
                        after_urrent_day
                        print('========== current day was found ==========')
                else:
                    if 'false' in day.get_attribute('class'):
                        days.append(day)
                        return days
        return days

    
    # @try_execute
    def search_date(self, waiter:WebDriverWait, driver: WebDriver, choised_date: datetime.date = None):
        print('===================method searche_date was called===================')
        # опредилиться с форматом даты
        # определиться с тем, как эту дату составлять из сайта
        calendar = waiter.until(EC.visibility_of_element_located((By.ID, 'f_trigger_c')))
        calendar.click()
        # print('10 seconds for move calendar')
        # time.sleep(10)
        print(f'-------------------------------------calendar was clicked-------------------------------------')
        
        right_btn = None
        time.sleep(2)
        
        right_btn = waiter.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='calendar']/table/thead/tr[@class='headrow']/td[4]")))
        self._get_all_free_dates_from_current_month(driver)
        right_btn.click()
        
        added_months_count = 0
        print('-------------------------------------right btn нажата-------------------------------------')
        
        while added_months_count <= 5:
            
            days = self._get_all_free_days(waiter, driver)

            if len(days)>0:
                days[0].click()

                time.sleep(1)
                return

            right_btn.click()
            added_months_count += 1