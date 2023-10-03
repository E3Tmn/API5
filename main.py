import requests
import itertools
import pprint
from statistics import mean


def predict_rub_salary(response):
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
    return {'vacancies_processed': len(salary), "average_salary": int(mean(salary))}


def get_vacancies(top_languages):
    statistic_vacancies = {}
    for language in top_languages:
        for page in itertools.count(0):
            url = 'https://api.hh.ru/vacancies/'
            payload = {
                "User-Agent": '???',
                "text": f'Программист {language}',
                "area": 1,
                "page": page,
                "period": 30,
                'only_with_salary': True
            }
            response = requests.get(url, params=payload)
            response.raise_for_status()
            vacancies = response.json()
            if page + 1 == vacancies['pages']:
                break
            medium_salary = {'vacancies_found': vacancies["found"]} | predict_rub_salary(vacancies)
        statistic_vacancies.setdefault(language, medium_salary)
    return statistic_vacancies


def main():
    top_languages = ['Javascript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'CSS', 'C#', 'C', 'GO']
    number_of_vacancies = get_vacancies(top_languages)
    pprint.pprint(number_of_vacancies)
if __name__ == "__main__":
    main()
