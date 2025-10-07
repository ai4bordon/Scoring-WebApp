import streamlit as st
from openai import OpenAI
from parse_hh import get_html, extract_vacancy_data, extract_resume_data

# Проверка наличия API ключа
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    if not api_key or api_key == "your-openai-api-key-here":
        st.error("❌ OpenAI API ключ не настроен!")
        st.info("Пожалуйста, добавьте ваш API ключ в файл `.streamlit/secrets.toml`")
        st.info("Инструкции по настройке см. в файле `README_SECRETS.md`")
        st.stop()
    client = OpenAI(api_key=api_key)
except Exception as e:
    st.error("❌ Ошибка загрузки секретов!")
    st.info("Создайте файл `.streamlit/secrets.toml` на основе шаблона `secrets.toml.example`")
    st.info(f"Детальная ошибка: {e}")
    st.stop()

SYSTEM_PROMPT = """
Проскорь кандидата, насколько он подходит для данной вакансии.

Сначала напиши короткий анализ, который будет пояснять оценку.
Отдельно оцени качество заполнения резюме (понятно ли, с какими задачами сталкивался кандидат и каким образом их решал?). Эта оценка должна учитываться при выставлении финальной оценки - нам важно нанимать таких кандидатов, которые могут рассказать про свою работу
Потом представь результат в виде оценки от 1 до 10.
""".strip()

def request_gpt(system_prompt, user_prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1000,
        temperature=0,
    )
    return response.choices[0].message.content

# UI
st.title('Scoring WebApp')

job_description = st.text_area('Введите ссылку на вакансию')
cv = st.text_area('Введите ссылку на резюме')

if st.button("Проанализировать соответствие"):
    with st.spinner("Парсим данные и отправляем в GPT..."):
        try:
            job_response = get_html(job_description)
            resume_response = get_html(cv)

            # Проверяем, что получили Response объекты, а не строки
            if hasattr(job_response, 'text'):
                job_html = job_response.text
            else:
                job_html = str(job_response)

            if hasattr(resume_response, 'text'):
                resume_html = resume_response.text
            else:
                resume_html = str(resume_response)

            job_text = extract_vacancy_data(job_response)
            resume_text = extract_resume_data(resume_response)

            prompt = f"# ВАКАНСИЯ\n{job_text}\n\n# РЕЗЮМЕ\n{resume_text}"
            response = request_gpt(SYSTEM_PROMPT, prompt)

            st.subheader("📊 Результат анализа:")
            st.markdown(response)

        except Exception as e:
            st.error(f"Произошла ошибка: {e}")
