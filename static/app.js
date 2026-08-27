// Static HTML/CSS/JS version of Winzuxx Launcher.
// Account demo uses localStorage because static hosting has no Python/SQLite backend.
// The visual interface and CSS are kept unchanged.

(function () {
  const usersKey = "winzuxx_users";
  const sessionKey = "winzuxx_username";

  function getUsers() {
    try { return JSON.parse(localStorage.getItem(usersKey) || "{}"); }
    catch (_) { return {}; }
  }

  function setUsers(users) {
    localStorage.setItem(usersKey, JSON.stringify(users));
  }

  function currentUser() {
    return localStorage.getItem(sessionKey);
  }

  function setupNav() {
    const nav = document.getElementById("topnav");
    if (!nav) return;
    const username = currentUser();
    if (username) {
      nav.innerHTML = '<span class="nav-user">Привет, ' + escapeHtml(username) +
        '</span><a href="#" class="nav-link" id="logoutBtn">Выйти</a>';
      document.getElementById("logoutBtn").addEventListener("click", function (e) {
        e.preventDefault();
        localStorage.removeItem(sessionKey);
        location.reload();
      });
    } else {
      nav.innerHTML = '<a href="login.html" class="nav-link">Войти</a>' +
        '<a href="register.html" class="nav-link nav-link--accent">Регистрация</a>';
    }

    const hint = document.getElementById("hint");
    const download = document.getElementById("downloadBtn");
    if (hint && username) hint.textContent = "Windows · бесплатно";
    if (download && username) {
      // Put your launcher file at static/downloads/WinzuxxLauncher_Setup.exe
      download.href = "static/downloads/WinzuxxLauncher_Setup.exe";
    }
  }

  function showError(message) {
    const box = document.getElementById("formError");
    if (box) { box.textContent = message; box.style.display = "block"; }
  }

  const registerForm = document.getElementById("registerForm");
  if (registerForm) {
    registerForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const username = document.getElementById("username").value.trim();
      const password = document.getElementById("password").value;
      if (username.length < 3) return showError("Имя пользователя должно быть не короче 3 символов.");
      if (password.length < 4) return showError("Пароль должен быть не короче 4 символов.");
      const users = getUsers();
      if (users[username]) return showError("Такой пользователь уже существует.");
      users[username] = password;
      setUsers(users);
      localStorage.setItem(sessionKey, username);
      location.href = "index.html";
    });
  }

  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const username = document.getElementById("username").value.trim();
      const password = document.getElementById("password").value;
      const users = getUsers();
      if (!users[username] || users[username] !== password) return showError("Неверный логин или пароль.");
      localStorage.setItem(sessionKey, username);
      location.href = "index.html";
    });
  }

  function escapeHtml(value) {
    return value.replace(/[&<>"']/g, function (c) {
      return ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" })[c];
    });
  }

  setupNav();
})();
