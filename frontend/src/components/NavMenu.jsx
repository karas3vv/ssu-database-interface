function NavMenu({ onLogout }) {
  return (
    <nav style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
      <span>
        <b>Интерфейс ресторана</b>
      </span>
      <button onClick={onLogout}>Выйти</button>
    </nav>
  );
}

export default NavMenu;
