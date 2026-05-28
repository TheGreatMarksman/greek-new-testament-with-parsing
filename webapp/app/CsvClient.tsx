"use client";

import { useMemo, useState } from "react";

type CSVRow = Record<string, string>;

const PAGE_SIZE = 50;

export default function CsvClient({ data }: { data: CSVRow[] }) {
    const [columnFilters, setColumnFilters] = useState<
        Record<string, string | null>
    >({});
    const [search, setSearch] = useState("");
    const [page, setPage] = useState(0);
    const [sort, setSort] = useState<{
        key: string;
        dir: "asc" | "desc";
    } | null>(null);

    const buttonBase = "px-2 py-1 rounded text-sm";

    const buttonRed = "text-white bg-red-500 hover:bg-red-700";

    const buttonGreen = "text-white bg-green-500 hover:bg-green-700";

    const buttonGray = "text-white bg-gray-400 hover:bg-gray-600";

    const [hiddenColumns, setHiddenColumns] = useState<string[]>([
        "total_word_index",
        "mono_LC",
        "betacode",
        "std_poly_LC",
        "lemma",
        "str_num",
        "root_1",
        "root_2",
        "root_3",
        "alt_1_str_num",
        "alt_2_str_num",
        "rp_code",
        "rp_alt_code",
        "rp_pos",
        "rp_gender",
        "rp_alt_gender",
        "rp_number",
        "rp_word_case",
        "rp_alt_word_case",
        "rp_tense",
        "rp_type",
        "rp_voice",
        "rp_mood",
        "rp_alt_mood",
        "rp_person",
        "rp_indeclinable",
        "rp_why_indeclinable",
        "rp_kai_crasis",
        "rp_attic_greek_form",
    ]);

    const formatValue = (v: string) => {
        if (!v) return "";

        // detect float-like numbers
        if (/^-?\d+\.\d+$/.test(v)) {
            return String(parseFloat(v));
        }

        return v;
    };

    const columns = useMemo(() => {
        return data.length ? Object.keys(data[0]) : [];
    }, [data]);

    const columnValues = useMemo(() => {
        const map: Record<string, Set<string>> = {};

        for (const col of columns) {
            map[col] = new Set();
        }

        for (const row of data) {
            for (const col of columns) {
                map[col].add(String(row[col] ?? ""));
            }
        }

        const result: Record<string, string[]> = {};

        for (const col of columns) {
            result[col] = Array.from(map[col]).sort();
        }

        return result;
    }, [data, columns]);

    // FILTER
    const filtered = useMemo(() => {
        return data.filter((row) => {
            // global search
            const matchesSearch =
                !search ||
                Object.values(row).some((v) =>
                    String(v).toLowerCase().includes(search.toLowerCase())
                );

            // column filters
            const matchesColumns = Object.entries(columnFilters).every(
                ([col, value]) => {
                    if (!value) return true;
                    return String(row[col]) === value;
                }
            );

            return matchesSearch && matchesColumns;
        });
    }, [data, search, columnFilters]);

    // SORT
    const sorted = useMemo(() => {
        if (!sort) return filtered;

        return [...filtered].sort((a, b) => {
            const av = String(a[sort.key] ?? "");
            const bv = String(b[sort.key] ?? "");

            if (av < bv) return sort.dir === "asc" ? -1 : 1;
            if (av > bv) return sort.dir === "asc" ? 1 : -1;
            return 0;
        });
    }, [filtered, sort]);

    // PAGINATION
    const totalPages = Math.ceil(sorted.length / PAGE_SIZE);

    const pageData = useMemo(() => {
        const start = page * PAGE_SIZE;
        return sorted.slice(start, start + PAGE_SIZE);
    }, [sorted, page]);

    const [selectedRow, setSelectedRow] = useState<CSVRow | null>(null);

    function toggleColumn(col: string) {
        setHiddenColumns((prev) =>
            prev.includes(col)
                ? prev.filter((c) => c !== col)
                : [...prev, col]
        );
    }

    return (
        <div className="p-4 space-y-4">
            <input
                className="border p-2 w-full max-w-md"
                placeholder="Search..."
                value={search}
                onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(0);
                }}
            />
            <div className="flex flex-wrap gap-2">
                {hiddenColumns.map((col) => (
                    <button
                        key={col}
                        onClick={() => toggleColumn(col)}
                        //className="border px-2 py-1 text-sm"
                        className={`${buttonBase} ${buttonGray}`}
                    >
                        Show {col}
                    </button>
                ))}
            </div>
            <div className="border overflow-auto max-h-[70vh]">
                <table className="min-w-full text-sm">
                    <thead className="bg-gray-100 sticky top-0">
                        <tr>
                            {columns
                                .filter((col) => !hiddenColumns.includes(col))
                                .map((col) => (
                                    <th key={col} className="p-2 border">
                                        <div className="flex items-center gap-2">
                                            <span>{col}</span>

                                            <button
                                                onClick={() => toggleColumn(col)}
                                                className="text-xs border px-1 hover:bg-gray-200"
                                            >
                                                Hide
                                            </button>
                                        </div>

                                        <select
                                            value={columnFilters[col] ?? ""}
                                            onChange={(e) =>
                                                setColumnFilters((prev) => ({
                                                    ...prev,
                                                    [col]: e.target.value || null,
                                                }))
                                            }
                                            className="text-xs border mt-1"
                                        >
                                            <option value="">All</option>

                                            {columnValues[col]
                                                ?.filter((v) => v && v.trim() !== "")
                                                .slice(0, 200)
                                                .map((v) => (
                                                    <option key={v} value={v}>
                                                        {v}
                                                    </option>
                                                ))
                                            }
                                        </select>
                                    </th>
                                ))
                            }
                        </tr>
                    </thead>

                    <tbody>
                        {pageData.map((row, i) => (
                            <tr
                                key={i}
                                className={`border-t cursor-pointer ${
                                    selectedRow === row
                                        ? "bg-blue-100"
                                        : "hover:bg-gray-100"
                                }`}
                                onClick={() =>
                                    setSelectedRow((prev) =>
                                        prev === row ? null : row
                                    )
                                }
                            >
                                {columns
                                    .filter((col) => !hiddenColumns.includes(col))
                                    .map((col) => (
                                        <td key={col} className="p-2">
                                            {formatValue(String(row[col] ?? ""))}
                                        </td>
                                    ))
                                }
                                <td className="hidden group-hover:block absolute left-full top-0 z-10 bg-white border p-3 shadow-lg min-w-[300px]">
                                    <div className="space-y-1">
                                        {columns.map((col) => (
                                            <div key={col}>
                                                <strong>{col}:</strong>{" "}
                                                {String(row[col] ?? "")}
                                            </div>
                                        ))}
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {selectedRow && (
                <div className="fixed right-4 top-4 w-[350px] max-h-[80vh] overflow-auto border bg-white shadow-lg p-4 z-50">
                    <button
                        onClick={() => setSelectedRow(null)}
                        className={`${buttonBase} ${buttonGray}`}
                    >
                        Close
                    </button>
                    <h2 className="font-bold mb-2">
                        Row Details
                    </h2>

                    <div className="space-y-1 text-sm">
                        {hiddenColumns
                            .filter((col) => {
                                const value = selectedRow[col];
                                return value !== null && value !== undefined && String(value).trim() !== "";
                            })
                            .map((col) => (
                                <div key={col}>
                                    <strong>{col}:</strong>{" "}
                                    {String(selectedRow[col])}
                                </div>
                            ))
                        }
                    </div>
                </div>
            )}

            <div className="flex gap-2 items-center">
                <button
                    onClick={() => setPage((p) => Math.max(p - 1, 0))}
                    disabled={page === 0}
                    className={`${buttonBase} ${buttonGray}`}
                >
                    Prev
                </button>

                <span>
                    Page {page + 1} / {totalPages || 1}
                </span>

                <button
                    onClick={() =>
                        setPage((p) => Math.min(p + 1, totalPages - 1))
                    }
                    disabled={page >= totalPages - 1}
                    className={`${buttonBase} ${buttonGray}`}
                >
                    Next
                </button>
            </div>
        </div>
    );
}