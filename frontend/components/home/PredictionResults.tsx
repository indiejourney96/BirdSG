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
    common_name: string | null;
    scientific_name: string | null;
    family: string | null;
    order: string | null;
  };
  photo: PhotoInfo | null;
  recent_sightings_sg: RecentSighting[];
  recording: RecordingInfo | null;
  details: SpeciesDetails | null;
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
    birdsByLabel?: Record<string, BirdInfo>;
  };
  onReset: () => void;
}

interface PhotoInfo {
  url: string;
  caption: string | null;
  photographer: string | null;
  license: string | null;
  source: string;
}

interface RecentSighting {
  location: string | null;
  date: string | null;
  count: number | null;
}

interface RecordingInfo {
  audio_url: string | null;
  recording_id: string | null;
  recordist: string | null;
  location: string | null;
}

interface SpeciesDetails {
  general_knowledge: string | null;
  identification_tips: string | null;
  habitat: string | null;
  behaviour: string | null;
  diet: string | null;
  feeding_habits: string | null;
}

// Helper to turn snake_case labels into clean display titles
function formatLabel(label: string): string {
  return label
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function hasText(value: string | null | undefined): value is string {
  return Boolean(value?.trim());
}

function normalizeAudioUrl(url: string): string {
  return url.startsWith("//") ? `https:${url}` : url;
}

function normalizeImageUrl(url: string): string {
  return url.startsWith("//") ? `https:${url}` : url;
}

export default function PredictionResults({ data, onReset }: PredictionResultsProps) {
  const birdDetails = data.bird?.details;
  const recording = data.bird?.recording ?? null;
  const recordingAudioUrl = hasText(recording?.audio_url)
    ? normalizeAudioUrl(recording.audio_url)
    : null;
  const recentSightings = data.bird?.recent_sightings_sg ?? [];
  const knowledgeItems = birdDetails
    ? [
      {
        title: "Identification Tips",
        icon: "visibility",
        body: birdDetails.identification_tips,
      },
      {
        title: "Habitat",
        icon: "park",
        body: birdDetails.habitat,
      },
      {
        title: "Behaviour",
        icon: "flutter_dash",
        body: birdDetails.behaviour,
      },
      {
        title: "Diet",
        icon: "restaurant",
        body: birdDetails.diet,
      },
      {
        title: "Feeding Habits",
        icon: "grass",
        body: birdDetails.feeding_habits,
      },
    ].filter((item) => hasText(item.body))
    : [];

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
            const birdInfo = data.birdsByLabel?.[pred.label] ?? (
              pred.label === data.bird?.label ? data.bird : null
            );
            const photoUrl = hasText(birdInfo?.photo?.url)
              ? normalizeImageUrl(birdInfo.photo.url)
              : null;
            const photoAlt = birdInfo?.species.common_name ?? formatLabel(pred.label);

            return (
              <div
                key={pred.label}
                className={`p-md rounded-lg border transition-all flex flex-col gap-md md:flex-row ${index === 0
                  ? "bg-primary-container/20 border-primary/20 shadow-xs"
                  : "bg-surface border-outline-variant/30"
                  }`}
              >
                <div className="h-28 w-full overflow-hidden rounded-lg bg-surface-variant md:h-24 md:w-32 md:shrink-0">
                  {photoUrl ? (
                    <img
                      src={photoUrl}
                      alt={photoAlt}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center text-on-surface-variant">
                      <span className="material-symbols-outlined text-[32px]">
                        image_not_supported
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex-1">
                  <div className="flex justify-between items-start mb-sm">
                    <div>
                      <div className="flex flex-wrap items-center gap-xs">
                        <span className={`font-body text-body-lg font-bold ${index === 0 ? "text-primary" : "text-on-surface"
                          }`}>
                          {birdInfo?.species.common_name ?? formatLabel(pred.label)}
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
              </div>
            );
          })}

          {/* Bird Details Panel */}
          {data.bird && (
            <div className="bg-surface-container-low rounded-xl p-lg shadow-sm border border-surface-variant flex flex-col gap-md mt-lg">

              {/* Header */}
              <div className="flex flex-col gap-xs md:flex-row md:items-start md:justify-between">
                <div className="flex items-center gap-sm">
                  <span className="material-symbols-outlined text-primary">
                    flutter_dash
                  </span>
                  <h4 className="font-headline text-headline-md text-on-surface">
                    Bird Details
                  </h4>
                </div>
                <span className="font-label-sm text-label-sm text-on-surface-variant">
                  eBird code: {data.bird.ebird_code}
                </span>
              </div>

              {/* Species Info Card */}
              <div className="grid md:grid-cols-2 gap-md">

                <div className="p-md rounded-lg bg-surface border border-surface-variant">
                  <p className="font-label-sm text-on-surface-variant">Common Name</p>
                  <p className="font-body-lg font-semibold text-on-surface">
                    {data.bird.species.common_name ?? "Unknown"}
                  </p>
                </div>

                <div className="p-md rounded-lg bg-surface border border-surface-variant">
                  <p className="font-label-sm text-on-surface-variant">Scientific Name</p>
                  <p className="font-body-lg font-semibold italic text-on-surface">
                    {data.bird.species.scientific_name ?? "Unknown"}
                  </p>
                </div>

                <div className="p-md rounded-lg bg-surface border border-surface-variant">
                  <p className="font-label-sm text-on-surface-variant">Family</p>
                  <p className="font-body-lg text-on-surface">
                    {data.bird.species.family ?? "Unknown"}
                  </p>
                </div>

                <div className="p-md rounded-lg bg-surface border border-surface-variant">
                  <p className="font-label-sm text-on-surface-variant">Order</p>
                  <p className="font-body-lg text-on-surface">
                    {data.bird.species.order ?? "Unknown"}
                  </p>
                </div>

              </div>

              {(hasText(birdDetails?.general_knowledge) || knowledgeItems.length > 0) && (
                <div className="flex flex-col gap-md">
                  {hasText(birdDetails?.general_knowledge) && (
                    <div className="p-md rounded-lg bg-surface border border-surface-variant">
                      <div className="flex items-center gap-xs mb-xs">
                        <span className="material-symbols-outlined text-primary text-[18px]">
                          auto_stories
                        </span>
                        <p className="font-label-sm text-on-surface-variant uppercase tracking-wider">
                          General Knowledge
                        </p>
                      </div>
                      <p className="font-body text-body-md text-on-surface leading-relaxed">
                        {birdDetails.general_knowledge}
                      </p>
                    </div>
                  )}

                  {knowledgeItems.length > 0 && (
                    <div className="grid md:grid-cols-2 gap-md">
                      {knowledgeItems.map((item) => (
                        <div
                          key={item.title}
                          className="p-md rounded-lg bg-surface border border-surface-variant"
                        >
                          <div className="flex items-center gap-xs mb-xs">
                            <span className="material-symbols-outlined text-secondary text-[18px]">
                              {item.icon}
                            </span>
                            <p className="font-label-sm text-on-surface-variant uppercase tracking-wider">
                              {item.title}
                            </p>
                          </div>
                          <p className="font-body text-body-md text-on-surface leading-relaxed">
                            {item.body}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}


          {recentSightings.length > 0 && (
            <div className="bg-surface-container-low rounded-xl p-lg shadow-sm border border-surface-variant flex flex-col gap-md">

              <h4 className="font-headline text-headline-md text-on-surface">
                Recent Sightings in Singapore
              </h4>

              <div className="flex flex-col gap-sm">
                {recentSightings.map((sighting, idx) => (
                  <div
                    key={idx}
                    className="p-md rounded-lg bg-surface border border-surface-variant flex justify-between"
                  >
                    <div>
                      <p className="font-body font-semibold text-on-surface">
                        {sighting.location ?? "Unknown location"}
                      </p>
                      <p className="font-label-sm text-on-surface-variant">
                        {sighting.date ?? "Date unavailable"}
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

          {recordingAudioUrl && (
            <div className="bg-surface-container-low rounded-xl p-lg shadow-sm border border-surface-variant flex flex-col gap-md">
              <div className="flex flex-col gap-xs md:flex-row md:items-start md:justify-between">
                <div className="flex items-center gap-sm">
                  <span className="material-symbols-outlined text-primary">
                    volume_up
                  </span>
                  <h4 className="font-headline text-headline-md text-on-surface">
                    Bird Recording
                  </h4>
                </div>

                {hasText(recording?.recording_id) && (
                  <a
                    href={`https://xeno-canto.org/${recording.recording_id.replace(/^XC/i, "")}`}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-xs font-label-sm text-label-sm text-primary hover:underline"
                  >
                    <span className="material-symbols-outlined text-[16px]">
                      open_in_new
                    </span>
                    {recording.recording_id}
                  </a>
                )}
              </div>

              <div className="p-md rounded-lg bg-surface border border-surface-variant flex flex-col gap-sm">
                <audio
                  controls
                  preload="metadata"
                  src={recordingAudioUrl}
                  className="w-full"
                >
                  Your browser does not support audio playback.
                </audio>

                <div className="grid md:grid-cols-2 gap-sm">
                  {hasText(recording?.recordist) && (
                    <div>
                      <p className="font-label-sm text-on-surface-variant">
                        Recordist
                      </p>
                      <p className="font-body text-body-md text-on-surface">
                        {recording.recordist}
                      </p>
                    </div>
                  )}

                  {hasText(recording?.location) && (
                    <div>
                      <p className="font-label-sm text-on-surface-variant">
                        Recording Location
                      </p>
                      <p className="font-body text-body-md text-on-surface">
                        {recording.location}
                      </p>
                    </div>
                  )}
                </div>

                <p className="font-label-sm text-label-sm text-on-surface-variant">
                  Audio reference from Xeno-canto
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
