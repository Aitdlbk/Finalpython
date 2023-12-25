from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from Logging import setup_logger
from Config import user, host, password, db_name
import requests
from requests.exceptions import RequestException
from flask import jsonify
import os

# Создаем экземпляр Flask
app = Flask(__name__)
app.secret_key = '94d2305c08beba97ec38b632b638e3f8'  # Замените на свой секретный ключ

# Определение базового класса для таблицы в базе данных
Base = declarative_base()
# Определение модели для таблицы фильмов (Movies table model definition)
class MovieData(Base):
    __tablename__ = "cartoons"

    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    release_year = Column(Integer)
    genre = Column(String(255))
    plot = Column(String(1000))
    timestamp = Column(DateTime, default=datetime.utcnow)

# Настройка подключения к базе данных
engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}/{db_name}", echo=False)
Base.metadata.create_all(engine)

# Создание сессии для работы с базой данных
Session = sessionmaker(bind=engine)
session = Session()

# Настройка логгера
logger = setup_logger()

# Маршрут для отображения всех фильмов
@app.route('/')
def index():
    cartoons = session.query(MovieData).all()
    return render_template('index.html', cartoons=cartoons)

# Маршрут для добавления нового фильма
@app.route('/add_cartoon', methods=['GET', 'POST'])
def add_cartoon():
    if request.method == 'POST':
        movie_title = request.form['movie_title']

        try:
            # Запрос к OMDb API для получения данных о фильме
            api_key = '3f22046d'
            url = f"http://www.omdbapi.com/?t={movie_title}&apikey={api_key}"
            response = requests.get(url)
            response.raise_for_status()  # Бросаем исключение в случае ошибки HTTP

            movie_data = response.json()

            # Проверяем, были ли получены данные о фильме
            if movie_data.get("Response") == "False":
                flash("Movie not found. Please enter a valid movie title.", 'danger')
                return redirect(url_for('add_cartoon'))

            # Извлечение данных о фильме
            title = movie_data.get("Title")
            release_year = int(movie_data.get("Year"))
            genre = movie_data.get("Genre")
            plot = movie_data.get("Plot")

            # Проверяем, существуют ли данные с таким же названием в базе данных
            existing_data = session.query(MovieData).filter(MovieData.title == title).first()

            if not existing_data:
                # Если данных не существует, добавляем новые данные в базу данных
                new_movie_data = MovieData(
                    title=title,
                    release_year=release_year,
                    genre=genre,
                    plot=plot,
                )
                session.add(new_movie_data)

                # Сохраняем изменения в базе данных
                session.commit()
                logger.info("Movie data inserted successfully")

                # Добавляем данные в файл cartoons.txt
                save_to_cartoons_file(title, release_year, genre, plot)

        except RequestException as e:
            logger.error(f"Error while fetching movie data from OMDb API: {e}")
            flash("An error occurred while fetching movie data. Please try again.", 'danger')

        except Exception as e:
            logger.error(f"Unexpected error during movie data processing: {e}")
            flash("An unexpected error occurred. Please try again.", 'danger')

        return redirect(url_for('index'))

    return render_template('add_cartoon.html')

# Маршрут для сохранения нового фильма
def save_to_cartoons_file(title, release_year, genre, plot):
    try:
        # Путь к файлу cartoons.txt
        file_path = 'cartoons.txt'

        # Проверяем, существует ли файл, и создаем его, если нет
        if not os.path.exists(file_path):
            with open(file_path, 'w') as file:
                file.write("Title\tRelease Year\tGenre\tPlot\n")

        # Добавляем информацию о фильме в файл
        with open(file_path, 'a') as file:
            file.write(f"{title}\t{release_year}\t{genre}\t{plot}\n")

        logger.info("Data saved to cartoons.txt successfully")

    except Exception as e:
        logger.error(f"Error while saving data to cartoons.txt: {e}")


# Маршрут для удаления фильма
@app.route('/delete_cartoon/<int:cartoon_id>', methods=['POST'])
def delete_cartoon(cartoon_id):
    try:
        cartoon = session.query(MovieData).get(cartoon_id)

        if cartoon:
            session.delete(cartoon)
            session.commit()
            logger.info(f"Movie {cartoon.title} deleted successfully")
            return jsonify({'status': 'success', 'message': 'Movie deleted successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Movie not found'}), 404

    except Exception as e:
        logger.error(f"Error while deleting movie: {e}")
        return jsonify({'status': 'error', 'message': 'An error occurred while deleting the movie'}), 500

# Маршрут для отображения деталей фильма
@app.route('/movie_details/<int:cartoon_id>')
def movie_details(cartoon_id):
    try:
        cartoon = session.query(MovieData).get(cartoon_id)
        if cartoon:
            api_key = '3f22046d'
            # Получение данных о фильме через OMDb API
            api_url = f"http://www.omdbapi.com/?t={cartoon.title}&apikey={api_key}"
            response = requests.get(api_url)
            if response.status_code == 200:
                movie_data = response.json()
                cartoon.poster = movie_data.get("Poster")

            return render_template('movie_details.html', cartoon=cartoon)
        else:
            flash("Movie not found.", 'danger')
            return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Error on movie_details route: {e}")
        flash("An error occurred while fetching movie details. Please try again.", 'danger')
        return redirect(url_for('index'))

# Функция для отображения всех фильмов (дополнительная)
def index():
    try:
        cartoons = session.query(MovieData).all()
        return render_template('index.html', cartoons=cartoons)
    except Exception as e:
        app.logger.error(f"Error on index route: {e}")
        flash("An error occurred while processing your request. Please try again later.", 'danger')
        return redirect(url_for('index'))

# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)
