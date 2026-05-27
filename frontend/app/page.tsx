// frontend/app/page.tsx
"use client";

import { useState } from "react";
import Hero from "@/components/home/Hero";
import IdentifyCard from "@/components/home/IdentifyCard";
import PredictionResults from "@/components/home/PredictionResults";
import Hotspots from "@/components/home/Hotspots";
import RecentSightings from "@/components/home/RecentSightings";
import BottomNav from "@/components/home/BottomNav";
import Header from "@/components/home/Header";

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

export default function Home() {
  // Local state to maintain the server result hook
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);

  return (
    <>
    <Header />
      <main className="pt-24 px-margin-mobile max-w-screen-xl mx-auto pb-32">
        <Hero />
        
        {/* Conditional View Switching Logic */}
        {!analysisResult ? (
          <IdentifyCard onPredictionSuccess={(data) => setAnalysisResult(data)} />
        ) : (
          <PredictionResults 
            data={analysisResult} 
            onReset={() => setAnalysisResult(null)} 
          />
        )}

        <RecentSightings />
        <Hotspots />
      </main>
      
      <BottomNav />
    </>
  );
}
