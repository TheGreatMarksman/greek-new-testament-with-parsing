import { getData } from "@/lib/data";
import CsvClient from "./CsvClient";

export default function Page() {
    const data = getData();

    return <CsvClient data={data} />;
}