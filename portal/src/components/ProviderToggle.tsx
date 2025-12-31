import { useState, useEffect } from 'react';

type Provider = 'llamacpp' | 'claude';

interface ProviderInfo {
  name: string;
  description: string;
  icon: React.ReactNode;
}

const PROVIDERS: Record<Provider, ProviderInfo> = {
  llamacpp: {
    name: 'M4 MacBook Pro',
    description: 'Local Llama 3.3 70B - Cost effective',
    icon: (
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
      </svg>
    ),
  },
  claude: {
    name: 'Claude API',
    description: 'Anthropic Claude - Higher quality',
    icon: (
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
      </svg>
    ),
  },
};

export function ProviderToggle() {
  const [provider, setProvider] = useState<Provider>(() => {
    const saved = localStorage.getItem('generation_provider');
    return (saved as Provider) || 'llamacpp';
  });
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem('generation_provider', provider);
  }, [provider]);

  const currentProvider = PROVIDERS[provider];

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg border border-slate/30 bg-white dark:bg-charcoal-light hover:border-slate/50 transition-colors"
      >
        <span
          className={`w-2 h-2 rounded-full ${
            provider === 'llamacpp' ? 'bg-green-500' : 'bg-terracotta'
          }`}
        />
        <span className="text-charcoal dark:text-white">{currentProvider.name}</span>
        <svg
          className={`w-4 h-4 text-slate transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />

          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-64 rounded-lg border border-slate/20 bg-white dark:bg-charcoal-light shadow-lg z-20">
            <div className="p-3 border-b border-slate/10">
              <p className="text-xs font-medium text-slate uppercase tracking-wide">
                Generation Provider
              </p>
            </div>

            <div className="p-2">
              {(Object.entries(PROVIDERS) as [Provider, ProviderInfo][]).map(([key, info]) => (
                <button
                  key={key}
                  onClick={() => {
                    setProvider(key);
                    setIsOpen(false);
                  }}
                  className={`w-full flex items-start gap-3 p-3 rounded-lg transition-colors ${
                    provider === key
                      ? 'bg-slate/10 dark:bg-slate/20'
                      : 'hover:bg-slate/5 dark:hover:bg-slate/10'
                  }`}
                >
                  <div
                    className={`mt-0.5 p-1.5 rounded-full ${
                      key === 'llamacpp'
                        ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                        : 'bg-terracotta/10 text-terracotta dark:bg-terracotta/20 dark:text-terracotta-light'
                    }`}
                  >
                    {info.icon}
                  </div>
                  <div className="flex-1 text-left">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-charcoal dark:text-white">{info.name}</span>
                      {provider === key && (
                        <svg
                          className="w-4 h-4 text-slate"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      )}
                    </div>
                    <p className="text-xs text-slate dark:text-slate-light mt-0.5">
                      {info.description}
                    </p>
                  </div>
                </button>
              ))}
            </div>

            <div className="p-3 border-t border-slate/10 bg-slate/5 dark:bg-slate/10 rounded-b-lg">
              <p className="text-xs text-slate dark:text-slate-light">
                {provider === 'llamacpp' ? (
                  <>
                    <span className="font-medium text-green-600 dark:text-green-400">$0 cost</span>
                    {' '}- Uses local M4 Mac via Cloudflare Tunnel
                  </>
                ) : (
                  <>
                    <span className="font-medium text-terracotta dark:text-terracotta-light">
                      ~$2-5/project
                    </span>
                    {' '}- Higher quality output via Anthropic API
                  </>
                )}
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// Hook to get current provider for API calls
export function useGenerationProvider(): Provider {
  const [provider, setProvider] = useState<Provider>(() => {
    const saved = localStorage.getItem('generation_provider');
    return (saved as Provider) || 'llamacpp';
  });

  useEffect(() => {
    const handleStorage = () => {
      const saved = localStorage.getItem('generation_provider');
      setProvider((saved as Provider) || 'llamacpp');
    };

    window.addEventListener('storage', handleStorage);

    // Also listen for custom events from the toggle
    const interval = setInterval(() => {
      const saved = localStorage.getItem('generation_provider');
      if (saved !== provider) {
        setProvider((saved as Provider) || 'llamacpp');
      }
    }, 500);

    return () => {
      window.removeEventListener('storage', handleStorage);
      clearInterval(interval);
    };
  }, [provider]);

  return provider;
}
