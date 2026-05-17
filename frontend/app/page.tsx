import Header from "@/components/home/Header";
import Hero from "@/components/home/Hero";
import IdentifyCard from "@/components/home/IdentifyCard";
import RecentSightings from "@/components/home/RecentSightings";
import Hotspots from "@/components/home/Hotspots";
import BottomNav from "@/components/home/BottomNav";

export default function Home() {
  return (
    <>
      <Header />
      <main className="pt-24 px-margin-mobile max-w-screen-xl mx-auto">
        <Hero />
        <IdentifyCard />
        <RecentSightings />
        <Hotspots />
      </main>
      <BottomNav />
    </>
  );
}