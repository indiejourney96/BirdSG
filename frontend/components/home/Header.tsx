export default function Header() {
  return (
    <header className="fixed top-0 z-50 bg-surface dark:bg-surface-dim shadow-sm flex justify-between items-center w-full px-margin-mobile h-16">
      <div className="flex items-center gap-4">
        <button className="text-primary dark:text-primary-fixed hover:bg-surface-container-high dark:hover:bg-surface-container-highest transition-colors p-2 rounded-full active:scale-95 transition-transform duration-150">
          <span className="material-symbols-outlined">menu</span>
        </button>
        <h1 className="font-headline-md text-headline-md font-bold text-primary dark:text-primary-fixed">SG BirdSpotter</h1>
      </div>
      <button className="text-primary dark:text-primary-fixed hover:bg-surface-container-high dark:hover:bg-surface-container-highest transition-colors p-2 rounded-full active:scale-95 transition-transform duration-150">
        <span className="material-symbols-outlined">account_circle</span>
      </button>
    </header>
  );
}