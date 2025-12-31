import { Link, Outlet, useLocation } from 'react-router-dom';
import { ProviderToggle } from './ProviderToggle';
import { ThemeToggle } from './ThemeToggle';

export function Layout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-offwhite dark:bg-charcoal">
      {/* Header */}
      <header className="bg-white dark:bg-charcoal-light border-b border-slate/20 dark:border-slate/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <Link to="/" className="flex items-center gap-4">
                <div className="flex-shrink-0 p-1.5 bg-white dark:bg-charcoal rounded-lg shadow-sm border border-slate/10 dark:border-slate/20">
                  <img
                    src="/iyeska-logo.png"
                    alt="Iyeska"
                    className="h-12 w-auto"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                </div>
                <div className="flex flex-col">
                  <span className="logo-text text-2xl text-charcoal dark:text-white">
                    Wowasi Ya
                  </span>
                  <span className="text-sm text-slate dark:text-slate-light">
                    Project Documentation Assistant
                  </span>
                </div>
              </Link>

              <nav className="hidden md:flex items-center gap-4">
                <Link
                  to="/"
                  className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    location.pathname === '/'
                      ? 'text-slate bg-slate/10 dark:text-slate-light dark:bg-slate/20'
                      : 'text-charcoal-light hover:text-charcoal hover:bg-slate/5 dark:text-gray-300 dark:hover:text-white dark:hover:bg-slate/10'
                  }`}
                >
                  Dashboard
                </Link>
              </nav>
            </div>

            <div className="flex items-center gap-4">
              {/* Theme Toggle */}
              <ThemeToggle />

              {/* Provider Toggle */}
              <ProviderToggle />

              <a
                href="https://docs.iyeska.net"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-slate hover:text-slate-dark dark:text-slate-light dark:hover:text-white transition-colors"
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
      <footer className="border-t border-slate/20 dark:border-slate/30 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-slate dark:text-slate-light">
            Wowasi Ya - Project Documentation Assistant by{' '}
            <a
              href="https://iyeska.net"
              className="text-terracotta hover:text-terracotta-dark hover:underline dark:text-terracotta-light"
            >
              Iyeska LLC
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}
