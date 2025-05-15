CREATE DATABASE IF NOT EXISTS foodom;
USE foodom;

-- Пользователи
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    role ENUM('user', 'admin') NOT NULL DEFAULT 'user'
);

-- Рецепты
CREATE TABLE recipes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    ingredients TEXT,
    instructions TEXT,
    image_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Лайки
CREATE TABLE likes (
    user_id INT NOT NULL,
    recipe_id INT NOT NULL,
    PRIMARY KEY (user_id, recipe_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (recipe_id) REFERENCES recipes(id)
);

-- Комментарии
CREATE TABLE comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    recipe_id INT NOT NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (recipe_id) REFERENCES recipes(id)
);

-- Пример данных
INSERT INTO recipes (title, description, ingredients, instructions, image_path) VALUES
('Паста Карбонара', 'Классическая итальянская паста', 'Спагетти, яйца, гуанчиале, пармезан, перец', '1. Варите пасту...', 'pasta.jpg'),
('Оливье', 'Новогодний салат', 'Картофель, морковь, колбаса, горошек, майонез', '1. Отварите овощи...', 'olivier.jpg');
