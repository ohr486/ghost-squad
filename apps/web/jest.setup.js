// React Testing Library のための拡張マッチャー（.toBeInTheDocument()など）を有効化
require('@testing-library/jest-dom')

// fetch関数（API呼び出し）のグローバルモック
global.fetch = jest.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({}),
  })
);
