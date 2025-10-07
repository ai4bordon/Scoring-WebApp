import requests
from bs4 import BeautifulSoup
import logging

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_html(url):
    """
    Получает HTML-содержимое страницы с улучшенной обработкой ошибок

    Args:
        url (str): URL страницы для парсинга

    Returns:
        requests.Response: Объект ответа

    Raises:
        requests.RequestException: При ошибке HTTP-запроса
        ValueError: При недействительном URL
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL должен быть непустой строкой")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        logger.info(f"Загрузка страницы: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Проверка на корректный HTML
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' not in content_type:
            logger.warning(f"Неожиданный Content-Type: {content_type}")

        return response

    except requests.exceptions.Timeout:
        logger.error(f"Таймаут при загрузке {url}")
        raise requests.RequestException(f"Таймаут при загрузке страницы {url}")
    except requests.exceptions.ConnectionError:
        logger.error(f"Ошибка соединения для {url}")
        raise requests.RequestException(f"Ошибка соединения при загрузке {url}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP ошибка для {url}: {e}")
        raise requests.RequestException(f"HTTP ошибка при загрузке {url}: {e}")

def extract_vacancy_data(html):
    """
    Извлекает данные вакансии из HTML с улучшенной надежностью

    Args:
        html (requests.Response): HTML-ответ страницы вакансии

    Returns:
        str: Данные вакансии в формате Markdown
    """
    soup = BeautifulSoup(html.text, 'html.parser')

    def safe_text(selector, attrs=None, fallback_selectors=None):
        """
        Безопасное извлечение текста с альтернативными селекторами

        Args:
            selector (str): CSS-селектор
            attrs (dict): Атрибуты селектора
            fallback_selectors (list): Список альтернативных селекторов

        Returns:
            str: Извлеченный текст или "Не найдено"
        """
        # Основной селектор
        el = soup.find(selector, attrs or {})
        if el:
            return el.text.strip()

        # Альтернативные селекторы
        if fallback_selectors:
            for fallback in fallback_selectors:
                if isinstance(fallback, dict):
                    el = soup.find(fallback.get('tag', selector), fallback.get('attrs', {}))
                else:
                    el = soup.find(fallback)
                if el:
                    return el.text.strip()

        return "Не найдено"

    # Извлечение данных с альтернативными селекторами
    title = safe_text('h1', fallback_selectors=[
        {'tag': 'h1', 'attrs': {'class': 'bloko-header-1'}},
        {'tag': 'title'},
        'h1'
    ])

    salary = safe_text('span', {'data-qa': 'vacancy-salary'}, fallback_selectors=[
        {'tag': 'div', 'attrs': {'class': 'vacancy-salary'}},
        {'tag': 'span', 'attrs': {'class': 'bloko-header-2'}},
        'span'
    ])

    company = safe_text('a', {'data-qa': 'vacancy-company-name'}, fallback_selectors=[
        {'tag': 'span', 'attrs': {'data-qa': 'vacancy-company-name'}},
        {'tag': 'a', 'attrs': {'class': 'vacancy-company-name'}},
        'a'
    ])

    # Извлечение описания с альтернативными селекторами
    description = (soup.find('div', {'data-qa': 'vacancy-description'}) or
                  soup.find('div', {'class': 'vacancy-description'}) or
                  soup.find('div', {'id': 'vacancy-description'}))

    description_text = "Описание не найдено"
    if description:
        description_text = description.get_text(separator="\n").strip()

    # Формирование Markdown с проверками
    markdown = f"# {title}\n\n"

    if company != "Не найдено":
        markdown += f"**Компания:** {company}\n\n"

    if salary != "Не найдено":
        markdown += f"**Зарплата:** {salary}\n\n"

    markdown += f"## Описание\n\n{description_text}"

    return markdown.strip()

def extract_resume_data(html):
    """
    Извлекает данные резюме из HTML с улучшенной надежностью

    Args:
        html (requests.Response): HTML-ответ страницы резюме

    Returns:
        str: Данные резюме в формате Markdown
    """
    soup = BeautifulSoup(html.text, 'html.parser')

    def safe_text(selector, attrs=None, fallback_selectors=None):
        """
        Безопасное извлечение текста с альтернативными селекторами
        """
        # Основной селектор
        el = soup.find(selector, attrs or {})
        if el:
            return el.text.strip()

        # Альтернативные селекторы
        if fallback_selectors:
            for fallback in fallback_selectors:
                if isinstance(fallback, dict):
                    el = soup.find(fallback.get('tag', selector), fallback.get('attrs', {}))
                else:
                    el = soup.find(fallback)
                if el:
                    return el.text.strip()

        return "Не найдено"

    # Извлечение основных данных с альтернативными селекторами
    name = safe_text('h2', {'data-qa': 'bloko-header-1'}, fallback_selectors=[
        {'tag': 'h1', 'attrs': {'data-qa': 'bloko-header-1'}},
        {'tag': 'h2', 'attrs': {'class': 'bloko-header-1'}},
        'h1', 'h2'
    ])

    gender_age = safe_text('p', fallback_selectors=[
        {'tag': 'span', 'attrs': {'class': 'resume-personal-gender-age'}},
        'p'
    ])

    location = safe_text('span', {'data-qa': 'resume-personal-address'}, fallback_selectors=[
        {'tag': 'div', 'attrs': {'data-qa': 'resume-personal-address'}},
        {'tag': 'span', 'attrs': {'class': 'resume-personal-address'}},
        'span'
    ])

    job_title = safe_text('span', {'data-qa': 'resume-block-title-position'}, fallback_selectors=[
        {'tag': 'div', 'attrs': {'data-qa': 'resume-block-title-position'}},
        {'tag': 'h3', 'attrs': {'class': 'bloko-header-2'}},
        'span'
    ])

    job_status = safe_text('span', {'data-qa': 'job-search-status'}, fallback_selectors=[
        {'tag': 'div', 'attrs': {'data-qa': 'job-search-status'}},
        {'tag': 'span', 'attrs': {'class': 'job-search-status'}},
        'span'
    ])

    # Извлечение опыта работы с улучшенной обработкой ошибок
    experiences = []
    experience_selectors = [
        {'tag': 'div', 'attrs': {'data-qa': 'resume-block-experience'}},
        {'tag': 'div', 'attrs': {'class': 'resume-block-experience'}},
        {'tag': 'div', 'attrs': {'id': 'resume-block-experience'}}
    ]

    experience_section = None
    for selector in experience_selectors:
        experience_section = soup.find(selector.get('tag'), selector.get('attrs', {}))
        if experience_section:
            break

    if experience_section:
        experience_items = experience_section.find_all(['div', 'section'], class_=lambda x: x and 'resume-block-item' in str(x))
        if not experience_items:
            # Альтернативный поиск элементов опыта
            experience_items = experience_section.find_all('div', class_=lambda x: x and ('gap' in str(x) or 'item' in str(x)))

        for item in experience_items:
            try:
                # Гибкий поиск данных опыта работы
                period_elem = (item.find('div', class_='bloko-column_s-2') or
                              item.find('div', class_=lambda x: x and 'period' in str(x).lower()) or
                              item.find('h4') or
                              item.find('div'))

                duration_elem = (item.find('div', class_='bloko-text') or
                               item.find('span', class_=lambda x: x and 'duration' in str(x).lower()))

                company_elem = (item.find('div', class_='bloko-text_strong') or
                              item.find('strong') or
                              item.find('b'))

                position_elem = (item.find('div', {'data-qa': 'resume-block-experience-position'}) or
                               item.find('div', class_=lambda x: x and 'position' in str(x).lower()) or
                               item.find('h5'))

                description_elem = (item.find('div', {'data-qa': 'resume-block-experience-description'}) or
                                  item.find('div', class_=lambda x: x and 'description' in str(x).lower()) or
                                  item.find('p'))

                period = period_elem.text.strip() if period_elem else "Период не указан"
                duration = duration_elem.text.strip() if duration_elem else ""
                if duration:
                    period = period.replace(duration, f" ({duration})")

                company = company_elem.text.strip() if company_elem else "Компания не указана"
                position = position_elem.text.strip() if position_elem else "Должность не указана"
                description = description_elem.text.strip() if description_elem else "Описание отсутствует"

                experiences.append(f"**{period}**\n\n*{company}*\n\n**{position}**\n\n{description}\n")

            except Exception as e:
                logger.warning(f"Ошибка при обработке элемента опыта: {e}")
                continue

    # Извлечение навыков с альтернативными селекторами
    skills = []
    skills_selectors = [
        {'tag': 'div', 'attrs': {'data-qa': 'skills-table'}},
        {'tag': 'div', 'attrs': {'class': 'skills-table'}},
        {'tag': 'div', 'attrs': {'class': 'bloko-tag-list'}}
    ]

    skills_section = None
    for selector in skills_selectors:
        skills_section = soup.find(selector.get('tag'), selector.get('attrs', {}))
        if skills_section:
            break

    if skills_section:
        skill_elements = skills_section.find_all(['span', 'div'], {'data-qa': 'bloko-tag__text'})
        if not skill_elements:
            # Альтернативный поиск навыков
            skill_elements = skills_section.find_all(['span', 'div'], class_=lambda x: x and ('tag' in str(x) or 'skill' in str(x).lower()))

        skills = [tag.text.strip() for tag in skill_elements if tag.text.strip()]

    # Формирование Markdown с проверками
    markdown = f"# {name}\n\n"

    if gender_age != "Не найдено":
        markdown += f"**{gender_age}**\n\n"

    if location != "Не найдено":
        markdown += f"**Местоположение:** {location}\n\n"

    if job_title != "Не найдено":
        markdown += f"**Должность:** {job_title}\n\n"

    if job_status != "Не найдено":
        markdown += f"**Статус:** {job_status}\n\n"

    markdown += "## Опыт работы\n\n"
    markdown += "\n".join(experiences) if experiences else "Опыт работы не найден.\n"

    markdown += "\n## Ключевые навыки\n\n"
    markdown += ", ".join(skills) if skills else "Навыки не указаны.\n"

    return markdown.strip()
