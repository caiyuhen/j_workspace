import React from "react";
import { TrafficLightCell } from "./TrafficLightCell";
import type { RoB2Overall, TrafficLightRating } from "@meda/shared-sdk";

export type RoB2MatrixProps = {
  studies: RoB2Overall[];
  editable?: boolean;
  onCellChange?: (studyId: string, domain: string, rating: TrafficLightRating) => void;
  gradeDowngrade?: "-1" | "-2" | "0";
};

const DOMAIN_KEYS = [
  { key: "D1_randomization", label: "D1" },
  { key: "D2_deviations", label: "D2" },
  { key: "D3_missing", label: "D3" },
  { key: "D4_measurement", label: "D4" },
  { key: "D5_reporting", label: "D5" },
] as const;

export function RoB2Matrix({
  studies,
  editable = false,
  onCellChange,
  gradeDowngrade,
}: RoB2MatrixProps): JSX.Element {
  const getDomainRating = (study: RoB2Overall, domainKey: string): TrafficLightRating => {
    const found = study.domains.find((d) => d.domain === domainKey);
    return found?.rating ?? "ni";
  };

  return (
    <div className="rob2-matrix-wrapper" style={{ overflowX: "auto" }}>
      <style>{`
        .rob2-matrix table { border-collapse: collapse; width: 100%; font-family: system-ui; }
        .rob2-matrix th, .rob2-matrix td {
          padding: 0.5rem 0.75rem;
          text-align: center;
          border: 1px solid #e5e7eb;
          font-size: 0.875rem;
        }
        .rob2-matrix thead th {
          background: #f9fafb;
          font-weight: 700;
        }
        .rob2-matrix .rob2-study-cell {
          text-align: left;
          font-weight: 600;
          background: #fafafa;
        }
        .rob2-matrix .rob2-overall-col {
          border-left: 3px solid #374151;
          border-right: 3px solid #374151;
          background: #f3f4f6;
        }
        .rob2-matrix thead th.rob2-overall-col {
          border-top: 3px solid #374151;
        }
        .rob2-matrix tbody tr:last-child td.rob2-overall-col {
          border-bottom: 3px solid #374151;
        }
        .rob2-matrix .rob2-grade-badge {
          display: inline-flex;
          align-items: center;
          margin-left: 0.5rem;
          padding: 0.125rem 0.5rem;
          background: #fef3c7;
          color: #92400e;
          border-radius: 9999px;
          font-weight: 700;
          font-size: 0.75rem;
          font-family: system-ui;
        }
        .rob2-matrix .rob2-title-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 0.5rem;
        }
        .rob2-matrix .robins-i-btn {
          display: inline-flex;
          align-items: center;
          gap: 0.25rem;
          padding: 0.25rem 0.5rem;
          background: #e0e7ff;
          color: #3730a3;
          border: 1px solid #c7d2fe;
          border-radius: 0.375rem;
          font-size: 0.75rem;
          font-weight: 600;
          cursor: pointer;
          font-family: system-ui;
        }
      `}</style>
      <div className="rob2-matrix">
        <div className="rob2-title-row">
          <div style={{ fontWeight: 700, fontSize: "1rem" }}>
            RoB 2 Quality Matrix
            {gradeDowngrade !== undefined && (
              <span className="rob2-grade-badge">RoB {gradeDowngrade}</span>
            )}
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th className="rob2-study-cell">studyId</th>
              {DOMAIN_KEYS.map((d) => (
                <th key={d.key}>{d.label}</th>
              ))}
              <th className="rob2-overall-col">Overall</th>
            </tr>
          </thead>
          <tbody>
            {studies.map((study) => {
              const isNRSI = study.study_type === "NRSI";
              return (
                <tr key={study.study_id}>
                  <td className="rob2-study-cell">{study.study_id}</td>
                  {DOMAIN_KEYS.map((d) => {
                    const rating = getDomainRating(study, d.key);
                    const handleClick = editable && onCellChange
                      ? () => onCellChange(study.study_id, d.key, rating)
                      : undefined;
                    const lockedStyle: React.CSSProperties | undefined = !editable ? { pointerEvents: "none" } : undefined;
                    return (
                      <td key={d.key}>
                        {isNRSI ? (
                          <button
                            type="button"
                            className="robins-i-btn"
                            onClick={handleClick}
                          >
                            ↪️ ROBINS-I
                          </button>
                        ) : (
                          <TrafficLightCell
                            rating={rating}
                            size="sm"
                            onClick={handleClick}
                          />
                        )}
                      </td>
                    );
                  })}
                  <td className="rob2-overall-col">
                    <TrafficLightCell rating={study.overall} size="md" />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export { TrafficLightCell };
