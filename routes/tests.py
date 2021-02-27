from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from cities.models import City
from routes.forms import RouteForm
from trains.models import Train
from routes import views as routes_view
from routes.utils import dfs_paths, get_graph
from cities import views as cities_view


# . - означает успешное выполнение теста, F - означает, что что-то пошло не так.
class AllTestsCase(TestCase):

    # Начальные даные для базы данных
    def setUp(self) -> None:
        # Создание экземляров городов
        self.city_A = City.objects.create(name='A')
        self.city_B = City.objects.create(name='B')
        self.city_C = City.objects.create(name='C')
        self.city_D = City.objects.create(name='D')
        self.city_E = City.objects.create(name='E')
        # Создание экземляров поездов
        lst = [
            Train(name='t1', from_city=self.city_A, to_city=self.city_B, travel_time=9),
            Train(name='t2', from_city=self.city_B, to_city=self.city_D, travel_time=8),
            Train(name='t3', from_city=self.city_A, to_city=self.city_C, travel_time=7),
            Train(name='t4', from_city=self.city_C, to_city=self.city_B, travel_time=6),
            Train(name='t5', from_city=self.city_B, to_city=self.city_E, travel_time=3),
            Train(name='t6', from_city=self.city_B, to_city=self.city_A, travel_time=11),
            Train(name='t7', from_city=self.city_A, to_city=self.city_C, travel_time=10),
            Train(name='t8', from_city=self.city_E, to_city=self.city_D, travel_time=5),
            Train(name='t9', from_city=self.city_D, to_city=self.city_E, travel_time=4)
        ]
        Train.objects.bulk_create(lst)

    # Проверка невозможности созданий дублей
    def test_model_city_duplicate(self):
        """Тестирование возникновения ошибки при создании дубликата города"""
        city = City(name='A')
        with self.assertRaises(ValidationError):
            city.full_clean()

    def test_model_train_duplicate(self):
        """Тестирование возникновения ошибки при создании дубликата поезда"""
        train = Train(name='t1', from_city=self.city_A, to_city=self.city_B, travel_time=129)
        with self.assertRaises(ValidationError):
            train.full_clean()

    def test_model_train_train_duplicate(self):
        """Тестирование возникновения ошибки при создании дубликата поезда"""
        train = Train(name='t1234', from_city=self.city_A, to_city=self.city_B, travel_time=9)
        with self.assertRaises(ValidationError):
            train.full_clean()
        try:
            train.full_clean()
        except ValidationError as e:
            # Проверка на соответствие словарю, если ожидаем только одну ошибку
            self.assertEqual({'__all__': ['Измените время в пути']}, e.message_dict)
            # Проверка на соответствие определенного сообщения в списке сообщений
            self.assertIn('Измените время в пути', e.messages)

    # Проверка валидации шаблонов и функций
    # Тестирование функции home из routes
    def test_home_routes_views(self):
        # client - эмулирует запрос в браузере
        response = self.client.get(reverse('home'))
        # 200 - код страницы
        self.assertEqual(200, response.status_code)
        # Проверка на то, что мы используем правильный шаблон
        self.assertTemplateUsed(response, template_name='routes/home.html')
        # Проверка на то, какую функцию мы используем для этих целей
        self.assertEqual(response.resolver_match.func, routes_view.home)

    # Проверка на то, какой view используется для детализации города
    def test_cbv_detail_views(self):
        # client - эмулирует запрос в браузере
        response = self.client.get(reverse('cities:detail', kwargs={'pk': self.city_A.id}))
        # 200 - код страницы
        self.assertEqual(200, response.status_code)
        # Проверка на то, что мы используем правильный шаблон
        self.assertTemplateUsed(response, template_name='cities/detail.html')
        # Проверка на то, какую функцию мы используем для этих целей
        # Т.к. это встроенный метод в класс, то сравнение идет по имени функции,
        # поэтому после func добавляем __name__
        self.assertEqual(response.resolver_match.func.__name__,
                         cities_view.CityDetailView.as_view().__name__)

    # Тестирование работоспособности функций построения графа и поиска маршрута
    def test_find_all_routes(self):
        qs = Train.objects.all()
        graph = get_graph(qs)
        all_routes = list(dfs_paths(graph, self.city_A.id, self.city_E.id))
        self.assertEqual(len(all_routes), 4)

    # Тестирование формы на валидность переданных ей данных
    def test_valid_route_form(self):
        data = {'from_city': self.city_A.id,
                'to_city': self.city_B.id,
                'cities': [self.city_E.id, self.city_D.id],
                'travelling_time': 9
                }
        form = RouteForm(data=data)
        # Если переданные данные корректны, то форма должна быть валидна
        self.assertTrue(form.is_valid())

    # Тестирование формы на невалидность переданных ей данных
    def test_invalid_route_form(self):
        data = {'from_city': self.city_A.id,
                'to_city': self.city_B.id,
                'cities': [self.city_E.id, self.city_D.id],
                }
        form = RouteForm(data=data)
        # Если передаем не полный набор данных, то форма должна быть невалидна
        self.assertFalse(form.is_valid())
        # При передаче float вместо int форма является невалидной
        data = {'from_city': self.city_A.id,
                'to_city': self.city_B.id,
                'cities': [self.city_E.id, self.city_D.id],
                'travelling_time': 9.45
                }
        form = RouteForm(data=data)
        # Если переданные данные корректны, то форма должна быть валидна
        self.assertFalse(form.is_valid())

    # Тестирование сообщений об ошибках
    def test_message_error_more_time(self):
        data = {'from_city': self.city_A.id,
                'to_city': self.city_E.id,
                'cities': [self.city_C.id],
                'travelling_time': 9
                }
        response = self.client.post('/find_routes/', data)
        # self.assertContains(response, Текст сообщения, сколько раз выводится, status code)
        self.assertContains(response, 'Время в пути больше заданного', 1, 200)

    # Тестирование сообщений об ошибках
    def test_message_error_from_cities(self):
        data = {'from_city': self.city_B.id,
                'to_city': self.city_E.id,
                'cities': [self.city_C.id],
                'travelling_time': 349
                }
        response = self.client.post('/find_routes/', data)
        # self.assertContains(response, Текст сообщения, сколько раз выводится, status code)
        self.assertContains(response, 'Маршрут через эти города невозможен', 1, 200)
