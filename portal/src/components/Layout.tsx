import { Link, Outlet, useLocation } from 'react-router-dom';

export function Layout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <Link to="/" className="flex items-center gap-2">
                <img
                  src="/iyeska-logo.png"
                  alt="Iyeska"
                  className="h-8 w-auto"
                  onError={(e) => {
                    // Hide if logo not found
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
                <span className="text-xl font-bold text-gray-900 dark:text-white">
                  Wowasi Ya
                </span>
              </Link>

              <nav className="hidden md:flex items-center gap-4">
                <Link
                  to="/"
                  className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    location.pathname === '/'
                      ? 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-white dark:hover:bg-gray-700'
                  }`}
                >
                  Dashboard
                </Link>
              </nav>
            </div>

            <div className="flex items-center gap-4">
              <a
                href="https://docs.iyeska.net"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
              >
                Docs
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-700 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500 dark:text-gray-400">
            Wowasi Ya - Project Documentation Assistant by{' '}
            <a
              href="https://iyeska.net"
              className="text-blue-600 hover:underline dark:text-blue-400"
            >
              Iyeska LLC
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}
