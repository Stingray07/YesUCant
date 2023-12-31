import os
import requests
from src.Canvas.decorators import handle_req_errors
from dotenv import load_dotenv
from src.Canvas.consts import COURSES_URL, ANNOUNCEMENTS_URL, ACTIVE_ENROLLMENT_STATE
from datetime import datetime
from src.Canvas.course_functions import get_course_code

load_dotenv()
API_KEY = os.getenv("API_KEY")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}
PAGINATION_PAGE_NUMBER = 1
PAGINATION_PER_PAGE = 50


@handle_req_errors
def initialize_courses():
    courses = get_current_courses(page_number=PAGINATION_PAGE_NUMBER, per_page=PAGINATION_PER_PAGE)
    for course_key in courses:
        course = courses[course_key]
        course['latest_announcement'] = get_latest_announcement(courses, course_key)
        course['pending_assignments'] = get_pending_assignments(courses, course_key)
        course['teacher'] = get_teacher(courses, course_key)
        course['modules'] = get_module(courses, course_key)
        print(f'✔  {course['course_name']}')

    return courses


@handle_req_errors
def get_current_courses(page_number, per_page):
    params = {
        'enrollment_state': ACTIVE_ENROLLMENT_STATE,
        'page': page_number,
        'per_page': per_page
    }

    courses = {}
    response = requests.get(COURSES_URL, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()

    if not data:
        return {}

    for item in data:
        course_name = item.get('name', None)
        course_id = item.get('id', None)
        original_name = item.get('original_name', None)

        if course_name.isupper():
            orig_course_code = item.get('course_code', None)
            course_code = get_course_code(orig_course_code)

            courses[course_code] = {
                'course_name': course_name,
                'course_id': course_id,
                'original_name': original_name,
            }

    return courses


@handle_req_errors
def get_latest_announcement(courses, course_key):
    context_code = f'course_{courses[course_key]["course_id"]}'
    params = {
        'context_codes[]': [context_code],
        'latest_only': True
    }

    response = requests.get(ANNOUNCEMENTS_URL, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()

    if not data:
        return ""

    markdown_message = data[0]['message']

    return markdown_message


@handle_req_errors
def get_pending_assignments(courses, course_key):
    course_id = courses[course_key]['course_id']
    ASSIGNMENT_URL = f'{COURSES_URL}/{course_id}/assignments'
    pending_assignments = {}

    params = {
        'include[]': ['submission'],
        'bucket': 'unsubmitted',
    }

    response = requests.get(ASSIGNMENT_URL, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()

    if not data:
        return {}

    for assignment in data:
        due = assignment['due_at']
        due_today = is_today(due)
        description = assignment['description']
        points = assignment['points_possible']
        name = assignment['name']
        assignment_id = str(assignment['id'])
        graded = assignment['submission']['grade']
        status = assignment['submission']['submitted_at']
        if not graded and not status:
            pending_assignments[assignment_id] = {
                'name': name,
                'points': points,
                'due': to_readable_date(due),
                'due_today': due_today,
                'description': description,
            }

    return pending_assignments


@handle_req_errors
def get_teacher(courses, course_key):
    course_id = courses[course_key]['course_id']
    USER_URL = f'{COURSES_URL}/{course_id}/users'

    params = {
        'enrollment_type[]': ['teacher']
    }

    response = requests.get(USER_URL, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()

    if not data:
        return ""

    teacher = data[0]['name']

    return teacher


@handle_req_errors
def get_module(courses, course_key):
    course_id = courses[course_key]['course_id']
    MODULES_URL = f"{COURSES_URL}/{course_id}/modules"
    modules = {}

    params = {
        'include[]': ['items']
    }

    response = requests.get(MODULES_URL, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()

    if not data:
        return {}

    items_list = []

    for module in data:
        name = module['name']
        module_id = str(module['id'])
        items = module['items']

        for item in items:
            item_name = item['title']
            items_list.append(item_name)

        modules[module_id] = {
            'name': name,
            'items': items_list,
        }
        items_list = []

    return modules


def to_readable_date(date_str):
    if not date_str:
        return None

    date_object = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    readable_date = date_object.strftime("%B %d, %Y %I:%M %p")

    return readable_date


def refresh_courses():
    return initialize_courses


def is_today(time):
    time = str(time)
    try:
        given_time = datetime.fromisoformat(time).date()
        current_date = datetime.now().date()
        return given_time == current_date

    except ValueError:
        return False
