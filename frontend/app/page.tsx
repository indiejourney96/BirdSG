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


export default function Home() {
  // Local state to maintain the server result hook
  const [analysisResult, setAnalysisResult] = useState<any>(null);

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