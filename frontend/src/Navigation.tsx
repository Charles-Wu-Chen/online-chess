import React from 'react';
import { Link } from 'react-router-dom';

const Navigation: React.FC = () => {
  return (
    <nav style={{
      display: 'flex',
      justifyContent: 'center',
      padding: '1rem',
      backgroundColor: '#f0f0f0',
      marginBottom: '1rem',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    }}>
      <Link to="/" style={linkStyle}>Home</Link>
      <Link to="/default" style={linkStyle}>Default Chessboard</Link>
      <Link to="/random-move" style={linkStyle}>Random Move Chessboard</Link>
    </nav>
  );
};

const linkStyle = {
  margin: '0 1rem',
  textDecoration: 'none',
  color: '#333',
  fontWeight: 'bold',
  padding: '0.5rem 1rem',
  borderRadius: '4px',
  transition: 'background-color 0.3s',
};

export default Navigation;