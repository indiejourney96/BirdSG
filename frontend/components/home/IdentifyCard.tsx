// frontend/components/home/IdentifyCard.tsx
"use client";
import { useState } from "react";
import { predictBird } from "@/lib/api";

interface IdentifyCardProps {
  onPredictionSuccess: (data: any) => void;
}

export default function IdentifyCard({ onPredictionSuccess }: IdentifyCardProps) {
  const [loading, setLoading] = useState(false);

  async function handleUpload(file: File) {
    try {
      setLoading(true);
      const data = await predictBird(file);
      
      // Pass the complete server dataset upward to layout parent container
      onPredictionSuccess(data);
    } catch (error) {
      console.error(error);
      alert("Prediction failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="mb-xl">
      <div className="relative overflow-hidden rounded-xl bg-primary-container text-on-primary-container p-lg shadow-lg flex flex-col md:flex-row items-center justify-between gap-md group">
        <div className="z-10 text-center md:text-left flex-1">
          <h3 className="font-headline-md text-headline-md mb-2 text-on-primary-container">Identify Bird</h3>
          <p className="font-body-md text-body-md opacity-90 mb-lg">Point your camera to instantly identify species and log your encounter.</p>
          
          <label className="inline-flex items-center gap-2 bg-on-primary text-primary px-lg py-sm rounded-full font-label-md text-label-md shadow-md cursor-pointer hover:opacity-90 transition-opacity">
            <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>photo_camera</span>
            {loading ? "Analyzing Specimen..." : "Launch Scanner"}
            <input
              type="file"
              accept="image/*"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleUpload(file);
              }}
              className="hidden"
            />
          </label>
        </div>
        
        <div className="relative w-full md:w-1/3 aspect-square md:aspect-video rounded-lg overflow-hidden shadow-xl border-4 border-white/10">
          <img alt="Identification interface" className="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBtgJ1H3Ojo3nC4c6GX1HdvddBmuhuWZOSv35YgUcjnhAl_smIddDRSoHBVGKNDxqjXoA_OZuQ4RX7WMS2leABt_of0OxQSjeNYzy7Vh_LrfdH5hBfWgZp7NhC57toVWfNS-HaeuxBFxQ5p8NwRaSKi5ETu06Y4bhs3mTt0Hq_fBu4RbtThbDTAdwPap7CYVXjyJHWOek6AQoRHf7_gXk3FA-t_v_1L-ujx4bKqxAY6RO6E1JE0_7uocB_X8pQVzu-O-WvxWHq29Vdp" />
        </div>
        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-transparent pointer-events-none"></div>
      </div>
    </section>
  );
}