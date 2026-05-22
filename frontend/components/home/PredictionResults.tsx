// frontend/components/home/PredictionResults.tsx
"use client";

interface Prediction {
  label: string;
  confidence: number;
  singapore_match: boolean;
}

interface BirdInfo {
  label: string;
  ebird_code: string;
  species: {
    common_name: string;
    scientific_name: string;
    family: string;
    order: string;
  };
}

interface PredictionResultsProps {
  data: {
    prediction: {
      filename: string;
      mode: string;
      predictions: Prediction[];
      singapore_filtered: boolean;
      sighting_id: string | null;
    };
    bird: BirdInfo | null;
  };
  onReset: () => void;
}

// Helper to turn snake_case labels into clean display titles
function formatLabel(label: string): string {
  return label
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export default function PredictionResults({ data, onReset }: PredictionResultsProps) {
  return (
    <section className="mb-xl animate-fade-in">
      {/* Header Area */}
      <div className="flex items-center justify-between mb-md">
        <h3 className="font-headline text-headline-md text-on-surface">
          Analysis Results
        </h3>
        <button
          onClick={onReset}
          className="inline-flex items-center gap-1.5 text-primary hover:bg-surface-container-high px-md py-xs rounded-full font-label-md text-label-md transition-colors active:scale-95"
        >
          <span className="material-symbols-outlined text-[18px]">refresh</span>
          Scan Another
        </button>
      </div>

      {/* Main Results Wrapper Card */}
      <div className="bg-surface-container-low rounded-xl p-lg shadow-sm border border-surface-variant flex flex-col gap-lg">
        <div>
          <p className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider mb-xs">
            Source File
          </p>
          <p className="font-body text-body-lg font-semibold text-on-surface">
            {data.prediction.filename}
          </p>
        </div>

        {/* Predictions Stack */}
        <div className="flex flex-col gap-md">
          <p className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
            Top Matches
          </p>

          {data.prediction.predictions.map((pred, index) => {
            const percentage = (pred.confidence * 100).toFixed(2);

            return (
              <div
                key={pred.label}
                className={`p-md rounded-lg border transition-all ${index === 0
                  ? "bg-primary-container/20 border-primary/20 shadow-xs"
                  : "bg-surface border-outline-variant/30"
                  }`}
              >
                <div className="flex justify-between items-start mb-sm">
                  <div>
                    <div className="flex items-center gap-xs">
                      <span className={`font-body text-body-lg font-bold ${index === 0 ? "text-primary" : "text-on-surface"
                        }`}>
                        {formatLabel(pred.label)}
                      </span>

                      {/* Singapore Native / Resident Stamp badge */}
                      {pred.singapore_match && (
                        <span className="inline-flex items-center gap-0.5 bg-secondary-container text-on-secondary-container text-[11px] font-semibold px-2 py-0.5 rounded-full">
                          <span className="material-symbols-outlined text-[12px]">location_on</span>
                          SG Native
                        </span>
                      )}
                    </div>
                    <p className="font-label-sm text-label-sm text-on-surface-variant mt-0.5">
                      Rank #{index + 1} Match
                    </p>
                  </div>

                  {/* Percentage Metric */}
                  <span className={`font-headline text-body-lg font-bold ${index === 0 ? "text-primary" : "text-on-surface-variant"
                    }`}>
                    {percentage}%
                  </span>
                </div>

                {/* Accuracy Progress Bar */}
                <div className="w-full bg-surface-variant h-2 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${index === 0 ? "bg-primary" : "bg-secondary"
                      }`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}

          {/* Bird Details Panel */}
          {data.bird && (
            <div className="bg-surface-container-low rounded-xl p-lg shadow-sm border border-surface-variant flex flex-col gap-md mt-lg">

              {/* Header */}
              <div className="flex items-center gap-sm">
                <span className="material-symbols-outlined text-primary">
                  flutter_dash
                </span>
                <h4 className="font-headline text-headline-md text-on-surface">
                  Bird Details
                </h4>
              </div>

              {/* Species Info Card */}
              <div className="grid md:grid-cols-2 gap-md">

                <div className="p-md rounded-lg bg-surface border border-surface-variant">
                  <p className="font-label-sm text-on-surface-variant">Common Name</p>
                  <p className="font-body-lg font-semibold text-on-surface">
                    {data.bird.species.common_name}
                  </p>
                </div>

                <div className="p-md rounded-lg bg-surface border border-surface-variant">
                  <p className="font-label-sm text-on-surface-variant">Scientific Name</p>
                  <p className="font-body-lg font-semibold italic text-on-surface">
                    {data.bird.species.scientific_name}
                  </p>
                </div>

                <div className="p-md rounded-lg bg-surface border border-surface-variant">
                  <p className="font-label-sm text-on-surface-variant">Family</p>
                  <p className="font-body-lg text-on-surface">
                    {data.bird.species.family}
                  </p>
                </div>

                <div className="p-md rounded-lg bg-surface border border-surface-variant">
                  <p className="font-label-sm text-on-surface-variant">Order</p>
                  <p className="font-body-lg text-on-surface">
                    {data.bird.species.order}
                  </p>
                </div>

              </div>
            </div>
          )}


          {(data as any).bird?.recent_sightings_sg?.length > 0 && (
            <div className="bg-surface-container-low rounded-xl p-lg shadow-sm border border-surface-variant flex flex-col gap-md">

              <h4 className="font-headline text-headline-md text-on-surface">
                Recent Sightings (Singapore)
              </h4>

              <div className="flex flex-col gap-sm">
                {(data as any).bird.recent_sightings_sg.map((sighting, idx) => (
                  <div
                    key={idx}
                    className="p-md rounded-lg bg-surface border border-surface-variant flex justify-between"
                  >
                    <div>
                      <p className="font-body font-semibold text-on-surface">
                        {sighting.location}
                      </p>
                      <p className="font-label-sm text-on-surface-variant">
                        {sighting.date}
                      </p>
                    </div>

                    {/* <div className="text-primary font-bold">
                      {sighting.count}
                    </div> */}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}