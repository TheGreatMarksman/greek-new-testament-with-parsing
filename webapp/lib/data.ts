import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";

const filePath = path.join(process.cwd(), "data", "word_classification.csv");

let cachedData: Record<string, string>[] | null = null;

export function getData(): Record<string, string>[] {
    if (cachedData) {
        return cachedData;
    }

    const fileContent = fs.readFileSync(filePath, "utf-8");

    cachedData = parse(fileContent, {
        columns: true,
        skip_empty_lines: true,
        bom: true,
    });

    return cachedData;
}