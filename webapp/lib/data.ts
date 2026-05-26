import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";

export function getData() {
    const filePath = path.join(
        process.cwd(),
        "data",
        "word_classification.csv"
    );

    const fileContent = fs.readFileSync(
        filePath,
        "utf-8"
    );

    const records = parse(fileContent, {
        columns: true,
        skip_empty_lines: true,
        bom:true
    });

    return records;
}