import sqlite3
from datetime import timedelta
from pathlib import Path

from flask import Flask, render_template, redirect, request, session, url_for, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

# Абсолютный путь к папке проекта — не зависит от того, откуда запущен скрипт
BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

# Секретный ключ нужен, чтобы куки сессии нельзя было подделать.
# Перед деплоем в продакшен замени на свою случайную длинную строку.
app.secret_key = "7f3a8d4b-9c5e-6f2a-1b3d-5e7f9a1b2c3d4e5f"

# Без этого кука входа — "сессионная": она живёт только пока открыт браузер
# и слетает при следующем визите (ровно то, из-за чего каждый день просило
# логиниться заново). PERMANENT_SESSION_LIFETIME задаёт, на сколько кука
# реально сохраняется на диске у пользователя — тут выставлен год.
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=365)

DB_PATH = BASE_DIR / "users.db"

# ==========================================================
#  ССЫЛКА НА СКАЧИВАНИЕ ЛАУНЧЕРА
#
#  По умолчанию раздаём файл из static/downloads/WinzuxxLauncher_Setup.exe —
#  положи туда установщик, собранный из папки installer/ (см. её README_RU.md).
#  Если хочешь раздавать с другого хоста/CDN — впиши сюда полный URL вместо None.
# ==========================================================
DOWNLOAD_URL = None  # None = локальный файл static/downloads/WinzuxxLauncher_Setup.exe
# ==========================================================


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def safe_next(next_url: str):
    """Разрешаем редирект только на свои же внутренние страницы (защита от
    open-redirect — нельзя передать в ?next= ссылку на чужой сайт)."""
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return None


@app.route("/favicon.ico")
def favicon():
    # Поисковики (Яндекс, Google) в первую очередь проверяют иконку
    # именно по адресу site.com/favicon.ico, а не только тег в <head>.
    return send_from_directory(
        app.static_folder, "favicon.ico", mimetype="image/vnd.microsoft.icon"
    )


@app.route("/")
def index():
    username = session.get("username")
    return render_template("index.html", username=username)


@app.route("/register", methods=["GET", "POST"])
def register():
    next_url = request.args.get("next") or request.form.get("next") or ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3:
            flash("Имя пользователя должно быть не короче 3 символов.")
            return render_template("register.html", next_url=next_url)
        if len(password) < 4:
            flash("Пароль должен быть не короче 4 символов.")
            return render_template("register.html", next_url=next_url)

        conn = get_db()
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            conn.close()
            flash("Такой пользователь уже существует.")
            return render_template("register.html", next_url=next_url)

        password_hash = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        conn.commit()
        conn.close()

        # Сразу логиним пользователя после регистрации — session.permanent
        # заставляет браузер реально сохранить куку (иначе она пропадает,
        # как только браузер закрыт, и на следующий день просит войти снова)
        session.permanent = True
        session["username"] = username
        return redirect(safe_next(next_url) or url_for("index"))

    return render_template("register.html", next_url=next_url)


@app.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.args.get("next") or request.form.get("next") or ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Неверный логин или пароль.")
            return render_template("login.html", next_url=next_url)

        # session.permanent = True — без этого кука входа держится только
        # пока открыт браузер и слетает на следующий день.
        session.permanent = True
        session["username"] = user["username"]
        return redirect(safe_next(next_url) or url_for("index"))

    return render_template("login.html", next_url=next_url)


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("index"))


@app.route("/download")
def download():
    # Скачивание доступно только зарегистрированным пользователям.
    if not session.get("username"):
        flash("Чтобы скачать лаунчер, сначала зарегистрируйся — это займёт 10 секунд.")
        return redirect(url_for("register", next=url_for("download")))

    # Перенаправляет на файл лаунчера: локальный static/downloads/... либо
    # внешний URL, если он задан в DOWNLOAD_URL выше.
    target = DOWNLOAD_URL or url_for("static", filename="downloads/WinzuxxLauncher_Setup.exe")
    return redirect(target)


# Создаём таблицу пользователей сразу при загрузке модуля.
# Это важно для хостингов, которые запускают приложение через
# WSGI/gunicorn — там блок "if __name__ == '__main__'" ниже не выполняется,
# поэтому init_db() нельзя вызывать только там.
init_db()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
