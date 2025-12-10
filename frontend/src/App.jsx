import { useState } from "react";
import { login as apiLogin } from "./api";
import LoginPage from "./pages/LoginPage";
import ReferencesPage from "./pages/ReferencesPage";
import NavMenu from "./components/NavMenu";

function App() {
  const [token, setToken] = useState(null);

  async function handleLogin(login, password) {
    const data = await apiLogin(login, password);
    setToken(data.access_token);
  }

  function handleLogout() {
    setToken(null);
  }

  if (!token) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <div style={{ fontFamily: "sans-serif" }}>
      <NavMenu onLogout={handleLogout} />
      <ReferencesPage token={token} />
    </div>
  );
}

export default App;
