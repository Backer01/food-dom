from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
from functools import wraps
from werkzeug.utils import secure_filename
import os
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, validators
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# MySQL конфигурация
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1122'
app.config['MYSQL_DB'] = 'foodom'
mysql = MySQL(app)

# Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Admin decorator
def admin_required(f):
    """Декоратор для ограничения доступа только админам.

    Проверяет аутентификацию и наличие роли 'admin' у текущего пользователя.
    В случае ошибки возвращает HTTP 403 Forbidden.

    Args:
        f: Функция-обработчик маршрута

    Returns:
        function: Обёрнутый обработчик с проверкой прав
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


class User(UserMixin):
    """Класс пользователя для системы аутентификации.

    Args:
        id (int): Уникальный идентификатор пользователя
        username (str): Имя пользователя
        role (str): Роль пользователя ('user' или 'admin')
    """
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role


@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, role FROM users WHERE id = %s", (user_id,))
    user_data = cur.fetchone()
    cur.close()
    if user_data:
        return User(id=user_data[0], username=user_data[1], role=user_data[2])
    return None


# Формы
class RegistrationForm(FlaskForm):
    """Форма регистрации нового пользователя.
    
    Attributes:
        username (StringField): Поле для ввода имени пользователя (4-25 символов)
        password (PasswordField): Поле для ввода пароля
        confirm (PasswordField): Поле для подтверждения пароля
    """
    username = StringField('Username', [validators.Length(min=4, max=25)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


class LoginForm(FlaskForm):
    """Форма входа в систему.
    
    Attributes:
        username (StringField): Поле для ввода имени пользователя
        password (PasswordField): Поле для ввода пароля
    """
    username = StringField('Username')
    password = PasswordField('Password')


class RecipeForm(FlaskForm):
    """Форма создания/редактирования рецепта.
    
    Attributes:
        title (StringField): Название рецепта (обязательное поле)
        description (TextAreaField): Описание рецепта
        ingredients (TextAreaField): Список ингредиентов (обязательное поле)
        instructions (TextAreaField): Пошаговые инструкции (обязательное поле)
    """
    title = StringField('Название', [validators.DataRequired()])
    description = TextAreaField('Описание')
    ingredients = TextAreaField('Ингредиенты', [validators.DataRequired()])
    instructions = TextAreaField('Инструкции', [validators.DataRequired()])


def allowed_file(filename):
    """Проверяет допустимость расширения файла.

    Args:
        filename (str): Имя файла для проверки

    Returns:
        bool: True если расширение разрешено, иначе False
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWEDED_EXTENSIONS']


# Маршруты
@app.route('/privacy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM recipes")
    recipes = cur.fetchall()
    cur.close()
    return render_template('index.html', recipes=recipes)


@app.route('/recipe/<int:id>')
def recipe(id):
    cur = mysql.connection.cursor()

    # Получаем рецепт
    cur.execute("SELECT * FROM recipes WHERE id = %s", (id,))
    recipe = cur.fetchone()

    # Получаем комментарии
    cur.execute("""
        SELECT comments.text, users.username 
        FROM comments 
        JOIN users ON comments.user_id = users.id 
        WHERE recipe_id = %s
    """, (id,))
    comments = cur.fetchall()

    # Проверяем лайк
    is_liked = False
    if current_user.is_authenticated:
        cur.execute("SELECT 1 FROM likes WHERE user_id = %s AND recipe_id = %s", (current_user.id, id))
        is_liked = cur.fetchone() is not None

    cur.close()
    return render_template('recipe.html', recipe=recipe, comments=comments, is_liked=is_liked)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        password = form.password.data  # В реальном проекте нужно хешировать!

        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, 'user')", (username, password))
            mysql.connection.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Username already exists!', 'danger')
        finally:
            cur.close()

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        password = form.password.data

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, password, role FROM users WHERE username = %s", (username,))
        user_data = cur.fetchone()
        cur.close()

        if user_data and user_data[1] == password:  # Сравнение без хеширования (для демо)
            user = User(id=user_data[0], username=username, role=user_data[2])
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials!', 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/like/<int:recipe_id>', methods=['POST'])
@login_required
def like(recipe_id):
    cur = mysql.connection.cursor()

    # Проверяем, не лайкал ли уже
    cur.execute("SELECT 1 FROM likes WHERE user_id = %s AND recipe_id = %s", (current_user.id, recipe_id))
    if cur.fetchone():
        cur.execute("DELETE FROM likes WHERE user_id = %s AND recipe_id = %s", (current_user.id, recipe_id))
        action = 'unliked'
    else:
        cur.execute("INSERT INTO likes (user_id, recipe_id) VALUES (%s, %s)", (current_user.id, recipe_id))
        action = 'liked'

    mysql.connection.commit()
    cur.close()
    return {'status': 'success', 'action': action}


