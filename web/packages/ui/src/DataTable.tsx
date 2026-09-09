"use client";

import type { ReactNode } from "react";
import { useT } from "@saarthi/i18n";

export type DataTableRow = Record<string, ReactNode>;

export type DataTableColumn<R extends DataTableRow> = {
  key: string;
  labelKey: string;
  align?: "start" | "center" | "end";
  /** Optional cell renderer; without it the cell is `row[key]`. */
  render?: (row: R) => ReactNode;
};

export type DataTableProps<R extends DataTableRow> = {
  columns: DataTableColumn<R>[];
  rows: R[];
  emptyKey: string;
  onRowClick?: (row: R) => void;
  /** Screen-reader caption; defaults to the column labels. */
  captionKey?: string;
  /** Stable React key per row; defaults to the row index. */
  rowKey?: (row: R, index: number) => string;
};

/**
 * Semantic <table> in its own horizontal scroll container, so a wide console
 * table never makes the whole page scroll sideways (320px reflow, design.md §9).
 * When `onRowClick` is given the first cell becomes a real <button> — a row is
 * never a div with a click handler.
 */
export function DataTable<R extends DataTableRow>({
  columns,
  rows,
  emptyKey,
  onRowClick,
  captionKey,
  rowKey,
}: DataTableProps<R>) {
  const { t } = useT();
  const caption = captionKey ? t(captionKey) : columns.map((c) => t(c.labelKey)).join(", ");

  return (
    <div className="sa-table-scroll" role="region" aria-label={caption} tabIndex={0}>
      <table className="sa-table">
        <caption className="sa-sr-only">{caption}</caption>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} scope="col" className={`sa-table__th sa-table__cell--${c.align ?? "start"}`}>
                {t(c.labelKey)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td className="sa-table__empty" colSpan={Math.max(1, columns.length)}>
                {t(emptyKey)}
              </td>
            </tr>
          ) : (
            rows.map((row, i) => (
              <tr key={rowKey ? rowKey(row, i) : i} className="sa-table__row">
                {columns.map((c, ci) => {
                  const content = c.render ? c.render(row) : row[c.key];
                  return (
                    <td key={c.key} className={`sa-table__td sa-table__cell--${c.align ?? "start"}`}>
                      {onRowClick && ci === 0 ? (
                        <button type="button" className="sa-table__rowbtn" onClick={() => onRowClick(row)}>
                          {content}
                        </button>
                      ) : (
                        content
                      )}
                    </td>
                  );
                })}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
