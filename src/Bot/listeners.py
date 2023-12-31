import discord

from src.Canvas import consts as const
from src.Canvas import course_functions as cf
from html2text import html2text


async def listen_to_help(message):
    if message.content == const.HELP_COMMAND_PREFIX:
        await message.channel.typing()
        await message.channel.send(const.HELP_MESSAGE)


async def listen_to_courses(message, courses, cache):
    if message.content == const.COURSES_COMMAND_PREFIX:
        await message.channel.typing()

        if not courses:
            await message.channel.send('COURSES NOT FOUND')
            return cache
        if not cache:
            all_courses = cf.get_all_course_names(courses=courses)
            for course in all_courses:
                cache.append(course)
            print('Cached Courses from courses listener')

        for course in cache:
            await message.channel.typing()
            await message.channel.send(f"• **{course}**")

    return cache


async def listen_to_assignments(message, courses, cache):
    if message.content == const.ASSIGNMENTS_COMMAND_PREFIX:
        await message.channel.typing()
        if not cache:
            cache = cf.get_all_pending_assignments(courses=courses)
            print('Cached Assignments from assignments listener')

        await send_assignments_messages(message=message, pending_assignments=cache)

    return cache


async def listen_to_assignment(message, courses, cache):
    command_prefix_length = len(const.ASSIGNMENT_COMMAND_PREFIX)

    if message.content == const.ASSIGNMENT_COMMAND_PREFIX.strip():
        await message.channel.send('Please input Assignment ID')
        return

    if message.content.startswith(const.ASSIGNMENT_COMMAND_PREFIX):
        await message.channel.typing()

        if not cache:
            cache = cf.get_all_pending_assignments(courses=courses)

        assignment_id = message.content[command_prefix_length:].strip()
        assignment = cf.get_assignment(assignments=cache, assignment_id=assignment_id)
        description = None

        if not assignment:
            await message.channel.send('ID NOT FOUND')
            return cache

        for key, value in assignment.items():
            await message.channel.typing()

            if key not in ['description', 'due_today']:
                await message.channel.send(f"**{key.upper()}**: {value}")
            else:
                description = discord.Embed(
                    title='**DESCRIPTION**',
                    description=html2text(assignment['description'])
                )

        await message.channel.send(embed=description)

    return cache


async def listen_to_teacher(message, courses):
    command_prefix_length = len(const.TEACHER_COMMAND_PREFIX)

    if message.content == const.TEACHER_COMMAND_PREFIX.strip():
        await message.channel.send('Please input Course Code')
        return

    if message.content.startswith(const.TEACHER_COMMAND_PREFIX):
        await message.channel.typing()

        course_key = message.content[command_prefix_length:].upper().strip()
        teacher = cf.get_teacher(courses=courses, course_key=course_key)

        if not teacher:
            message_str = "Course Code Not Found"
        else:
            message_str = f"**{teacher}**"

        await message.channel.send(message_str)


async def listen_to_announcement(message, courses):
    command_prefix_length = len(const.ANNOUNCEMENT_COMMAND_PREFIX)

    if message.content == const.ANNOUNCEMENT_COMMAND_PREFIX.strip():
        await message.channel.send('Please input Course Code')
        return

    if message.content.startswith(const.ANNOUNCEMENT_COMMAND_PREFIX):
        await message.channel.typing()

        course_key = message.content[command_prefix_length:].upper().strip()
        announcement = cf.get_announcement(courses=courses, course_key=course_key)

        if not announcement:
            message_str = "Course Code Not Found"
        else:
            message_str = f"{announcement}"

        message_str = html2text(message_str)
        embed = discord.Embed(
            description=f"{message_str}"
        )

        await message.channel.send(embed=embed)


async def listen_to_section(message, courses):
    command_prefix_length = len(const.SECTION_COMMAND_PREFIX)

    if message.content == const.SECTION_COMMAND_PREFIX.strip():
        await message.channel.send('Please input Course Code')
        return

    if message.content.startswith(const.SECTION_COMMAND_PREFIX):
        await message.channel.typing()

        course_key = message.content[command_prefix_length:].upper().strip()
        section = cf.get_section(courses=courses, course_key=course_key)

        if not section:
            message_str = "**Section Not Found**"
        else:
            message_str = f"**{section}**"

        await message.channel.send(message_str)


async def listen_to_due_today(message, cache, courses):
    if message.content == const.DUE_TODAY_COMMAND_PREFIX:
        await message.channel.typing()

        if not cache:
            cache = cf.get_all_pending_assignments(courses=courses)
            print("Cached Assignments from due_today listener")

        no_due_today = await send_assignments_messages_due_today(message=message, pending_assignments=cache)

        if no_due_today:
            await message.channel.send('No Due Today')

    return cache


async def listen_to_modules(message, courses):
    command_prefix_length = len(const.MODULES_COMMAND_PREFIX)

    if message.content.startswith(const.MODULES_COMMAND_PREFIX):
        await message.channel.typing()

        course_key = message.content[command_prefix_length:].upper().strip()
        modules = cf.get_all_modules_from_course_key(courses=courses, course_key=course_key)

        if modules is None:
            await message.channel.send('COURSE NOT FOUND')
            return
        elif not modules:
            await message.channel.send('MODULE IS EMPTY')
            return
        else:
            for module_id, module_name in modules.items():
                await message.channel.typing()
                message_str = f"• **{module_name}** \nID = {module_id}"
                await message.channel.send(message_str)


async def listen_to_module(message, courses):
    command_prefix_length = len(const.MODULE_COMMAND_PREFIX)

    if message.content == const.MODULE_COMMAND_PREFIX.strip():
        await message.channel.send('Please input Module ID')
        return

    if message.content.startswith(const.MODULE_COMMAND_PREFIX):
        await message.channel.typing()

        module_id = message.content[command_prefix_length:].strip()
        module = cf.get_module_from_module_id(courses=courses, module_id=module_id)

        if module is None:
            await message.channel.send('MODULE NOT FOUND')
            return
        elif not module:
            await message.channel.send('ITEMS EMPTY')
            return
        else:
            await message.channel.send(f"**{module.get('name')}**")
            for item in module['items']:
                await message.channel.send(f"{item}")


async def send_assignments_messages(message, pending_assignments):
    for course, assignments in pending_assignments.items():
        await message.channel.typing()

        for assignment_id, assignment_info in assignments.items():
            message_str = f"• **{assignment_info['name']}** \n({course}). \nID = {assignment_id}"
            await message.channel.send(message_str)


async def send_assignments_messages_due_today(message, pending_assignments):
    no_due_today = True

    for course, assignments in pending_assignments.items():
        await message.channel.typing()

        for assignment_id, assignment_info in assignments.items():
            if assignment_info.get('due_today'):
                no_due_today = False
                message_str = f"• **{assignment_info['name']}** \n({course}). \nID = {assignment_id}"
                await message.channel.send(message_str)

    return no_due_today
