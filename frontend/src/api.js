const API_URL = "http://127.0.0.1:8000";

export async function login(login, password) {
  const body = new URLSearchParams();
  body.append("username", login);
  body.append("password", password);

  const resp = await fetch(`${API_URL}/auth/войти`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
  });

  if (!resp.ok) {
    throw new Error("Неверный логин или пароль");
  }

  return await resp.json(); // { access_token, token_type }
}

export async function getDishes(token) {
  const resp = await fetch(`${API_URL}/справочники/блюда`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!resp.ok) {
    throw new Error("Ошибка загрузки блюд");
  }
  return await resp.json();
}
