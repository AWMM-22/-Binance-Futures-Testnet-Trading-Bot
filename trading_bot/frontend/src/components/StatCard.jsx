const StatCard = ({ label, value, delta, tone }) => {
  return (
    <article className={`stat-card stat-${tone}`}>
      <p className="stat-label">{label}</p>
      <div className="stat-row">
        <h3>{value}</h3>
        <span className="stat-delta">{delta}</span>
      </div>
    </article>
  );
};

export default StatCard;
