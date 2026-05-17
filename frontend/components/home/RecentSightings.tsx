export default function RecentSightings() {
  const sightings = [
    { name: "Crimson Sunbird", tag: "Endemic", tagBg: "bg-secondary-container text-on-secondary-container", loc: "Sungei Buloh", img: "1" },
    { name: "Oriental Pied Hornbill", tag: "Resident", tagBg: "bg-tertiary-fixed text-on-tertiary-fixed", loc: "Pasir Ris Park", img: "2" },
    { name: "Blue-throated Bee-eater", tag: "Migratory", tagBg: "bg-secondary-container text-on-secondary-container", loc: "Jurong Lake Gardens", img: "3" },
  ];

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