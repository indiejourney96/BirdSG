import UploadBox from "@/components/identify/UploadBox";

export default function IdentifyPage() {
  return (
    <main className="min-h-screen p-6">
      <h1 className="text-3xl font-bold mb-6">
        Identify Bird
      </h1>

      <UploadBox />
    </main>
  );
}