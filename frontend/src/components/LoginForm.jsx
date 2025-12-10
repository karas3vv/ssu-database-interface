import { useState } from "react";

function LoginForm({ onLogin }) {
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await onLogin(login, password);
    } catch (err) {
      setError(err.message || "Ошибка входа");
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: 320, margin: "0 auto" }}>
      <h2>Вход</h2>
      <div>
        <label>Логин</label>
        <input
          type="text"
          value={login}
          onChange={(e) => setLogin(e.target.value)}
        />
      </div>
      <div>
        <label>Пароль</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>
      {error && <div style={{ color: "red" }}>{error}</div>}
      <button type="submit">Войти</button>
    </form>
  );
}

export default LoginForm;
