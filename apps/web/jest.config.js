const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Next.js アプリのディレクトリパス
  dir: './',
})

// Jest のカスタム設定
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
}

module.exports = createJestConfig(customJestConfig)
