import './Header.css'

function Header({ user, onLogout }) {
  return (
    <header className="header">
      <div className="header-content">
        <h1 className="header-title">Sistema de Asistencias</h1>
        
        <div className="header-right">
          <span className="user-info">
            <span className="user-name">{user.full_name}</span>
            <span className="user-role">{user.role}</span>
          </span>
          <button onClick={onLogout} className="btn-logout">
            Cerrar Sesión
          </button>
        </div>
      </div>
    </header>
  )
}

export default Header
