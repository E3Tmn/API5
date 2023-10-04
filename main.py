import requests
import itertools
from collections import Counter
from terminaltables import AsciiTable
import os
from dotenv import load_dotenv


def hh_predict_rub_salary(response):
    salary = []
    for item in response['items']:
        salary_from = item["salary"]['from']
        salary_to = item["salary"]['to']
        if item["salary"]["currency"] != 'RUR':
            continue
        elif salary_from and salary_to:
            salary.append((salary_from + salary_to)/2)
        elif salary_from and not salary_to:
            salary.append(salary_from * 1.2)
        else:
            salary.append(salary_to * 0.8)
    return {'vacancies_processed': len(salary), "average_salary": sum(salary)}


def hh_get_vacancies(top_languages):
    statistic_vacancies = {}
    for language in top_languages:
        forecast = Counter()
        for page in itertools.count(0):
            url = 'https://api.hh.ru/vacancies/'
            payload = {
                "text": f'Программист {language}',
                "per_page": 100,
                "area": 1,
                "page": page,
                "period": 30,
                'only_with_salary': True
            }
            response = requests.get(url, params=payload)
            response.raise_for_status()
            vacancies = response.json()
            forecast += Counter(hh_predict_rub_salary(vacancies))
            if page + 1 == vacancies['pages']:
                break
        forecast["average_salary"] = int(forecast["average_salary"] / forecast["vacancies_processed"])
        medium_salary = {'vacancies_found': vacancies["found"]} | forecast
        statistic_vacancies.setdefault(language, medium_salary)
    return statistic_vacancies


def sj_predict_rub_salary(vacancies):
    salary = []
    for item in vacancies['objects']:
        payment_from = item['payment_from']
        payment_to = item['payment_to']
        if item["currency"] != 'rub':
            return None
        elif payment_from and payment_to:
            salary.append((payment_from + payment_to)/2)
        elif payment_from and not payment_to:
            salary.append(payment_from * 1.2)
        else:
            salary.append(payment_to * 0.8)
    return {'vacancies_processed': len(salary), "average_salary": sum(salary)}


def sj_get_vacancies(top_languages):
    statistic_vacancies = {}
    for language in top_languages:
        forecast = Counter()
        for page in range(5):
            url = 'https://api.superjob.ru/2.0/vacancies/'
            headers = {
                'X-Api-App-Id': os.environ["SUPERJOB_KEY"]
            }
            payload = {
                'town': 'Москва',
                'catalogues': 48,
                'keyword': f"программист {language}",
                'no_agreement': 1,
                'period': 30,
                "page": page,
                'count': 100
            }
            response = requests.get(url, params=payload, headers=headers)
            response.raise_for_status()
            vacancies = response.json()
            forecast += Counter(sj_predict_rub_salary(response.json()))
        if forecast:
            forecast["average_salary"] = int(forecast["average_salary"] / forecast["vacancies_processed"])
        medium_salary = {'vacancies_found': vacancies['total']} | forecast
        statistic_vacancies.setdefault(language, medium_salary)
    return statistic_vacancies


def print_table(title, statistic_vacancies):
    table_data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for counter, vacancy in enumerate(statistic_vacancies):
            table_data.append([vacancy])
            for key, value in statistic_vacancies[vacancy].items():
                table_data[counter + 1].append(value)
    table = AsciiTable(table_data, title)
    print(table.table)
    return


def main():
    load_dotenv()
    secret_key = os.environ["SUPERJOB_KEY"]
    top_languages = ['Javascript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'CSS', 'C#', 'C', 'GO']
    print_table('HeadHunter Moscow', hh_get_vacancies(top_languages))
    print_table('SuperJob Moscow', sj_get_vacancies(top_languages))


if __name__ == "__main__":
    main()
