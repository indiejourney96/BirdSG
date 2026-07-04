export default function RecentSightings() {
  return (
    <section className="mb-xl">
      <div className="flex justify-between items-center mb-md">
        <h3 className="font-title-lg text-title-lg text-on-surface flex items-center gap-2">
          <span className="material-symbols-outlined text-primary">visibility</span>
          Recent Sightings
        </h3>
        <button className="text-primary font-label-md text-label-md hover:underline">View Map</button>
      </div>
      <div
        className="
          bg-surface-container-low
          rounded-xl
          p-lg
          shadow-sm
        "
      >
        Coming soon...
      </div>
    </section>
  );
}
