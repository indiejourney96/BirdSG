import UploadBox from "@/components/identify/UploadBox";

export default function IdentifyPage() {
  return (
    <main className="min-h-screen p-8 bg-[#f9faf2]">

      <h1 className="text-4xl font-bold mb-6 text-green-900">
        Bird Identifier
      </h1>

      <UploadBox />

    </main>
  );
}