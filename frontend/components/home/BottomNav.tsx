export default function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-4 pb-safe pt-2 bg-surface dark:bg-surface-dim border-t border-outline-variant dark:border-outline shadow-lg">
      <a className="flex flex-col items-center justify-center bg-secondary-container dark:bg-secondary text-on-secondary-container dark:text-on-secondary rounded-full px-5 py-1.5 active:scale-90 transition-all duration-200" href="#">
        <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>home</span>
        <span className="font-label-sm text-label-sm">Home</span>
      </a>
      <a className="flex flex-col items-center justify-center text-on-surface-variant dark:text-on-surface-variant py-1.5 hover:bg-surface-container dark:hover:bg-surface-container-high rounded-full transition-all" href="#">
        <span className="material-symbols-outlined">photo_camera</span>
        <span className="font-label-sm text-label-sm">Identify</span>
      </a>
      <a className="flex flex-col items-center justify-center text-on-surface-variant dark:text-on-surface-variant py-1.5 hover:bg-surface-container dark:hover:bg-surface-container-high rounded-full transition-all" href="#">
        <span className="material-symbols-outlined">auto_awesome_motion</span>
        <span className="font-label-sm text-label-sm">Collection</span>
      </a>
      <a className="flex flex-col items-center justify-center text-on-surface-variant dark:text-on-surface-variant py-1.5 hover:bg-surface-container dark:hover:bg-surface-container-high rounded-full transition-all" href="#">
        <span className="material-symbols-outlined">settings</span>
        <span className="font-label-sm text-label-sm">Settings</span>
      </a>
    </nav>
  );
}