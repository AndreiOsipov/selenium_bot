import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
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
    def __init__(self, name, default_value=None, required_state=None,setup_states=None, field_id=None) -> None:
        self.name = name
        self.required_state = required_state
        self.setup_states = setup_states
        self.default_value = default_value
        self.field_id = field_id

    @abstractmethod
    def input_into_field(self, web_waiter: WebDriverWait, value = None):
        "ввести значение в поле ввода"

class SmartClickFieldWrapper:
    def __init__(self, by: str, value: str ) -> None:
        self.by = by
        self.value = value    
    
    def smart_clikc(self, web_waiter: WebDriverWait):
        "подождать элемент и кликнуть на него"
        sleep_time = 2
        for i in range(3):
            try:
                el = web_waiter.until(EC.element_to_be_clickable((self.by, self.value)))
                el.click()
                return
            except:
                time.sleep(sleep_time)
                sleep_time *= 2

    def alert_click(self, web_waiter):
        alert = web_waiter.until(EC.alert_is_present())
        alert.accept()


class TextFieldWrapper(FieldWrapper):
    '''
    Обертка над текстовым полем
    ввод в текстовое поле:
    1) есть значение по умолчанию
    2) есть значение из таблицы
    3) поле обязательное(filler != "")
    '''
    def __init__(self, name, filler_value, default_value=None,required_state=None,) -> None:
        super().__init__(name, default_value, default_value,required_state)       
        self.filler_value = filler_value

    @try_execute
    def input_into_field(self,web_waiter:WebDriverWait, value=None):
        field = web_waiter.until(EC.element_to_be_clickable((By.NAME, self.name)))
        if self.default_value:
            field.send_keys(self.default_value)
        elif value and value != '':
            field.send_keys(value)
        else:
            field.send_keys(self.filler_value)
    
class DateFieldWrapper(FieldWrapper):
    '''
    обертка над полем даты
    default value -- нужно для поля "дата прилета"
    дата вводится если:
    1) если есть значение по умолчанию
    2) если дата -- не None и  не пустая строка
    '''
    def __init__(self, name, default_value = None) -> None:
        super().__init__(name, default_value, default_value)

    @try_execute
    def _input_into_field(self,web_waiter: WebDriverWait, str_date = None):
        field = web_waiter.until(EC.element_to_be_clickable((By.NAME, self.name)))
        if self.default_value:
            # print(f'default value: {self.default_date}')
            field.send_keys(self.default_value)
        else:
            if (str_date is None) or (str_date == ''):
                return
            date_elements = str_date.split('.')
            field.send_keys(f'{date_elements[2]}/{date_elements[1]}/{date_elements[0]}')
        # print('----------------дата введена----------------')
    
    
    def input_into_field(self,web_waiter: WebDriverWait, value=None):
        # print(f'попытка заполнить поле даты {self.name}')
        self._input_into_field(web_waiter, value)
        # ActionChains(driver).move_by_offset(150, 150).click()#необходимо увести курсор от места появления календаря
        #пересмотреть работу с alert
        #уникальные alert-обработчики
        try:
            alert = web_waiter.until(EC.alert_is_present())
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
    def __init__(self, name, default_value=None, required_state=None, setup_states=None,international_codes={},option_index=1,field_id=None,first=False) -> None:
        super().__init__(name, default_value, required_state, setup_states,field_id)
        self.option_index = option_index
        self.international_codes = international_codes
        self.first=first

    @try_execute
    def input_into_field(self, web_waiter: WebDriverWait, value=None):

        if self.first:
            self.set_first_value(web_waiter)
            return
        if self.field_id is None:
            field = web_waiter.until(EC.visibility_of_element_located((By.NAME, self.name)))
        else:
            field = web_waiter.until(EC.visibility_of_element_located((By.ID, self.field_id)))
        if value:
            Select(field).select_by_value(self.international_codes[value])        
        elif self.default_value:
            Select(field).select_by_value(self.international_codes[self.default_value])
    
    @try_execute
    def set_first_value(self, waiter: WebDriverWait):
        '''
        выберает первое свободное значение
        нужен для выбора времени записи в посольство
        работает, только если возможных вариантов больше 1, так как первый --- пустое время("----")
        сначала пытается выставить нужное время прием(так как одновременно записывается несколько человек)
        если не выйдет -- попытается выбрать первое свободное время
        '''
        field = waiter.until(EC.element_to_be_clickable((By.NAME, self.name)))
        available_options = list(field.find_elements(By.TAG_NAME, 'option'))
        if len(available_options)>self.option_index:
            value = available_options[self.option_index].get_attribute('value')
            Select(field).select_by_value(value)
        else:
            if len(available_options) > 1:
                value = available_options[1].get_attribute('value')
                Select(field).select_by_value(value)

class CalendarWrapper(FieldWrapper):
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
    def __init__(self, name, default_value=None, required_state=None, setup_states=None, field_id=None) -> None:
        self.name = name
        super().__init__(name,default_value,required_state,setup_states,field_id)
    
    def _get_all_free_days(self, web_Waiter: WebDriverWait):
        days = []
        trs = web_Waiter.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='calendar']/table/tbody/tr")))
        print(f'--------------------- всего календарных строк: {len(trs)} ---------------------')
        for tr in trs:
            all_days_in_tr = tr.find_elements(By.TAG_NAME, 'td')
            print(f'>>>> len of days in tr: {len(days)} ')
            days = tr.find_elements(By.CLASS_NAME, 'false')
            if len(days) != 0:
                return days
        return days
    
    def _get_all_free_dates_from_current_month(self, web_waiter: WebDriverWait):
        days = []
        trs = web_waiter.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='calendar']/table/tbody/tr")))
        after_urrent_day = False
        for tr in trs:
            all_days_in_tr = tr.find_elements(By.TAG_NAME, 'td')
            for day in all_days_in_tr:
                print(day.get_attribute('class'))
                if not(after_urrent_day):
                    if day.get_attribute('class') == 'day false selected today':
                        after_urrent_day = True
                        print('========== current day was found ==========')
                else:
                    if 'false' in day.get_attribute('class'):
                        days.append(day)
                        return days
        return days

    
    # @try_execute
    def input_into_field(self, web_waiter:WebDriverWait, value = None):
        calendar = web_waiter.until(EC.visibility_of_element_located((By.ID, 'f_trigger_c')))
        calendar.click()

        right_btn = None
        time.sleep(2)
        right_btn = web_waiter.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='calendar']/table/thead/tr[@class='headrow']/td[4]")))
        self._get_all_free_dates_from_current_month(web_waiter=web_waiter)
        right_btn.click()
        added_months_count = 0
        # print('-------------------------------------right btn нажата-------------------------------------')
        while added_months_count <= 5:
            days = self._get_all_free_days(web_waiter)
            if len(days)>0:
                days[0].click()
                time.sleep(1)
                return
            right_btn.click()
            added_months_count += 1