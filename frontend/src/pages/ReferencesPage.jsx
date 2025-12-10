import { useEffect, useState } from "react";
import { getDishes } from "../api";

function ReferencesPage({ token }) {
  const [dishes, setDishes] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await getDishes(token);
        setDishes(data);
      } catch (err) {
        setError(err.message || "Ошибка загрузки");
      }
    }
    load();
  }, [token]);

  return (
    <div style={{ padding: "1rem" }}>
      <h2>Справочник блюд</h2>
      {error && <div style={{ color: "red" }}>{error}</div>}
      <table border="1" cellPadding="4">
        <thead>
          <tr>
            <th>Идентификатор</th>
            <th>Название</th>
            <th>Категория</th>
            <th>Цена</th>
            <th>Страна происхождения</th>
          </tr>
        </thead>
        <tbody>
          {dishes.map((b) => (
            <tr key={b.id}>
              <td>{b.id}</td>
              <td>{b.name}</td>
              <td>{b.category}</td>
              <td>{b.price}</td>
              <td>{b.country_of_origin}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ReferencesPage;
