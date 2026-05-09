const DataTable = ({ title, columns, rows }) => {
  return (
    <section className="table-card">
      <header className="table-header">
        <h3>{title}</h3>
        <button type="button" className="ghost-button">
          View all
        </button>
      </header>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                {row.values.map((value, index) => (
                  <td key={`${row.id}-${index}`}>{value}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default DataTable;
