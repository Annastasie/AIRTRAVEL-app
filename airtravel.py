import os
from typing import List, Dict
import psycopg2.extras
import psycopg2
from dotenv import load_dotenv

class airtravelDatabase:
    def __init__(self, db_params: Dict[str, str] = None):
        load_dotenv()

        if db_params is None:
            self.db_params = self.get_db_params_from_dotenv()
        else:
            self.db_params = db_params

        self.connection = None

    def get_db_params_from_dotenv(self) -> Dict[str, str]:
        params = {
            'host': os.environ.get("HOST"),
            'database': os.environ.get("DATABASE"),
            'user': os.environ.get("USER_NAME"),
            'password': os.environ.get("PASSWORD"),
            'port': os.environ.get("PORT")
        }

        return params

    def connect(self):
        try:
            self.connection = psycopg2.connect(**self.db_params)
            print("Успешное подключение к PostgreSQL")
            return True

        except psycopg2.Error as e:
            print(f"Ошибка подключения к PostgreSQL: {e}")
            return False

    def disconnect(self):
        """Закрытие соединения с базой данных"""
        if self.connection:
            self.connection.close()
            print("Соединение с базой данных закрыто")

    def get_airports_by_coordinates(self, lat_min: float, lat_max: float,
                                    lon_min: float, lon_max: float) -> List[Dict]:

        """
        Поиск аэропортов в диапазоне географических координат
        """
        query = """
        SELECT id, city, country, iata, icao, latitude, longitude
        FROM airports
        WHERE latitude BETWEEN %s AND %s 
        AND longitude BETWEEN %s AND %s
        ORDER BY country, city
        """

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(query, (lat_min, lat_max, lon_min, lon_max))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except psycopg2.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            return []

    def find_airport_by_city_country(self, city: str, country: str) -> List[Dict]:
        """
        Поиск аэропорта по городу и стране
        """
        query = """
        SELECT id, city, country, iata, icao, latitude, longitude
        FROM airports
        WHERE LOWER(city) = LOWER(%s) AND LOWER(country) = LOWER(%s)
        """

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(query, (city, country))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except psycopg2.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            return []

    def get_flights_by_city(self, city: str, country: str, flight_type: str = 'both') -> List[Dict]:
        """
        Поиск всех рейсов в или из заданного города
        flight_type: 'departure', 'arrival', 'both'
        """
        if flight_type == 'departure':
            query = """
            SELECT r.airline, r.src_airport, r.dst_airport, 
                   a1.city as src_city, a1.country as src_country,
                   a2.city as dst_city, a2.country as dst_country
            FROM routes r
            JOIN airports a1 ON r.src_airport = a1.iata
            JOIN airports a2 ON r.dst_airport = a2.iata
            WHERE LOWER(a1.city) = LOWER(%s) AND LOWER(a1.country) = LOWER(%s)
            """
        elif flight_type == 'arrival':
            query = """
            SELECT r.airline, r.src_airport, r.dst_airport, 
                   a1.city as src_city, a1.country as src_country,
                   a2.city as dst_city, a2.country as dst_country
            FROM routes r
            JOIN airports a1 ON r.src_airport = a1.iata
            JOIN airports a2 ON r.dst_airport = a2.iata
            WHERE LOWER(a2.city) = LOWER(%s) AND LOWER(a2.country) = LOWER(%s)
            """
        else:  # both
            query = """
            SELECT r.airline, r.src_airport, r.dst_airport, 
                   a1.city as src_city, a1.country as src_country,
                   a2.city as dst_city, a2.country as dst_country
            FROM routes r
            JOIN airports a1 ON r.src_airport = a1.iata
            JOIN airports a2 ON r.dst_airport = a2.iata
            WHERE (LOWER(a1.city) = LOWER(%s) AND LOWER(a1.country) = LOWER(%s))
               OR (LOWER(a2.city) = LOWER(%s) AND LOWER(a2.country) = LOWER(%s))
            """

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                if flight_type == 'both':
                    cursor.execute(query, (city, country, city, country))
                else:
                    cursor.execute(query, (city, country))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except psycopg2.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            return []

    def get_direct_flights(self, src_city: str, src_country: str,
                           dst_city: str, dst_country: str) -> List[Dict]:
        """
        Поиск прямых рейсов между двумя городами
        """
        query = """
        SELECT r.airline, r.src_airport, r.dst_airport, 
               a1.id as src_id, a2.id as dst_id
        FROM routes r
        JOIN airports a1 ON r.src_airport = a1.iata
        JOIN airports a2 ON r.dst_airport = a2.iata
        WHERE LOWER(a1.city) = LOWER(%s) AND LOWER(a1.country) = LOWER(%s)
          AND LOWER(a2.city) = LOWER(%s) AND LOWER(a2.country) = LOWER(%s)
        """

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(query, (src_city, src_country, dst_city, dst_country))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except psycopg2.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            return []


    def _get_flights_between_airports(self, src_airport: str, dst_airport: str) -> List[Dict]:
        """Получение рейсов между двумя аэропортами"""
        query = """
        SELECT airline, src_airport, dst_airport
        FROM routes
        WHERE src_airport = %s AND dst_airport = %s
        """

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(query, (src_airport, dst_airport))
                return [dict(row) for row in cursor.fetchall()]
        except psycopg2.Error as e:
            print(f"Ошибка получения рейсов: {e}")
            return []


