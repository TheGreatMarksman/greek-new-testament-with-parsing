export default function HomePage() {
    return (
        <main className="p-8">
            <h1>Hello World</h1>
        </main>
    );
}

{/*

import { getData } from "@/lib/data";

type CSVRow = Record<string, string>;

export default function HomePage() {
    const data = getData() as CSVRow[];

    return (
        <main className="p-8">
            <h1 className="text-3xl font-bold mb-6">
                CSV Data
            </h1>

            <div className="space-y-4">
                {data.map((row, index) => (
                    <div
                        key={index}
                        className="border p-4 rounded"
                    >
                        {Object.entries(row).map(
                            ([key, value]) => (
                                <div key={key}>
                                    <strong>{key}:</strong>{" "}
                                    {String(value)}
                                </div>
                            )
                        )}
                    </div>
                ))}
            </div>
        </main>
    );
}
*/}