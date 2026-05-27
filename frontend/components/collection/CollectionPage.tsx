"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import Header from "@/components/home/Header";
import BottomNav from "@/components/home/BottomNav";
import { ApiError, getSighting } from "@/lib/api";

const COLLECTION_STORAGE_KEY = "birdsg:sightingIds";

type Prediction = {
  label: string;
  confidence: number;
  singapore_match: boolean;
};

type Sighting = {
  id: string;
  filename: string;
  image_url: string | null;
  predictions: Prediction[];
  singapore_filtered: boolean;
  created_at: string;
  lat: number | null;
  lng: number | null;
};

function hasText(value: string | null | undefined): value is string {
  return Boolean(value?.trim());
}

function formatLabel(label: string): string {
  return label
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatConfidence(confidence: number): string {
  const percentage = confidence <= 1 ? confidence * 100 : confidence;
  return `${percentage.toFixed(1)}%`;
}

function formatDateTime(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Date unavailable";
  }

  return new Intl.DateTimeFormat("en-SG", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Singapore",
  }).format(date);
}

function formatCoordinates(lat: number | null, lng: number | null): string {
  if (typeof lat !== "number" || typeof lng !== "number") {
    return "Location not saved";
  }

  return `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
}

function readStoredSightings(): string[] {
  if (typeof window === "undefined") {
    return [];
  }

  const raw = window.localStorage.getItem(COLLECTION_STORAGE_KEY);

  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw);

    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.filter((id): id is string => typeof id === "string" && id.trim().length > 0);
  } catch {
    return [];
  }
}

function persistSightings(ids: string[]) {
  window.localStorage.setItem(COLLECTION_STORAGE_KEY, JSON.stringify(ids));
}

export default function CollectionPage() {
  const [sightingIds, setSightingIds] = useState<string[]>(() => readStoredSightings());
  const [sightings, setSightings] = useState<Sighting[]>([]);
  const [loading, setLoading] = useState(() => sightingIds.length > 0);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [onlyWithLocation, setOnlyWithLocation] = useState(false);

  useEffect(() => {
    if (sightingIds.length === 0) {
      return;
    }

    let cancelled = false;

    async function loadSightings() {
      setLoading(true);
      setError(null);

      const results = await Promise.allSettled(
        sightingIds.map((id) => getSighting(id) as Promise<Sighting>),
      );

      if (cancelled) {
        return;
      }

      const nextSightings: Sighting[] = [];
      const validIds: string[] = [];

      results.forEach((result, index) => {
        if (result.status === "fulfilled") {
          nextSightings.push(result.value);
          validIds.push(sightingIds[index]);
        }
      });

      nextSightings.sort(
        (left, right) =>
          new Date(right.created_at).getTime() - new Date(left.created_at).getTime(),
      );

      if (validIds.length !== sightingIds.length) {
        persistSightings(validIds);
        setSightingIds(validIds);
      }

      setSightings(nextSightings);

      const rejected = results.find((result) => result.status === "rejected");
      if (rejected && nextSightings.length === 0) {
        const reason = rejected.status === "rejected" ? rejected.reason : null;
        const message =
          reason instanceof ApiError
            ? reason.message
            : "We could not load your saved sightings right now.";
        setError(message);
      }

      setLoading(false);
    }

    void loadSightings();

    return () => {
      cancelled = true;
    };
  }, [sightingIds]);

  const visibleSightings = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();

    return sightings.filter((sighting) => {
      const primaryLabel = sighting.predictions[0]?.label ?? "";
      const locationText = formatCoordinates(sighting.lat, sighting.lng);
      const haystack = [
        sighting.filename,
        primaryLabel,
        formatLabel(primaryLabel),
        locationText,
      ]
        .join(" ")
        .toLowerCase();

      if (term && !haystack.includes(term)) {
        return false;
      }

      if (onlyWithLocation && (typeof sighting.lat !== "number" || typeof sighting.lng !== "number")) {
        return false;
      }

      return true;
    });
  }, [onlyWithLocation, searchTerm, sightings]);

  const totalSightings = sightings.length;
  const speciesCount = new Set(
    sightings.map((sighting) => sighting.predictions[0]?.label).filter(hasText),
  ).size;
  const geotaggedCount = sightings.filter(
    (sighting) => typeof sighting.lat === "number" && typeof sighting.lng === "number",
  ).length;
  const singaporeMatchCount = sightings.filter((sighting) => sighting.singapore_filtered).length;
  const latestSightings = sightings.slice(0, 2);

  return (
    <>
      <Header />

      <main className="mx-auto min-h-screen max-w-screen-xl px-margin-mobile pb-32 pt-24">
        <section className="mb-lg overflow-hidden rounded-[2rem] border border-primary/10 bg-gradient-to-br from-primary-container via-primary to-tertiary-container p-lg text-on-primary shadow-[0_20px_80px_rgba(21,66,18,0.18)]">
          <div className="grid gap-lg lg:grid-cols-[1.4fr_0.9fr] lg:items-end">
            <div className="space-y-md">
              <span className="inline-flex items-center gap-2 rounded-full bg-on-primary/10 px-4 py-2 text-label-sm uppercase tracking-[0.2em] text-on-primary/80">
                <span className="material-symbols-outlined text-[18px]">
                  auto_awesome_motion
                </span>
                Your field notes
              </span>

              <div className="space-y-sm">
                <h1 className="font-headline text-4xl font-bold leading-tight md:text-5xl">
                  Collection
                </h1>
                <p className="max-w-2xl text-body-lg text-on-primary/85">
                  Revisit the photos you uploaded, review the top species predictions, and check whether the sighting was geotagged when you captured it.
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-2xl border border-on-primary/10 bg-on-primary/10 p-4 backdrop-blur">
                  <p className="text-label-sm uppercase tracking-[0.18em] text-on-primary/70">
                    Sightings
                  </p>
                  <p className="mt-2 text-3xl font-bold">{totalSightings}</p>
                </div>
                <div className="rounded-2xl border border-on-primary/10 bg-on-primary/10 p-4 backdrop-blur">
                  <p className="text-label-sm uppercase tracking-[0.18em] text-on-primary/70">
                    Unique species
                  </p>
                  <p className="mt-2 text-3xl font-bold">{speciesCount}</p>
                </div>
                <div className="rounded-2xl border border-on-primary/10 bg-on-primary/10 p-4 backdrop-blur">
                  <p className="text-label-sm uppercase tracking-[0.18em] text-on-primary/70">
                    With location
                  </p>
                  <p className="mt-2 text-3xl font-bold">{geotaggedCount}</p>
                </div>
                <div className="rounded-2xl border border-on-primary/10 bg-on-primary/10 p-4 backdrop-blur">
                  <p className="text-label-sm uppercase tracking-[0.18em] text-on-primary/70">
                    Singapore matches
                  </p>
                  <p className="mt-2 text-3xl font-bold">{singaporeMatchCount}</p>
                </div>
              </div>
            </div>

            <div className="rounded-[1.75rem] border border-on-primary/10 bg-surface/10 p-lg backdrop-blur-sm">
              <p className="text-label-sm uppercase tracking-[0.2em] text-on-primary/70">
                Latest captures
              </p>
              <div className="mt-md space-y-4">
                {latestSightings.length > 0 ? (
                  latestSightings.map((sighting) => {
                    const topPrediction = sighting.predictions[0];

                    return (
                      <div
                        key={sighting.id}
                        className="rounded-2xl border border-on-primary/10 bg-on-primary/10 p-4"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-title-lg font-semibold text-on-primary">
                              {topPrediction?.label
                                ? formatLabel(topPrediction.label)
                                : sighting.filename}
                            </p>
                            <p className="text-label-sm text-on-primary/75">
                              {formatDateTime(sighting.created_at)}
                            </p>
                          </div>
                          <span className="rounded-full bg-secondary-container px-3 py-1 text-label-sm font-semibold text-on-secondary-container">
                            {topPrediction ? formatConfidence(topPrediction.confidence) : "No match"}
                          </span>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="rounded-2xl border border-on-primary/10 bg-on-primary/10 p-4 text-on-primary/80">
                    Your latest scans will appear here once you start identifying birds.
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        <section className="sticky top-20 z-30 mb-lg rounded-2xl border border-outline-variant/70 bg-background/90 p-4 shadow-sm backdrop-blur">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="relative flex-1">
              <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-outline">
                search
              </span>
              <input
                type="search"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search by bird name, filename, or coordinates..."
                className="w-full rounded-2xl border border-outline-variant bg-surface-container-lowest py-4 pl-12 pr-4 text-on-surface shadow-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/15"
              />
            </div>

            <button
              type="button"
              onClick={() => setOnlyWithLocation((current) => !current)}
              className={`inline-flex items-center justify-center gap-2 rounded-full px-5 py-3 text-label-md font-semibold transition ${
                onlyWithLocation
                  ? "bg-primary text-on-primary shadow-md"
                  : "bg-surface-container text-on-surface hover:bg-surface-container-high"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">
                {onlyWithLocation ? "location_on" : "public"}
              </span>
              {onlyWithLocation ? "Showing geotagged only" : "Show geotagged only"}
            </button>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {["All photos", "Top species", "Map ready"].map((chip) => (
              <span
                key={chip}
                className="rounded-full border border-outline-variant bg-surface px-3 py-1 text-label-sm text-on-surface-variant"
              >
                {chip}
              </span>
            ))}
          </div>
        </section>

        {loading ? (
          <section className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <div
                key={index}
                className="overflow-hidden rounded-[1.75rem] border border-outline-variant/60 bg-surface-container-low shadow-sm"
              >
                <div className="aspect-[4/3] animate-pulse bg-surface-container-high" />
                <div className="space-y-4 p-5">
                  <div className="h-8 w-2/3 animate-pulse rounded-full bg-surface-container-high" />
                  <div className="h-4 w-full animate-pulse rounded-full bg-surface-container-high" />
                  <div className="h-4 w-5/6 animate-pulse rounded-full bg-surface-container-high" />
                  <div className="h-24 animate-pulse rounded-2xl bg-surface-container-high" />
                </div>
              </div>
            ))}
          </section>
        ) : error ? (
          <section className="rounded-[1.75rem] border border-error/20 bg-error-container p-lg text-on-error-container shadow-sm">
            <div className="flex items-start gap-3">
              <span className="material-symbols-outlined text-[24px]">error</span>
              <div>
                <h2 className="font-headline text-headline-md font-bold">
                  We could not load your collection
                </h2>
                <p className="mt-2 text-body-md">{error}</p>
              </div>
            </div>
          </section>
        ) : visibleSightings.length > 0 ? (
          <section className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {visibleSightings.map((sighting, index) => {
              const topPrediction = sighting.predictions[0];
              const topLabel = topPrediction?.label ?? sighting.filename;
              const isPrimary = index === 0;

              return (
                <article
                  key={sighting.id}
                  className={`group overflow-hidden rounded-[1.75rem] border bg-surface-container-lowest shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl ${
                    isPrimary ? "border-primary/20 ring-1 ring-primary/10" : "border-outline-variant/70"
                  }`}
                >
                  <div className="relative aspect-[4/3] overflow-hidden bg-surface-container-high">
                    {hasText(sighting.image_url) ? (
                      <img
                        src={sighting.image_url}
                        alt={topLabel}
                        className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                      />
                    ) : (
                      <div className="flex h-full w-full flex-col items-center justify-center gap-3 bg-gradient-to-br from-primary-container to-tertiary-container text-on-primary">
                        <span className="material-symbols-outlined text-[44px]">image_not_supported</span>
                        <div className="text-center">
                          <p className="text-title-lg font-semibold">
                            {formatLabel(topLabel)}
                          </p>
                          <p className="text-label-sm uppercase tracking-[0.2em] text-on-primary/75">
                            No stored photo preview
                          </p>
                        </div>
                      </div>
                    )}

                    <div className="absolute left-4 right-4 top-4 flex items-center justify-between gap-2">
                      <span className="rounded-full bg-surface/90 px-3 py-1 text-label-sm font-semibold text-on-surface shadow-sm backdrop-blur">
                        {formatDateTime(sighting.created_at)}
                      </span>

                      {sighting.singapore_filtered && (
                        <span className="rounded-full bg-secondary-container px-3 py-1 text-label-sm font-semibold text-on-secondary-container shadow-sm">
                          Singapore match
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="space-y-5 p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className="font-headline text-2xl font-bold leading-tight text-on-surface">
                          {formatLabel(topLabel)}
                        </h3>
                        <p className="mt-1 text-body-md text-on-surface-variant">
                          {sighting.filename}
                        </p>
                      </div>

                      <div className="text-right">
                        <p className="text-label-sm uppercase tracking-[0.18em] text-on-surface-variant">
                          Top confidence
                        </p>
                        <p className="text-2xl font-bold text-primary">
                          {topPrediction ? formatConfidence(topPrediction.confidence) : "N/A"}
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {sighting.predictions.slice(0, 3).map((prediction, predictionIndex) => (
                        <span
                          key={`${sighting.id}-${prediction.label}`}
                          className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-label-sm font-semibold ${
                            predictionIndex === 0
                              ? "bg-primary-container text-on-primary-container"
                              : predictionIndex === 1
                                ? "bg-secondary-container text-on-secondary-container"
                                : "bg-tertiary-fixed text-on-tertiary-fixed"
                          }`}
                        >
                          <span className="material-symbols-outlined text-[15px]">
                            flutter_dash
                          </span>
                          {formatLabel(prediction.label)}
                          <span className="opacity-80">
                            {formatConfidence(prediction.confidence)}
                          </span>
                        </span>
                      ))}
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="rounded-2xl border border-outline-variant bg-surface p-4">
                        <p className="text-label-sm uppercase tracking-[0.18em] text-on-surface-variant">
                          Location
                        </p>
                        <p className="mt-2 text-body-md font-medium text-on-surface">
                          {formatCoordinates(sighting.lat, sighting.lng)}
                        </p>
                      </div>
                      <div className="rounded-2xl border border-outline-variant bg-surface p-4">
                        <p className="text-label-sm uppercase tracking-[0.18em] text-on-surface-variant">
                          Record ID
                        </p>
                        <p className="mt-2 break-all text-body-md font-medium text-on-surface">
                          {sighting.id}
                        </p>
                      </div>
                    </div>
                  </div>
                </article>
              );
            })}
          </section>
        ) : (
          <section className="overflow-hidden rounded-[1.75rem] border border-outline-variant bg-surface-container-low shadow-sm">
            <div className="grid gap-0 lg:grid-cols-[0.95fr_1.05fr]">
              <div className="bg-gradient-to-br from-primary-container via-primary to-tertiary-container p-lg text-on-primary">
                <span className="inline-flex items-center gap-2 rounded-full bg-on-primary/10 px-3 py-1 text-label-sm uppercase tracking-[0.2em] text-on-primary/75">
                  <span className="material-symbols-outlined text-[18px]">
                    search_off
                  </span>
                  Nothing here yet
                </span>
                <h2 className="mt-4 font-headline text-4xl font-bold">
                  Your sightings will appear here
                </h2>
                <p className="mt-4 max-w-xl text-body-lg text-on-primary/85">
                  After each identification, BirdSG stores the sighting ID returned by the API. That lets this Collection page pull back the saved prediction payload later.
                </p>
              </div>

              <div className="flex flex-col justify-center gap-4 p-lg">
                <div className="rounded-2xl border border-dashed border-outline-variant bg-surface p-6">
                  <p className="text-title-lg font-semibold text-on-surface">
                    Start a new scan
                  </p>
                  <p className="mt-2 text-body-md text-on-surface-variant">
                    Upload a bird photo from the Identify tab and the result will be added to your collection automatically.
                  </p>
                </div>

                <div className="flex flex-wrap gap-3">
                  <Link
                    href="/identify"
                    className="inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-label-md font-semibold text-on-primary shadow-md transition hover:opacity-90"
                  >
                    <span className="material-symbols-outlined text-[18px]">
                      photo_camera
                    </span>
                    Open Identify
                  </Link>
                  <Link
                    href="/"
                    className="inline-flex items-center gap-2 rounded-full bg-surface-container px-5 py-3 text-label-md font-semibold text-on-surface transition hover:bg-surface-container-high"
                  >
                    <span className="material-symbols-outlined text-[18px]">
                      home
                    </span>
                    Back to Home
                  </Link>
                </div>
              </div>
            </div>
          </section>
        )}
      </main>

      <BottomNav />
    </>
  );
}
