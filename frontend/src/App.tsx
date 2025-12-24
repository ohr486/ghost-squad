import React, { useEffect, useState } from 'react';
import './App.css';

function App() {
  const [message, setMessage] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // バックエンドAPIからメッセージを取得
    fetch('http://localhost:8000/')
      .then(response => response.json())
      .then(data => {
        setMessage(data.message);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching data:', error);
        setMessage('バックエンドに接続できませんでした');
        setLoading(false);
      });
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Ghost Squad</h1>
        <h2>AIエージェントサポートシステム</h2>
        {loading ? (
          <p>読み込み中...</p>
        ) : (
          <p>バックエンドからのメッセージ: {message}</p>
        )}
      </header>
    </div>
  );
}

export default App;