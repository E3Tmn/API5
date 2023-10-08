import requests
import itertools
from collections import Counter
from terminaltables import AsciiTable
import os
from dotenv import load_dotenv



def get_array_salaries(salary_from, salary_to):
    if salary_from and salary_to:
        average_salary = (salary_from + salary_to)/2
    elif salary_from and not salary_to:
        average_salary = salary_from * 1.2
    else:
        average_salary = salary_to * 0.8
    return average_salary


def hh_predict_rub_salary(response):
    salaries = []
    for vacancy in response['items']:
        if vacancy["salary"]:
            salary_from = vacancy["salary"]['from']
            salary_to = vacancy["salary"]['to']
            if vacancy["salary"]["currency"] != 'RUR':
                continue
            else:
                salaries.append(get_array_salaries(salary_from, salary_to))
    return (len(salaries), sum(salaries))


def hh_get_vacancies_statistics(top_languages):
    statistic_vacancies = {}
    number_of_elements = 100
    region_id = 1
    number_of_days = 30
    for language in top_languages:
        forecast = Counter()
        for page_number in itertools.count(0):
            url = 'https://api.hh.ru/vacancies/'
            payload = {
                "text": f'Программист {language}',
                "per_page": number_of_elements,
                "area": region_id,
                "page": page_number,
                "period": number_of_days
            }
            response = requests.get(url, params=payload)
            response.raise_for_status()
            vacancies = response.json()
            salary_statistics = hh_predict_rub_salary(vacancies)
            forecast += Counter({'vacancies_processed': salary_statistics[0], "average_salary": salary_statistics[1]})
            if page_number + 1 == vacancies['pages']:
                break
        if forecast:
            forecast["average_salary"] = int(forecast["average_salary"] / forecast["vacancies_processed"])
        medium_salary = {'vacancies_found': vacancies["found"]} | forecast
        statistic_vacancies.setdefault(language, medium_salary)
    return statistic_vacancies


def sj_predict_rub_salary(vacancies):
    salaries = []
    for item in vacancies['objects']:
        payment_from = item['payment_from']
        payment_to = item['payment_to']
        if item["currency"] != 'rub':
            return None
        else:
            salaries.append(get_array_salaries(payment_from, payment_to))
    return (len(salaries), sum(salaries))


def sj_get_vacancies_statistics(top_languages, secret_key):
    statistic_vacancies = {}
    number_of_elements = 100
    catalog_number = 48
    salary_type_id = 1
    number_of_days = 30
    max_number_of_pages = 5
    for language in top_languages:
        forecast = Counter()
        for page_number in range(max_number_of_pages):
            url = 'https://api.superjob.ru/2.0/vacancies/'
            headers = {
                'X-Api-App-Id': secret_key
            }
            payload = {
                'town': 'Москва',
                'catalogues': catalog_number,
                'keyword': f"программист {language}",
                'no_agreement': salary_type_id,
                'period': number_of_days,
                "page": page_number,
                'count': number_of_elements
            }
            response = requests.get(url, params=payload, headers=headers)
            response.raise_for_status()
            vacancies = response.json()
            salary_statistics = sj_predict_rub_salary(vacancies)
            forecast += Counter({'vacancies_processed': salary_statistics[0], "average_salary": salary_statistics[1]})
        if forecast:
            forecast["average_salary"] = int(forecast["average_salary"] / forecast["vacancies_processed"])
        medium_salary = {'vacancies_found': vacancies['total']} | forecast
        statistic_vacancies.setdefault(language, medium_salary)
    return statistic_vacancies


def print_table(title, statistic_vacancies):
    table = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for counter, vacancy in enumerate(statistic_vacancies):
            table.append([vacancy])
            for requirement, parameter in statistic_vacancies[vacancy].items():
                table[counter + 1].append(parameter)
    table = AsciiTable(table, title)
    print(table.table)
    return


def main():
    load_dotenv()
    secret_key = os.environ["SUPERJOB_KEY"]
    top_languages = ['Javascript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'CSS', 'C#', 'C', 'GO']
    print_table('HeadHunter Moscow', hh_get_vacancies_statistics(top_languages))
    print_table('SuperJob Moscow', sj_get_vacancies_statistics(top_languages, secret_key))


if __name__ == "__main__":
    main()
