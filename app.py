from tkinter import *
from tkinter import ttk, messagebox # подключаем пакет ttk
import psycopg2
from config import DB_airtravel

# ======================================================================
# =======================  Соединение с БД  ============================
# ======================================================================

def get_db_connection():
    try:
        return psycopg2.connect(**DB_airtravel)
    except Exception as e:
        messagebox.showerror("База данных", f"Не удалось подключиться к БД:\n{e}")
        return None

# ======================================================================
# ======================== SQL-функции (backend) =======================
# ======================================================================

def search_airports_by_coordinates(coordinates):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        coords = [float(coord.strip()) for coord in coordinates.split(',')]
        lat_min, lat_max, lon_min, lon_max = coords

        with conn.cursor() as cur:
            query = """
            SELECT id, city, country, latitude, longitude
            FROM airports
            WHERE latitude  BETWEEN %s AND %s
            AND longitude BETWEEN %s AND %s
            ORDER BY country, city, id
            """
            cur.execute(query, (lat_min, lat_max, lon_min, lon_max))
            results = cur.fetchall()
        return results

    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")
        return []
    finally:
        if conn:
            conn.close()

def show_coord_results(results, coord_window):
    results_window = Toplevel(coord_window)
    results_window.title("Результаты поиска по координатам")
    results_window.geometry("1000x400")

    tree = ttk.Treeview(results_window, columns=("ID аэропорта", "Город", "Страна", "Широта", "Долгота"),
                        show="headings")

    tree.heading("ID аэропорта", text="ID аэропорта")
    tree.heading("Город", text="Город")
    tree.heading("Страна", text="Страна")
    tree.heading("Широта", text="Широта")
    tree.heading("Долгота", text="Долгота")

    # Настраиваем ширину столбцов
    tree.column("ID аэропорта", width=50, anchor="center")
    tree.column("Город", width=150, anchor="center")
    tree.column("Страна", width=150, anchor="center")
    tree.column("Широта", width=100, anchor="center")
    tree.column("Долгота", width=100, anchor="center")

    for result in results:
        tree.insert("", "end", values=result)

    scrollbar = ttk.Scrollbar(results_window, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", expand=True, fill="both", padx=10, pady=10)
    scrollbar.pack(side="right", fill="y")

    ttk.Button(results_window, text="Закрыть", command=results_window.destroy).pack(side = "bottom", pady=10)

def search_by_city_country(city, country):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cur:
            query = """
            SELECT id, city, country, iata, icao, latitude, longitude
            FROM airports
            WHERE LOWER(city) = LOWER(%s) AND LOWER(country) = LOWER(%s)
            """
            cur.execute(query, (city, country))
            return cur.fetchall()
    except Exception as e:
        print(f"Ошибка поиска аэропортов: {e}")
        return [], []
    finally:
        if conn:
            conn.close()


def show_city_results(results, city_window):
    results_window = Toplevel(city_window)
    results_window.title("Результаты поиска по городу")
    results_window.geometry("1000x400")

    tree = ttk.Treeview(results_window, columns=("ID аэропорта", "Город", "Страна", "IATA", "ICAO", "Широта", "Долгота"),
                        show="headings")

    tree.heading("ID аэропорта", text="ID аэропорта")
    tree.heading("Город", text="Город")
    tree.heading("Страна", text="Страна")
    tree.heading("IATA", text="IATA")
    tree.heading("ICAO", text="ICAO")
    tree.heading("Широта", text="Широта")
    tree.heading("Долгота", text="Долгота")

    # Настраиваем ширину столбцов
    tree.column("ID аэропорта", width=80, anchor="center")
    tree.column("Город", width=120, anchor="center")
    tree.column("Страна", width=120, anchor="center")
    tree.column("IATA", width=80, anchor="center")
    tree.column("ICAO", width=80, anchor="center")
    tree.column("Широта", width=120, anchor="center")
    tree.column("Долгота", width=120, anchor="center")

    for result in results:
        tree.insert("", "end", values=result)

    scrollbar = ttk.Scrollbar(results_window, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", expand=True, fill="both", padx=10, pady=10)
    scrollbar.pack(side="right", fill="y")

    ttk.Button(results_window, text="Закрыть", command=results_window.destroy).pack(side="bottom", pady=10)

def search_flights_from_city(city, country, flight_type):
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cur:
            if flight_type == 'departure':
                query = """
                SELECT 
                    r.airline, 
                    r.src_airport, 
                    r.dst_airport, 
                    a1.city as src_city, 
                    a1.country as src_country, 
                    a2.city as dst_city, 
                    a2.country as dst_country
                FROM routes r
                JOIN airports a1 ON r.src_airport = a1.iata
                JOIN airports a2 ON r.dst_airport = a2.iata
                WHERE LOWER(a1.city) = LOWER(%s) AND LOWER(a1.country) = LOWER(%s)
                """
                cur.execute(query, (city, country))

            elif flight_type == 'arrival':
                query = """
                SELECT r.airline, 
                       r.src_airport, 
                       r.dst_airport, 
                       a1.city as src_city, 
                       a1.country as src_country,
                       a2.city as dst_city, 
                       a2.country as dst_country
                FROM routes r
                JOIN airports a1 ON r.src_airport = a1.iata
                JOIN airports a2 ON r.dst_airport = a2.iata
                WHERE LOWER(a2.city) = LOWER(%s) AND LOWER(a2.country) = LOWER(%s)
                """
                cur.execute(query, (city,country))
            else:
                query = """
                SELECT r.airline, 
                       r.src_airport, 
                       r.dst_airport, 
                       a1.city as src_city, 
                       a1.country as src_country,
                       a2.city as dst_city, 
                       a2.country as dst_country
                FROM routes r
                JOIN airports a1 ON r.src_airport = a1.iata
                JOIN airports a2 ON r.dst_airport = a2.iata
                WHERE (LOWER(a1.city) = LOWER(%s) AND LOWER(a1.country) = LOWER(%s))
                    OR (LOWER(a2.city) = LOWER(%s) AND LOWER(a2.country) = LOWER(%s))
                """
                cur.execute(query, (city, country, city, country))

            return cur.fetchall()
    except Exception as e:
        print(f"Ошибка поиска рейсов: {e}")
        return []
    finally:
        if conn:
            conn.close()

def show_flights_results(results, flights_window, flight_type):
    results_window = Toplevel(flights_window)

    if flight_type == 'departure':
        title = "Рейсы отправления"
    elif flight_type == 'arrival':
        title = "Рейсы прибытия"
    else:
        title = "Все рейсы"

    results_window.title(f"Результаты поиска - {title}")
    results_window.geometry("1000x400")

    tree = ttk.Treeview(results_window, columns=("Аэропорт вылета", "Аэропорт прилета", "Город вылета","Страна вылета",
                                                 "Город прилета", "Страна прилета"), show="headings")

    tree.heading("Аэропорт вылета", text="Аэропорт вылета")
    tree.heading("Аэропорт прилета", text="Аэропорт прилета")
    tree.heading("Город вылета", text="Город вылета")
    tree.heading("Страна вылета", text="Страна вылета")
    tree.heading("Город прилета", text="Город прилета")
    tree.heading("Страна прилета", text="Страна прилета")

    # Настраиваем ширину столбцов
    tree.column("Аэропорт вылета", width=100, anchor="center")
    tree.column("Аэропорт прилета", width=100, anchor="center")
    tree.column("Город вылета", width=120, anchor="center")
    tree.column("Страна вылета", width=120, anchor="center")
    tree.column("Город прилета", width=120, anchor="center")
    tree.column("Страна прилета", width=120, anchor="center")

    for result in results:
        tree.insert("", "end", values=result)

    scrollbar = ttk.Scrollbar(results_window, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", expand=True, fill="both", padx=10, pady=10)
    scrollbar.pack(side="right", fill="y")

    ttk.Button(results_window, text="Закрыть", command=results_window.destroy).pack(side = "bottom", pady=10)

def search_direct_flights_between_cities(from_city, from_country, to_city, to_country):
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cur:
            query = """
            SELECT r.airline, 
                   r.src_airport, 
                   r.dst_airport, 
                   a1.city as src_city,
                   a1.country as src_country, 
                   a2.city as dst_city,
                   a2.country as dst_country
            FROM routes r
            JOIN airports a1 ON r.src_airport = a1.iata
            JOIN airports a2 ON r.dst_airport = a2.iata
            WHERE LOWER(a1.city) = LOWER(%s) AND LOWER(a1.country) = LOWER(%s)
              AND LOWER(a2.city) = LOWER(%s) AND LOWER(a2.country) = LOWER(%s)
            """

            cur.execute(query, (from_city, from_country, to_city, to_country))
            return cur.fetchall()
    except Exception as e:
        print(f"Ошибка поиска прямых рейсов: {e}")
        return []
    finally:
        if conn:
            conn.close()

def show_direct_results(results, direct_window):
    results_window = Toplevel(direct_window)
    results_window.title("Результаты поиска прямых рейсов")
    results_window.geometry("1000x400")

    tree = ttk.Treeview(results_window,
                        columns=("Авиакомпания", "Аэропорт вылета", "Аэропорт прилета", "Город вылета",
                                 "Страна вылета", "Город прилета", "Страна прилета"),
                        show="headings")

    tree.heading("Авиакомпания", text="Авиакомпания")
    tree.heading("Аэропорт вылета", text="Аэропорт вылета")
    tree.heading("Аэропорт прилета", text="Аэропорт прилета")
    tree.heading("Город вылета", text="Город вылета")
    tree.heading("Страна вылета", text="Страна вылета")
    tree.heading("Город прилета", text="Город прилета")
    tree.heading("Страна прилета", text="Страна прилета")

    tree.column("Авиакомпания", width=100, anchor="center")
    tree.column("Аэропорт вылета", width=100, anchor="center")
    tree.column("Аэропорт прилета", width=100, anchor="center")
    tree.column("Город вылета", width=100, anchor="center")
    tree.column("Страна вылета", width=100, anchor="center")
    tree.column("Город прилета", width=100, anchor="center")
    tree.column("Страна прилета", width=100, anchor="center")

    for result in results:
        tree.insert("", "end", values=result)

    scrollbar = ttk.Scrollbar(results_window, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", expand=True, fill="both", padx=10, pady=10)
    scrollbar.pack(side="right", fill="y")

    ttk.Button(results_window, text="Закрыть", command=results_window.destroy).pack(side = "bottom", pady=10)

# Функции для работы кнопок
# 1. Для кнопки помощь
def open_help():
    try:
        # Читаем файл help.txt
        with open("help.txt", "r", encoding="utf-8") as file:
            help_text = file.read()
    except FileNotFoundError:
        help_text = "Файл help.txt не найден!"

    # Создаем новое окно
    help_window = Toplevel()
    help_window.title("Help")
    help_window.geometry("500x400")

    help_label = ttk.Label(help_window, text=help_text,
                          wraplength=450)  # Перенос строк
    help_label.pack(padx=20, pady=20)

    close_btn = ttk.Button(help_window, text="Закрыть", command=help_window.destroy)
    close_btn.pack(expand=True, pady=2)

# ======================================================================
# ========================= Help и старт  ==============================
# ======================================================================

def open_start():
    start = Toplevel()
    start.title("Airtravel app")
    start.geometry("650x650")

    text=("Содержание приложения:\n"
"1. Поиск аэропортов по координатам\n"
"2. Поиск аэропорта по городу и стране\n"
"3. Поиск рейсов по городу\n"
"4. Поиск прямых рейсов между городами\n"

"Введите необходимый параметр и нажмите Enter:")

    label_start = ttk.Label(start, text=text, font=("Times New Roman", 14),
                            wraplength=450)
    label_start.pack(padx=20, pady=15)

    # Создание поля ввода
    field_entry = ttk.Entry(start, font=("Times New Roman", 14), width=30)
    field_entry.pack(pady=5)

    start.choice = PhotoImage(file="./Vopros.png")
    image_label = ttk.Label(start, image=start.choice)
    image_label.pack(pady=10)

    # Кнопка закрытия
    close_button = ttk.Button(start, text="Закрыть", command=start.destroy)
    close_button.pack(expand=True, anchor="s", pady=15)

    #Проверка на ввод пользователем:
    def show_errors(error_text):
        error_window=Toplevel(start)
        error_window.title("ОШИБКА")
        error_window.geometry("300x150")

        #Текст ошибки
        error_label = ttk.Label(error_window, text=error_text,
                                font=("Times New Roman", 14),
                                foreground="red",
                                wraplength=250,
                                justify="center")
        error_label.pack(expand=True, padx=20, pady=20)

        # Кнопка OK
        ok_button = ttk.Button(error_window, text="OK",
                               command=error_window.destroy)
        ok_button.pack(pady=10)

    def validate_input():
        user_input=field_entry.get().strip()

        #Проверка на пустое поле:
        if not user_input:
            show_errors("Ошибка: Поле не может быть пустым!")
            return False

        # Проверка на ввод буквы:
        if not user_input.isdigit():
            show_errors("Ошибка: Можно вводить только цифры!")
            return False

        # Проверка на длину (больше 1 цифры)
        if len(user_input) > 1:
            show_errors("Ошибка: Можно ввести только одну цифру!")
            return False

        # Проверка на диапазон (1-4)
        if user_input not in ['1', '2', '3', '4']:
            show_errors("Ошибка: Введите цифру от 1 до 4!")
            return False

        # Если все проверки пройдены - открываем соответствующее окно
        if user_input == '1':
            open_coordinates_search(start)  # передаем текущее окно для закрытия
        elif user_input == '2':
            open_city_country_search(start)
        elif user_input == '3':
            open_flights_search(start)
        elif user_input == '4':
            open_direct_flights_search(start)

        return True

    # Обработка нажатия Enter в поле ввода
    def on_enter(event):
        validate_input()

    field_entry.bind('<Return>', on_enter)

# ======================================================================
# ================== Поиск аэропортов по координатам  ==================
# ======================================================================

def open_coordinates_search(start):
    start.destroy()

    # Создаем новое окно для поиска по координатам
    coord_window = Toplevel()
    coord_window.title("Поиск аэропортов по координатам")
    coord_window.geometry("600x400")

    # Инструкция
    instruction = ("Введите диапазон координат:\n"
    "Минимальное и максимальное значение широты\n"
    "Минимальное и максимальное значение долготы\n"
    "Формат: минимальная_широта, максимальная_широта, минимальная_долгота, максимальная_долгота\n"
    "Диапазон поиска: широта [-90; 90], долгота [-180; 180]\n"
    "Пример: 40.0, 50.0, -80.0, -70.0")

    label=ttk.Label(coord_window, text=instruction, font=("Times New Roman", 12),
                   wraplength=550, justify="left")
    label.pack(padx=20, pady=15)

    # Поле ввода координат
    entry_frame = ttk.Frame(coord_window)
    entry_frame.pack(pady=10)

    coord_entry = ttk.Entry(entry_frame, font=("Times New Roman", 12), width=50)
    coord_entry.pack(side="left", padx=(0, 10))

    # Функция для показа ошибок в этом окне
    def show_coord_errors(error_text):
        error_window = Toplevel(coord_window)
        error_window.title("ОШИБКА")
        error_window.geometry("300x150")

        error_label = ttk.Label(error_window, text=error_text,
                                font=("Times New Roman", 11),
                                foreground="red",
                                wraplength=250,
                                justify="center")
        error_label.pack(expand=True, padx=20, pady=20)

        ok_button = ttk.Button(error_window, text="OK", command=error_window.destroy)
        ok_button.pack(pady=10)

    # Кнопка поиска
    def search_airports():
        coordinates = coord_entry.get().strip()

        # Здесь будет проверка ввода и поиск в БД
        if validate_coordinates(coordinates):
            results = search_airports_by_coordinates(coordinates)
            show_coord_results(results, coord_window)
        else:
            show_coord_errors("Неверный формат координат!")

    search_btn = ttk.Button(entry_frame, text="Поиск", command=search_airports)
    search_btn.pack(side="left")

    # Кнопка назад
    def go_back():
        coord_window.destroy()
        open_start()  # возвращаемся к выбору параметров

    back_btn = ttk.Button(coord_window, text="Назад", command=go_back)
    back_btn.pack(side="bottom", pady=10)

    # Функция проверки координат
    def validate_coordinates(coords_text):
        try:
            coords = [float(coord.strip()) for coord in coords_text.split(',')]
            if len(coords) != 4:
               return False

            lat_min, lat_max, lon_min, lon_max = coords

            # Проверка диапазонов
            if not (-90 <= lat_min <= 90 and -90 <= lat_max <= 90):
                return False
            if not (-180 <= lon_min <= 180 and -180 <= lon_max <= 180):
                return False
            if lat_min > lat_max or lon_min > lon_max:
                return False

            return True
        except:
            return False

# ======================================================================
# ============== Поиск аэропортов по городу и стране  ==================
# ======================================================================

def open_city_country_search(start):
    start.destroy()

    # Создаем новое окно для поиска по координатам
    city_window = Toplevel()
    city_window.title("Поиск аэропортов по городу и стране")
    city_window.geometry("600x400")

    # Инструкция
    instruction = ("Введите город и страну:\n"
                   "Формат: Город, Страна\n"
                   "Пример: Goroka, Papua New Guinea")
    label = ttk.Label(city_window, text=instruction, font=("Times New Roman", 12),
                      wraplength=550, justify="left")
    label.pack(padx=20, pady=15)

    # Поле ввода координат
    entry_frame = ttk.Frame(city_window)
    entry_frame.pack(pady=10)

    city_entry = ttk.Entry(entry_frame, font=("Times New Roman", 12), width=50)
    city_entry.pack(side="left", padx=(0, 10))

    # Функция для показа ошибок в этом окне
    def show_city_errors(error_text):
        error_window_city = Toplevel(city_window)
        error_window_city.title("ОШИБКА")
        error_window_city.geometry("300x150")

        error_label = ttk.Label(error_window_city, text=error_text,
                                font=("Times New Roman", 11),
                                foreground="red",
                                wraplength=250,
                                justify="center")
        error_label.pack(expand=True, padx=20, pady=20)

        ok_button = ttk.Button(error_window_city, text="OK", command=error_window_city.destroy)
        ok_button.pack(pady=10)

    # Функция проверки ввода города и страны
    def validate_city_country_input(input_text):
        if not input_text:
            return False, "Введите город и страну!"

        parts = [part.strip() for part in input_text.split(',')]
        if len(parts) != 2:
            return False, "Неверный формат!\nИспользуйте: Город, Страна"

        city, country = parts
        if not city or not country:
            return False, "Город и страна не могут быть пустыми!"

        return True, (city, country)

    def search_by_city_country_f():
        input_text = city_entry.get().strip()
        is_valid, result = validate_city_country_input(input_text)
        if not is_valid:
            show_city_errors(result)
            return

        city, country = result
        results = search_by_city_country(city, country)
        if results:
            show_city_results(results, city_window)
        else:
            show_city_errors("Аэропорты не найдены!")

    search_btn = ttk.Button(entry_frame, text="Поиск", command=search_by_city_country_f)
    search_btn.pack(side="left")

    # Кнопка назад
    def go_back():
        city_window.destroy()
        open_start()  # возвращаемся к выбору параметров

    back_btn = ttk.Button(city_window, text="Назад", command=go_back)
    back_btn.pack(side="bottom", pady=5)

# ======================================================================
# =====================  Поиск рейсов по городу  =======================
# ======================================================================

def open_flights_search(start):
    start.destroy()

    flights_window = Toplevel()
    flights_window.title("Поиск рейсов по городу")
    flights_window.geometry("600x400")

    instruction = ("Введите город, страну и тип рейса.\n\n"
"Формат: Город, Страна, Тип рейса \n"
"Тип рейса может быть: arrival-прибытие, departure-отправление, both-оба варианта\n"
"Пример: Goroka, Papua New Guinea, departure")
    label_flights = ttk.Label(flights_window, text=instruction,
                              font=("Times New Roman", 12),
                              foreground="black",
                              wraplength=250,
                              justify="left")
    label_flights.pack(expand=True, padx=20, pady=20)

    # Поле ввода
    entry_frame = ttk.Frame(flights_window)
    entry_frame.pack(pady=20)

    flights_entry = ttk.Entry(entry_frame, font=("Times New Roman", 12), width=50)
    flights_entry.pack(side="left", padx=(0, 10))

    # Функция для показа ошибок в этом окне
    def show_flight_errors(error_text):
        error_window_flights = Toplevel(flights_window)
        error_window_flights.title("ОШИБКА")
        error_window_flights.geometry("300x150")

        error_label = ttk.Label(error_window_flights, text=error_text,
                                font=("Times New Roman", 12),
                                foreground="red",
                                wraplength=250,
                                justify="center")
        error_label.pack(expand=True, padx=20, pady=20)

        ok_button = ttk.Button(error_window_flights, text="OK", command=error_window_flights.destroy)
        ok_button.pack(pady=10)

    # Функция проверки ввода города, страны и типа рейса
    def validate_flights_input(input_text):
        if not input_text:
            return False, "Введите город, страну и тип рейса!"

        parts = [part.strip() for part in input_text.split(',')]
        if len(parts) != 3:
            return False, "Неверный формат!\nИспользуйте: Город, Страна, Тип рейса"

        city, country, flight_type = parts
        if not city or not country:
            return False, "Город, страна, тип рейса не могут быть пустыми!"

        return True, (city, country, flight_type)

    def search_flights():
        input_text = flights_entry.get().strip()
        is_valid, result = validate_flights_input(input_text)
        if not is_valid:
            show_flight_errors(result)
            return

        city, country, flight_type = result
        results = search_flights_from_city(city, country,  flight_type)

        if results:
            show_flights_results(results, flights_window, flight_type)
        else:
            show_flight_errors("Рейсы не найдены!\n\nПроверьте правильность введенных данных.")

    search_btn = ttk.Button(entry_frame, text="Поиск", command=search_flights)
    search_btn.pack(side="left")

    # Кнопка назад
    def go_back():
        flights_window.destroy()
        open_start()  # возвращаемся к выбору параметров

    back_btn = ttk.Button(flights_window, text="Назад", command=go_back)
    back_btn.pack(side="bottom", pady=5)

# ======================================================================
# =============== Прямые рейсы между двумя городами  ===================
# ======================================================================

def open_direct_flights_search(start):
    start.destroy()

    direct_window = Toplevel()
    direct_window.title("Поиск прямых рейсов между городами")
    direct_window.geometry("600x400")

    instruction = ("Введите города и страны отправления и назначения:\n"
                   "Формат отправления и назначения: Город, Страна\n"
                   "Пример отправления: Goroka, Papua New Guinea\n"
                   "Пример назначения: Madang, Papua New Guinea")

    label = ttk.Label(direct_window, text=instruction, font=("Times New Roman", 12),
                      wraplength=550, justify="left")
    label.pack(padx=20, pady=15)

    #Для отправления
    from_entry_frame = ttk.Frame(direct_window)
    from_entry_frame.pack(pady=10)

    ttk.Label(from_entry_frame, text="Отправление (Город, Страна):",
              font=("Times New Roman", 11)).pack(anchor="w")

    from_entry = ttk.Entry(from_entry_frame, font=("Times New Roman", 12), width=50)
    from_entry.pack(pady=5)

    #Для назначения
    to_entry_frame = ttk.Frame(direct_window)
    to_entry_frame.pack(pady=10)

    ttk.Label(to_entry_frame, text="Назначение (Город, Страна):",
              font=("Times New Roman", 11)).pack(anchor="w")

    to_entry = ttk.Entry(to_entry_frame, font=("Times New Roman", 12), width=50)
    to_entry.pack(pady=5)

    button_frame = ttk.Frame(direct_window)
    button_frame.pack(pady=20)

    def show_direct_errors(error_text):
        error_window = Toplevel(direct_window)
        error_window.title("ОШИБКА")
        error_window.geometry("300x150")

        error_label = ttk.Label(error_window, text=error_text,
                                font=("Times New Roman", 12),
                                foreground="red", wraplength=250, justify="center")
        error_label.pack(expand=True, padx=20, pady=20)

        ok_btn = ttk.Button(error_window, text="OK", command=error_window.destroy)
        ok_btn.pack (side="bottom", pady=5)

    def validate_direct_flights_input(input_text, field_name):
        if not input_text:
            return False, f"Введите {field_name}!"

        parts = [part.strip() for part in input_text.split(',')]
        if len(parts) != 2:
            return False, f"Неверный формат!\n Введите город и страну"

        city, country = parts
        if not city or not country:
            return False, f"Город и страна не могут быть пустыми!"

        return True, (city, country)

    def search_direct_flights_func():
        from_text = from_entry.get().strip()
        to_text = to_entry.get().strip()

        is_valid_from, result_from = validate_direct_flights_input(from_text, "отправления")
        if not is_valid_from:
            show_direct_errors(result_from)
            return

        # Проверяем ввод назначения
        is_valid_to, result_to = validate_direct_flights_input(to_text, "назначения")
        if not is_valid_to:
            show_direct_errors(result_to)
            return

        from_city, from_country = result_from
        to_city, to_country = result_to

        results = search_direct_flights_between_cities(from_city, from_country, to_city, to_country)
        if results:
            show_direct_results(results, direct_window)
        else:
            show_direct_errors("Прямые рейсы не найдены!\n\nПроверьте правильность введенных городов и стран.")

    search_btn = ttk.Button(button_frame, text="Найти рейсы", command=search_direct_flights_func)
    search_btn.pack(side="left", padx=(0, 10))

    def go_back():
        direct_window.destroy()
        open_start()

    close_btn = ttk.Button(direct_window, text="Назад", command=go_back)
    close_btn.pack(side="bottom", pady=10)

# ======================================================================
# ========================== Корневое окно  ============================
# ======================================================================

root = Tk()  # создаем корневой объект - окно
root.title("Airtravel app")  # устанавливаем заголовок окна
root.iconbitmap(default="plane2.ico") #Изображение иконки рядом с названием заголовка окна
root.geometry("500x500") # устанавливаем размеры окна


#Текстовая метка Label
plane = PhotoImage(file="./plane1.png")
label = ttk.Label(image=plane, text="Добро пожаловать в приложение авиакомпаний!", font=("Times New Roman", 14), compound="top",
                  borderwidth=2, relief="solid", background="#99FFFF", foreground="#000", padding=8)
label.pack()

#Создаем виджеты
#1. Кнопки
btn1 = ttk.Button(text="Начать", command=open_start) # создаем кнопку из пакета ttk
btn1.place(relx=0.5, rely=0.5, anchor="center") #Размещаем кнопку
btn2 = ttk.Button(root, text="Помощь", command=open_help)
btn2.pack(expand=True, anchor="sw", padx=15, pady=15)


# Создаем меню
root.option_add("*tearOff", FALSE)

main_menu = Menu()

file_menu = Menu()
file_menu.add_command(label="Новый файл")
file_menu.add_command(label="Сохранить")
file_menu.add_command(label="Открыть")
file_menu.add_separator()
file_menu.add_command(label="Выход")

main_menu.add_cascade(label="Файл", menu=file_menu)
main_menu.add_cascade(label="Правка")
main_menu.add_cascade(label="Вид")

root.config(menu=main_menu)

# устанавливаем тему
ttk.Style().theme_use("xpnative")

root.mainloop()