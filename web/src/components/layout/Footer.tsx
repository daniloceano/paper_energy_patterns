export default function Footer() {
  return (
    <footer className="mt-auto border-t border-slate-200 bg-slate-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="text-sm text-slate-500">
            <p>
              <strong>Energy Patterns of South Atlantic Cyclones</strong>
            </p>
            <p>
              Based on{' '}
              <a
                href="https://doi.org/10.5281/zenodo.18133432"
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 hover:underline"
              >
                Lorenz Energy Cycle diagnostics
              </a>{' '}
              &amp; ERA5 reanalysis
            </p>
          </div>
          <div className="text-sm text-slate-400">
            <p>1979–2020 · {(3820).toLocaleString()} cyclones · 42 years</p>
          </div>
        </div>
      </div>
    </footer>
  )
}
