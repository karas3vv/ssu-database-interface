import LoginForm from "../components/LoginForm";

function LoginPage({ onLogin }) {
  return (
    <div style={{ padding: "2rem" }}>
      <LoginForm onLogin={onLogin} />
    </div>
  );
}

export default LoginPage;
