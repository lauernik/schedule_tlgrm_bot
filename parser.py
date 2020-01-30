import requests
from bs4 import BeautifulSoup


# Основная функция вызванная ботом
def schedule(group):
    value = code_group(group)
    if value:
        return page(value)


# Юзер агент для парсера
def user_agent():
    return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0'


# Запрос номера для введенного номера группы
def code_group(group):
    group_number = group
    response = requests.get(
        'https://urfu.ru/api/schedule/groups/suggest',
        params={'query': group_number},
        headers={'User-Agent': user_agent()}
        )
    json_response = response.json()
    # Проверяем, что группа введена корректно
    if json_response:
        if len(json_response['suggestions']) == 1:
            data_value = json_response['suggestions'][0]['data']
            return str(data_value)


# Парсим страницу
def page(value):
    page = requests.get(
        'https://urfu.ru/api/schedule/groups/lessons/'+value,
        headers={'User-Agent': user_agent()}
        )
    soup = BeautifulSoup(page.text, 'html.parser')
    table = tableDataText(soup.find('table', {'class': 'shedule-group-table'}))
    return table


# Парсим таблицу с расписанием в словарь
def tableDataText(table):
    sch_dict = {}  # Словарь в котором хранится расписание
    dict_keys = []  # Список с ключами - датами к словарю
    trs = table.find_all('tr')
    for tr in trs:
        row = []
        for td in tr.find_all(['b']):  # Ключ - день
            dict_keys.append(td.get_text(strip=True))
            sch_dict.update({dict_keys[-1]: []})
        # Название предмета
        row += [' '.join(td.get_text(strip=True).split())
                for td in tr.find_all(['dd'],)]
        # Время
        row += [td.get_text(strip=True) for td in tr.find_all(
            [],
            'shedule-weekday-time')]
        # Учитель
        row += [td.get_text(strip=True) for td in tr.find_all(
            ['span'], 'teacher')]
        # Кабинет
        row += [' '.join(td.get_text(strip=True).split()) for
                td in tr.find_all(['span'], 'cabinet')]
        # Добавляем в словарь
        sch_dict[dict_keys[-1]] += row
    return sch_dict
