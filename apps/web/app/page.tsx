// apps/web/app/page.tsx
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-slate-50 p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold text-slate-800 tracking-tighter">
          PROJECT: <span className="text-blue-600">GHOST-SQUAD</span>
        </h1>
        <div className="fixed bottom-0 left-0 flex h-48 w-full items-end justify-center bg-gradient-to-t from-white via-white dark:from-black dark:via-black lg:static lg:h-auto lg:w-auto lg:bg-none">
          <div className="flex items-center gap-2 p-4 bg-white rounded-lg shadow-lg border border-blue-100">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-slate-600">SYSTEM ONLINE</span>
          </div>
        </div>
      </div>
    </main>
  )
}
