from typing import Dict, Any

AUTH_KEY = "YTVmOWE2MzctNzllYy00YmYzLTg3MjUtM2I3NDA5MTZiMjNiOmVkZWNiYTE4LWQ4NmEtNDFhNC1iOTQ5LTE2NjI1OTlmNjVlOA=="


def ai_resume_processing(input_dict, auth_key: str, departments):
    import json
    from gigachat import GigaChat

    processed_dict = {}
    processed_dict['competencies'] = input_dict['competencies']
    processed_dict['about'] = input_dict['about']

    resume = str(input_dict)
    softskills = "Коммуникативность, Менеджмент, Лидерские качества, Критическое мышление, Креативность, Стрессоустойчивость, Адаптивность, Тайм-менеджмент, Клиентоориентированность, Нетворкинг, Инициативность, Целеустремленность, Усидчивость, Грамотность"

    with GigaChat(model='GigaChat', credentials=auth_key, verify_ssl_certs=False) as giga:
        response1 = giga.chat(f"""Выдели в резюме навыки и личностные качества человека в виде строки (например, JavaScript, HTML, общительный). Выводи данные в json по шаблону:
                            "hard_skills": [
                                    *фигурная скоба*Тут перечисли хард скиллы в следующем формате: навык: кол-во лет (если не указано, то "Упомянуто")*фигурная скоба*],
                            "soft_skills": [Выбери из следующих в соответствии с резюме: {softskills})],
                            "hobby": ["...", "..."],
                            "tags": "[Все, что в hard_skills и в soft_skills, но в виде списка в квадратных скобках]", 

                            Списки помещай только в квадратные скобки. Проследи, чтобы каждый список открывался и закрывался. Ты должен указать все хард скиллы и софт скиллы из резюме и прописать теги.

                            Ты должен извлечь информацию строго из полученного резюме, не придумывай свое.

                            Вот резюме: {resume}""")

    with GigaChat(model='GigaChat-Pro', credentials=auth_key, verify_ssl_certs=False) as giga_pro:
        response2 = giga_pro.chat(f"""Есть следующий ответ:
                            {response1.choices[0].message.content}
                            Добавить к этому ответу (сохраняя структуру json) рекомендацию, в какой отдел лучше отправить этого сотрудника (выбирай из следующих: {departments}) по следующему шаблону:
                            "recommendation": "Тут пропиши название отдела из указанных"

                            Ты не должен писать ничего, кроме структуры json файла.""")

    answer = response2.choices[0].message.content
    answer_json = json.loads(answer.replace('```', '').replace('json', ''))

    input_dict.pop('competencies', None)
    input_dict.pop('about', None)

    output_dict = {**input_dict, **answer_json}

    return output_dict


def ai_process_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
    input_dict = {
        "competencies": user_data.get("work_experience", "") + " " + user_data.get("education", ""),
        "about": user_data.get("about", ""),
        **user_data
    }

    return ai_resume_processing(input_dict, AUTH_KEY, DEPARTMENTS)