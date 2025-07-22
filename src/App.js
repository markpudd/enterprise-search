// src/App.js
import React from 'react';
import { SearchProvider } from './contexts/SearchContext';
import { UserProvider } from './contexts/UserContext';
import { BrandingProvider } from './contexts/BrandingContext';
import Layout from './components/Layout/Layout';
import './styles/globals.css';

function App() {
  return (
    <div className="App">
      <BrandingProvider>
        <UserProvider>
          <SearchProvider>
            <Layout />
          </SearchProvider>
        </UserProvider>
      </BrandingProvider>
    </div>
  );
}

export default App;