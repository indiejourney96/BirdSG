// frontend/components/home/IdentifyCard.tsx
"use client";
import { useState } from "react";
import { ApiError, predictBird, getBirdInfo } from "@/lib/api";

const COLLECTION_STORAGE_KEY = "birdsg:sightingIds";

interface PredictionItem {
  label: string;
  confidence: number;
  singapore_match: boolean;
}

interface PredictionResponse {
  filename: string;
  mode: string;
  predictions: PredictionItem[];
  singapore_filtered: boolean;
  sighting_id: string | null;
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
  photo: {
    url: string;
    caption: string | null;
    photographer: string | null;
    license: string | null;
    source: string;
  } | null;
  recent_sightings_sg: Array<{
    location: string | null;
    date: string | null;
    count: number | null;
  }>;
  recording: {
    audio_url: string | null;
    recording_id: string | null;
    recordist: string | null;
    location: string | null;
  } | null;
  details: {
    general_knowledge: string | null;
    identification_tips: string | null;
    habitat: string | null;
    behaviour: string | null;
    diet: string | null;
    feeding_habits: string | null;
  } | null;
}

interface AnalysisResult {
  prediction: PredictionResponse;
  bird: BirdInfo | null;
  birdsByLabel: Record<string, BirdInfo>;
}

interface IdentifyCardProps {
  onPredictionSuccess: (data: AnalysisResult) => void;
}

export default function IdentifyCard({ onPredictionSuccess }: IdentifyCardProps) {
  const [loading, setLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  async function handleUpload(file: File) {
    try {
      setLoading(true);
      setUploadError(null);

      const predictionData = await predictBird(file) as PredictionResponse;
      const topPrediction = predictionData.predictions?.[0];
      const topPredictions = predictionData.predictions?.slice(0, 3) ?? [];

      const birdInfoResults = await Promise.all(
        topPredictions.map(async (prediction) => {
          try {
            return [prediction.label, await getBirdInfo(prediction.label)] as const;
          } catch (error) {
            console.error(`Failed to fetch bird info for ${prediction.label}`, error);
            return [prediction.label, null] as const;
          }
        }),
      );

      const birdsByLabel = Object.fromEntries(
        birdInfoResults.filter((entry): entry is readonly [string, BirdInfo] => entry[1] !== null),
      ) as Record<string, BirdInfo>;
      const birdInfo = topPrediction ? birdsByLabel[topPrediction.label] ?? null : null;

      if (predictionData.sighting_id) {
        const currentIds = window.localStorage.getItem(COLLECTION_STORAGE_KEY);
        let parsedIds: unknown = [];

        if (currentIds) {
          try {
            parsedIds = JSON.parse(currentIds);
          } catch {
            parsedIds = [];
          }
        }

        const nextIds = Array.isArray(parsedIds) ? parsedIds : [];

        if (!nextIds.includes(predictionData.sighting_id)) {
          nextIds.unshift(predictionData.sighting_id);
        }

        window.localStorage.setItem(COLLECTION_STORAGE_KEY, JSON.stringify(nextIds));
      }

      onPredictionSuccess({
        prediction: predictionData,
        bird: birdInfo,
        birdsByLabel,
      });
    } catch (error) {
      console.error(error);

      if (error instanceof ApiError) {
        if (error.status === 422) {
          setUploadError("No bird detected. Please upload a clearer photo where the bird is visible.");
        } else if (error.status === 415) {
          setUploadError("Unsupported media type. Please upload a JPEG, PNG, or WebP image.");
        } else {
          setUploadError(error.message);
        }
      } else {
        setUploadError("Prediction failed. Please try again with another image.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="mb-xl">
      <div className="relative overflow-hidden rounded-xl bg-primary-container text-on-primary-container p-lg shadow-lg flex flex-col md:flex-row items-center justify-between gap-md group">

        <div className="z-10 text-center md:text-left flex-1">

          <h3 className="font-headline-md text-headline-md mb-2 text-on-primary-container">
            Identify Bird
          </h3>

          <p className="font-body-md text-body-md opacity-90 mb-lg">
            Point your camera to instantly identify species and log your encounter.
          </p>

          <label className="inline-flex items-center gap-2 bg-on-primary text-primary px-lg py-sm rounded-full font-label-md text-label-md shadow-md cursor-pointer hover:opacity-90 transition-opacity">

            <span
              className="material-symbols-outlined"
              style={{
                fontVariationSettings: "'FILL' 1",
              }}
            >
              photo_camera
            </span>

            {loading
              ? "Analyzing Specimen..."
              : "Launch Scanner"}

            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                e.target.value = "";

                if (file) {
                  handleUpload(file);
                }
              }}
            />

          </label>

          {uploadError && (
            <div
              role="alert"
              className="mt-md inline-flex max-w-full items-start gap-sm rounded-lg border border-error/30 bg-error-container px-md py-sm text-left text-on-error-container shadow-sm"
            >
              <span className="material-symbols-outlined text-[20px]">
                error
              </span>
              <p className="font-body text-body-sm">
                {uploadError}
              </p>
            </div>
          )}
        </div>

        <div className="relative w-full md:w-1/3 aspect-square md:aspect-video rounded-lg overflow-hidden shadow-xl border-4 border-white/10">

          <img
            alt="Identification interface"
            className="w-full h-full object-cover"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuBtgJ1H3Ojo3nC4c6GX1HdvddBmuhuWZOSv35YgUcjnhAl_smIddDRSoHBVGKNDxqjXoA_OZuQ4RX7WMS2leABt_of0OxQSjeNYzy7Vh_LrfdH5hBfWgZp7NhC57toVWfNS-HaeuxBFxQ5p8NwRaSKi5ETu06Y4bhs3mTt0Hq_fBu4RbtThbDTAdwPap7CYVXjyJHWOek6AQoRHf7_gXk3FA-t_v_1L-ujx4bKqxAY6RO6E1JE0_7uocB_X8pQVzu-O-WvxWHq29Vdp"
          />

        </div>

        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-transparent pointer-events-none"></div>

      </div>
    </section>
  );
}
