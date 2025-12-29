from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import Material, Question, Subject, Test, Topic, UserProfile


@receiver(post_migrate)
def seed_studyhub_data(sender, **kwargs):
    """
    Seed demo data after migrations (idempotent).
    """
    # Only run when our app is migrated.
    if not sender or sender.label != 'core':
        return

    def ensure_subject(name: str) -> Subject:
        s, _ = Subject.objects.get_or_create(name=name)
        return s

    def ensure_topic(subject: Subject, name: str, description: str) -> Topic:
        t, _ = Topic.objects.get_or_create(subject=subject, name=name, defaults={'description': description})
        return t

    def ensure_material(topic: Topic, order: int, title: str, content: str) -> None:
        Material.objects.get_or_create(topic=topic, order=order, title=title, defaults={'content': content})

    math = ensure_subject('Математика')
    physics = ensure_subject('Физика')
    cs = ensure_subject('Информатика')
    eng = ensure_subject('Английский язык')
    chem = ensure_subject('Химия')
    bio = ensure_subject('Биология')
    hist = ensure_subject('История')
    geo = ensure_subject('География')
    lit = ensure_subject('Литература')
    econ = ensure_subject('Экономика')

    topic_alg = ensure_topic(
        math,
        'Алгебра: уравнения',
        'Линейные и квадратные уравнения, дискриминант, корни и проверка решения.',
    )
    topic_geo = ensure_topic(
        math,
        'Геометрия: треугольники',
        'Сумма углов, теорема Пифагора, свойства равнобедренного треугольника.',
    )
    topic_fun = ensure_topic(
        math,
        'Функции и графики',
        'Что такое функция, область определения, график, основные типы функций.',
    )
    topic_prob = ensure_topic(
        math,
        'Вероятность и статистика',
        'События, вероятность, среднее/медиана/мода и простые задачи.',
    )

    topic_kin = ensure_topic(
        physics,
        'Кинематика: движение',
        'Скорость, ускорение, равномерное и равноускоренное движение.',
    )
    topic_el = ensure_topic(
        physics,
        'Электричество: основы',
        'Напряжение, ток, сопротивление, закон Ома и простые цепи.',
    )
    topic_dyn = ensure_topic(
        physics,
        'Динамика: силы',
        'Сила, масса, ускорение. Законы Ньютона и примеры.',
    )
    topic_engy = ensure_topic(
        physics,
        'Энергия и работа',
        'Работа, энергия, мощность и закон сохранения энергии.',
    )

    topic_py = ensure_topic(
        cs,
        'Python: основы',
        'Типы данных, условия, циклы и функции. Практика на простых примерах.',
    )
    topic_big_o = ensure_topic(
        cs,
        'Алгоритмы: сложность',
        'Что такое Big-O, как оценивать сложность и выбирать структуры данных.',
    )
    topic_git = ensure_topic(
        cs,
        'Git: основы',
        'Коммиты, ветки, merge/rebase и базовый workflow.',
    )
    topic_web = ensure_topic(
        cs,
        'Web: HTTP и браузер',
        'Как работает HTTP, запрос/ответ, cookies, статус-коды.',
    )

    topic_eng = ensure_topic(
        eng,
        'Present Simple',
        'Базовое настоящее время: структура, маркеры, примеры и упражнения.',
    )
    topic_eng2 = ensure_topic(
        eng,
        'Past Simple',
        'Прошедшее время: правильные/неправильные глаголы и практика.',
    )
    topic_eng3 = ensure_topic(
        eng,
        'Future Simple',
        'Будущее время: will, маркеры времени и упражнения.',
    )

    # Extra subjects/topics for "много"
    ensure_topic(chem, 'Строение атома', 'Протоны/нейтроны/электроны, оболочки, изотопы.')
    ensure_topic(chem, 'Химические реакции', 'Типы реакций, уравнивание, примеры.')
    ensure_topic(chem, 'Кислоты и основания', 'pH, кислоты/основания, соли и нейтрализация.')
    ensure_topic(chem, 'Растворы', 'Концентрация, молярность, растворимость.')

    ensure_topic(bio, 'Клетка', 'Органоиды, функции, отличие растительной и животной клетки.')
    ensure_topic(bio, 'Генетика: основы', 'Гены, ДНК, наследование, законы Менделя.')
    ensure_topic(bio, 'Человек: системы органов', 'Кровообращение, дыхание, пищеварение.')
    ensure_topic(bio, 'Экология', 'Экосистемы, цепи питания, влияние человека.')

    ensure_topic(hist, 'Древний мир', 'Ключевые цивилизации и их вклад.')
    ensure_topic(hist, 'Средневековье', 'Феодализм, города, культура.')
    ensure_topic(hist, 'Новое время', 'Революции, индустриализация, государства.')
    ensure_topic(hist, 'XX век', 'Ключевые события и процессы.')

    ensure_topic(geo, 'Материки и океаны', 'Карта мира, климатические пояса.')
    ensure_topic(geo, 'Рельеф и полезные ископаемые', 'Горы, равнины и ресурсы.')
    ensure_topic(geo, 'Погода и климат', 'Температура, осадки, климатические зоны.')
    ensure_topic(geo, 'Население и страны', 'Демография, урбанизация, примеры стран.')

    ensure_topic(lit, 'Жанры литературы', 'Эпос, лирика, драма. Примеры.')
    ensure_topic(lit, 'Поэзия: анализ', 'Ритм, рифма, средства выразительности.')
    ensure_topic(lit, 'Проза: сюжет', 'Композиция, персонажи, конфликт.')
    ensure_topic(lit, 'Классика', 'Ключевые авторы и произведения.')

    ensure_topic(econ, 'Спрос и предложение', 'Равновесие, эластичность и примеры.')
    ensure_topic(econ, 'Рынки и конкуренция', 'Монополия, олигополия, конкуренция.')
    ensure_topic(econ, 'Деньги и инфляция', 'Что такое инфляция и как её измеряют.')
    ensure_topic(econ, 'Бюджет и налоги', 'Доходы/расходы государства, налоги.')

    # Materials (a few per topic)
    ensure_material(topic_alg, 1, 'Линейные уравнения', 'Линейное уравнение имеет вид ax + b = 0.\n\nШаги: перенести b, разделить на a.')
    ensure_material(
        topic_alg,
        2,
        'Квадратные уравнения и дискриминант',
        'Квадратное уравнение: ax² + bx + c = 0.\n\nДискриминант: D = b² − 4ac.\n'
        'Если D > 0 — 2 корня, D = 0 — 1 корень, D < 0 — корней нет (в ℝ).',
    )
    ensure_material(topic_geo, 1, 'Сумма углов треугольника', 'Сумма внутренних углов треугольника равна 180°.')
    ensure_material(topic_kin, 1, 'Скорость и ускорение', 'Скорость v = s/t.\nУскорение a = (v − v0)/t.\nЕдиницы: м/с, м/с².')
    ensure_material(topic_py, 1, 'Переменные и типы', 'Python: int, float, str, bool.\nПример: x = 5, name = \"Ann\".')
    ensure_material(topic_big_o, 1, 'Big-O на пальцах', 'O(1), O(log n), O(n), O(n log n), O(n²).\nГлавное — рост времени при увеличении n.')
    ensure_material(topic_git, 1, 'Коммиты и ветки', 'commit — снимок изменений.\nbranch — указатель на цепочку коммитов.\nОсновные команды: status, add, commit, branch, checkout/switch.')
    ensure_material(topic_web, 1, 'Структура HTTP', 'Запрос: метод, URL, заголовки, тело.\nОтвет: статус-код, заголовки, тело.\nПримеры кодов: 200, 301, 404, 500.')
    ensure_material(topic_eng, 1, 'Структура Present Simple', 'I/You/We/They + V1.\nHe/She/It + V1+s.\nОтрицание: do/does not.')
    ensure_material(topic_eng2, 1, 'Past Simple', 'I/He/She/It + V2.\nОтрицание: did not + V1.\nВопрос: Did + subject + V1?')
    ensure_material(topic_eng3, 1, 'Future Simple', 'will + V1.\nОтрицание: will not.\nВопрос: Will + subject + V1?')

    # Ensure every topic has at least 1 material (so "Материалы" is never empty)
    for t in Topic.objects.all():
        if not t.materials.exists():
            ensure_material(
                t,
                1,
                'Введение',
                (t.description or 'Короткий конспект по теме.') + '\n\nСовет: прочитайте материал и закрепите знания тестом.',
            )

    # Tests (one per topic, as per unique constraint). Use update_or_create to keep data correct and add explanations.
    test_alg, _ = Test.objects.get_or_create(topic=topic_alg, defaults={'title': 'Тест по алгебре (3 вопроса)'})
    Question.objects.update_or_create(
        test=test_alg,
        text='Чему равно значение x в уравнении 2x + 6 = 14?',
        defaults={
            'option_a': 'x = 2',
            'option_b': 'x = 4',
            'option_c': 'x = 5',
            'option_d': 'x = 6',
            'correct_answer': Question.ANSWER_B,
            'explanation': 'Переносим 6: 2x = 14 − 6 = 8, затем делим на 2: x = 4.',
        },
    )
    Question.objects.update_or_create(
        test=test_alg,
        text='Чему равен дискриминант уравнения x^2 - 5x + 6 = 0?',
        defaults={
            'option_a': 'D = 1',
            'option_b': 'D = 4',
            'option_c': 'D = 25',
            'option_d': 'D = 36',
            'correct_answer': Question.ANSWER_A,
            'explanation': 'D = b² − 4ac = (−5)² − 4·1·6 = 25 − 24 = 1.',
        },
    )
    Question.objects.update_or_create(
        test=test_alg,
        text='Какие корни у уравнения x^2 - 5x + 6 = 0?',
        defaults={
            'option_a': 'x = 1 и x = 6',
            'option_b': 'x = 2 и x = 3',
            'option_c': 'x = -2 и x = -3',
            'option_d': 'Корней нет',
            'correct_answer': Question.ANSWER_B,
            'explanation': 'x² − 5x + 6 = (x−2)(x−3) = 0, значит x = 2 и x = 3.',
        },
    )

    test_py, _ = Test.objects.get_or_create(topic=topic_py, defaults={'title': 'Python basics (3 вопроса)'})
    Question.objects.update_or_create(
        test=test_py,
        text='Какой тип у значения "123" (в кавычках)?',
        defaults={
            'option_a': 'int',
            'option_b': 'float',
            'option_c': 'str',
            'option_d': 'bool',
            'correct_answer': Question.ANSWER_C,
            'explanation': 'Кавычки означают строковый тип: "123" — это str, а не число.',
        },
    )
    Question.objects.update_or_create(
        test=test_py,
        text='Как вывести текст в консоль?',
        defaults={
            'option_a': 'echo("hi")',
            'option_b': 'print("hi")',
            'option_c': 'console.log("hi")',
            'option_d': 'printf("hi")',
            'correct_answer': Question.ANSWER_B,
            'explanation': 'В Python печать в консоль делается функцией print().',
        },
    )
    Question.objects.update_or_create(
        test=test_py,
        text='Что делает оператор == ?',
        defaults={
            'option_a': 'Присваивает значение',
            'option_b': 'Сравнивает на равенство',
            'option_c': 'Сравнивает на больше',
            'option_d': 'Объявляет функцию',
            'correct_answer': Question.ANSWER_B,
            'explanation': '== сравнивает два значения на равенство. Для присваивания используется =.',
        },
    )

    test_eng, _ = Test.objects.get_or_create(topic=topic_eng, defaults={'title': 'Present Simple (3 вопроса)'})
    Question.objects.update_or_create(
        test=test_eng,
        text='Выберите правильный вариант: He ____ to school every day.',
        defaults={
            'option_a': 'go',
            'option_b': 'goes',
            'option_c': 'going',
            'option_d': 'gone',
            'correct_answer': Question.ANSWER_B,
            'explanation': 'Для he/she/it в Present Simple добавляем -s/-es: go → goes.',
        },
    )
    Question.objects.update_or_create(
        test=test_eng,
        text='Отрицание в Present Simple для I/you/we/they строится с…',
        defaults={
            'option_a': 'do not',
            'option_b': 'does not',
            'option_c': 'did not',
            'option_d': 'am not',
            'correct_answer': Question.ANSWER_A,
            'explanation': 'Для I/you/we/they используется вспомогательный do: do not (don’t).',
        },
    )
    Question.objects.update_or_create(
        test=test_eng,
        text='Вопросительная форма для he/she/it начинается с…',
        defaults={
            'option_a': 'Do',
            'option_b': 'Does',
            'option_c': 'Did',
            'option_d': 'Is',
            'correct_answer': Question.ANSWER_B,
            'explanation': 'Для he/she/it в вопросе используем does: Does he…?',
        },
    )


@receiver(post_save, sender=get_user_model())
def ensure_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