class airtravelApp:
    def __init__(self):
        self.db = airtravelDatabase()
        self.is_connected = False

    def run(self):
        """Запуск приложения"""
        print("=" * 50)
        print("ПРИЛОЖЕНИЕ ДЛЯ РАБОТЫ С ДАННЫМИ АЭРОПОРТОВ (PostgreSQL)")
        print("=" * 50)

        if self.db.connect():
            self.is_connected = True
            print("Начинаем работу!")
            self.main_menu()
        else:
            print("Не удалось подключиться")


       # Главное меню
    def main_menu(self):
        while True:
            print("\nГЛАВНОЕ МЕНЮ:")
            print("1. Поиск аэропортов по координатам")
            print("2. Поиск аэропорта по городу и стране")
            print("3. Поиск рейсов по городу")
            print("4. Поиск прямых рейсов между городами")
            print("5. Выход")

            choice = input("\nВыберите опцию (1-5): ").strip()

            if choice == '1':
                self.search_by_coordinates()
            elif choice == '2':
                self.search_by_city_country()
            elif choice == '3':
                self.search_flights_by_city()
            elif choice == '4':
                self.search_direct_flights()
            elif choice == '5':
                break
            else:
                print("Неверный выбор. Попробуйте снова.")

        self.db.disconnect()
        print("Завершение работы с приложением. До свидания!")

    def _get_credentials(self):
        """Настройка параметров подключения к базе данных"""
        print("\nВведите ваши учетные данные:")

        username = input("Имя пользователя: ").strip()
        password = input("Пароль: ").strip()

        return username, password

    def search_by_coordinates(self):
        """Поиск аэропортов по координатам"""
        print("\n--- ПОИСК АЭРОПОРТОВ ПО КООРДИНАТАМ ---")

        try:
            lat_min = float(input("Минимальное значение широты: "))
            lat_max = float(input("Максимальное значение широты: "))
            lon_min = float(input("Минимальное значение долготы: "))
            lon_max = float(input("Максимальное значение долготы: "))
        except ValueError:
            print("Ошибка: введите числовые значения для координат.")
            return

        results = self.db.get_airports_by_coordinates(lat_min, lat_max, lon_min, lon_max)
        self.display_airports_table(results)

    def search_by_city_country(self):
        """Поиск аэропорта по городу и стране"""
        print("\n--- ПОИСК АЭРОПОРТА ПО ГОРОДУ И СТРАНЕ ---")

        city = input("Город: ").strip()
        country = input("Страна: ").strip()

        if not city or not country:
            print("Ошибка: город и страна не могут быть пустыми.")
            return

        results = self.db.find_airport_by_city_country(city, country)
        self.display_airports_table(results)

    def search_flights_by_city(self):
        """Поиск рейсов по городу"""
        print("\n--- ПОИСК РЕЙСОВ ПО ГОРОДУ ---")

        city = input("Город: ").strip()
        country = input("Страна: ").strip()
        flight_type = input("Тип рейсов (departure/arrival/both): ").strip().lower()

        if flight_type not in ['departure', 'arrival', 'both']:
            flight_type = 'both'

        results = self.db.get_flights_by_city(city, country, flight_type)
        self.display_flights_table(results)

    def search_direct_flights(self):
        """Поиск прямых рейсов между городами"""
        print("\n--- ПОИСК ПРЯМЫХ РЕЙСОВ ---")

        print("Город отправления:")
        src_city = input("Город: ").strip()
        src_country = input("Страна: ").strip()

        print("Город назначения:")
        dst_city = input("Город: ").strip()
        dst_country = input("Страна: ").strip()

        results = self.db.get_direct_flights(src_city, src_country, dst_city, dst_country)
        self.display_direct_flights_table(results)

    def display_airports_table(self, airports: List[Dict]):
        """Отображение таблицы аэропортов"""
        if not airports:
            print("Аэропорты не найдены.")
            return

        print("\n" + "=" * 100)
        print(f"{'Город':<15} {'Страна':<15} {'Широта':<10} {'Долгота':<10} {'Название аэропорта':<30} {'IATA':<6}")
        print("=" * 100)

        for airport in airports:
            latitude = airport.get('latitude')
            longitude = airport.get('longitude')
            lat_str = f"{latitude:.4f}" if isinstance(latitude, (int, float)) else str(latitude)
            lon_str = f"{longitude:.4f}" if isinstance(longitude, (int, float)) else str(longitude)

            print(f"{airport.get('city', ''):<15} {airport.get('country', ''):<15} "
                  f"{lat_str:<10} {lon_str:<10} "
                  f"{airport.get('id', ''):<30} {airport.get('iata', ''):<6}")

        print(f"\nНайдено аэропортов: {len(airports)}")

    def display_flights_table(self, flights: List[Dict]):
        """Отображение таблицы рейсов"""
        if not flights:
            print("Рейсы не найдены.")
            return

        print("\n" + "=" * 120)
        print(f"{'Авиакомпания':<15} {'Откуда':<20} {'Куда':<20} {'Город отправления':<20} {'Город назначения':<20}")
        print("=" * 120)

        for flight in flights:
            print(f"{flight.get('airline', ''):<15} {flight.get('src_airport', ''):<20} "
                  f"{flight.get('dst_airport', ''):<20} "
                  f"{flight.get('src_city', ''):<20} {flight.get('dst_city', ''):<20}")

        print(f"\nНайдено рейсов: {len(flights)}")

    def display_direct_flights_table(self, flights: List[Dict]):
        """Отображение таблицы прямых рейсов"""
        if not flights:
            print("Прямые рейсы не найдены.")
            return

        print("\n" + "=" * 80)
        print(f"{'Авиакомпания':<15} {'Аэропорт отправления':<20} {'Аэропорт назначения':<20}")
        print("=" * 80)

        for flight in flights:
            print(f"{flight.get('airline', ''):<15} {flight.get('src_airport', ''):<20} "
                  f"{flight.get('dst_airport', ''):<20}")

        print(f"\nНайдено прямых рейсов: {len(flights)}")


# Запуск приложения
if __name__ == "__main__":
    app = airtravelApp()
    app.run()