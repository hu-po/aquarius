import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';

export const Layout = () => {
  return (
    <div className="app-container">
      <nav className="main-nav">
        <div className="nav-links">
          <NavLink to="/" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            🏠
          </NavLink>
          <NavLink to="/streams" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            📷
          </NavLink>
          <NavLink to="/analysis" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            🧠
          </NavLink>
          <NavLink to="/info" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            📊
          </NavLink>
          <NavLink to="/robot" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            🤖
          </NavLink>
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout; 