@app.route('/comment/<int:recipe_id>', methods=['POST'])
@login_required
def comment(recipe_id):
    text = request.form.get('text')
    if text:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO comments (user_id, recipe_id, text) VALUES (%s, %s, %s)",
                    (current_user.id, recipe_id, text))
        mysql.connection.commit()
        cur.close()
        flash('Comment added!', 'success')
    return redirect(url_for('recipe', id=recipe_id))


@app.route('/create_recipe', methods=['GET', 'POST'])
@login_required
@admin_required
def create_recipe():
    form = RecipeForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        description = form.description.data
        ingredients = form.ingredients.data
        instructions = form.instructions.data

        # Обработка загрузки изображения
        image = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image = filename

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO recipes (title, description, ingredients, instructions, image_path) 
            VALUES (%s, %s, %s, %s, %s)
        """, (title, description, ingredients, instructions, image))
        mysql.connection.commit()
        cur.close()

        flash('Рецепт успешно создан!', 'success')
        return redirect(url_for('index'))

    return render_template('create_recipe.html', form=form)


@app.route('/edit_recipe/<int:id>', methods=['GET'])
@login_required
@admin_required
def edit_recipe(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM recipes WHERE id = %s", (id,))
    recipe = cur.fetchone()
    cur.close()

    if not recipe:
        abort(404)

    form = RecipeForm()
    form.title.data = recipe[1]
    form.description.data = recipe[2]
    form.ingredients.data = recipe[3]
    form.instructions.data = recipe[4]

    return render_template('edit_recipe.html', form=form, recipe={
        'id': recipe[0],
        'title': recipe[1],
        'description': recipe[2],
        'ingredients': recipe[3],
        'instructions': recipe[4],
        'image_path': recipe[5]
    })


@app.route('/delete_recipe/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_recipe(id):
    cur = mysql.connection.cursor()

    # Сначала удаляем связанные записи (лайки и комментарии)
    cur.execute("DELETE FROM likes WHERE recipe_id = %s", (id,))
    cur.execute("DELETE FROM comments WHERE recipe_id = %s", (id,))

    # Затем удаляем сам рецепт
    cur.execute("DELETE FROM recipes WHERE id = %s", (id,))

    mysql.connection.commit()
    cur.close()
    return '', 200


@app.route('/update_recipe/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_recipe(id):
    form = RecipeForm()
    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        ingredients = form.ingredients.data
        instructions = form.instructions.data

        # Обработка загрузки нового изображения
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = filename

        cur = mysql.connection.cursor()
        if image_path:
            cur.execute("""
                UPDATE recipes 
                SET title = %s, description = %s, ingredients = %s, 
                    instructions = %s, image_path = %s 
                WHERE id = %s
            """, (title, description, ingredients, instructions, image_path, id))
        else:
            cur.execute("""
                UPDATE recipes 
                SET title = %s, description = %s, ingredients = %s, 
                    instructions = %s 
                WHERE id = %s
            """, (title, description, ingredients, instructions, id))

        mysql.connection.commit()
        cur.close()
        flash('Рецепт успешно обновлен!', 'success')
        return redirect(url_for('recipe', id=id))

    return render_template('edit_recipe.html', form=form)


@app.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT recipes.* FROM recipes
        JOIN likes ON recipes.id = likes.recipe_id
        WHERE likes.user_id = %s
    """, (current_user.id,))
    liked_recipes = cur.fetchall()
    cur.close()
    return render_template('dashboard.html', recipes=liked_recipes)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
