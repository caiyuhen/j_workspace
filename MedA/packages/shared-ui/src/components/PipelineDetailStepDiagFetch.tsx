import React from "react";
import { useStepDiag, type InjectDiagClient } from "../hooks/useStepDiag";
import DedupDiagCards from "./DedupDiagCards";

export interface PipelineDetailStepDiagFetchProps {
  workspaceId: string;
  runId: string;
  stepIndex: number;
  stepStatus: string;
  intervalMs?: number;
  injectFetchClient?: Partial<InjectDiagClient>;
}

export function PipelineDetailStepDiagFetch(
  props: PipelineDetailStepDiagFetchProps,
): JSX.Element {
  const { workspaceId, runId, stepIndex, stepStatus, intervalMs, injectFetchClient } = props;

  if (stepStatus !== "success") {
    return (
      <div data-testid="dedupdiag-section">
        <div
          data-testid="diag-section"
          style={{
            padding: 16,
            background: "#fff",
            borderRadius: 8,
            border: "1px solid #e5e7eb",
            marginBottom: 20,
          }}
        >
          <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>🔬 Step 1 去重诊断</div>
          <div
            data-testid="diag-not-generated"
            style={{
              padding: 24,
              background: "#f3f4f6",
              borderRadius: 6,
              border: "1px dashed #d1d5db",
              color: "#6b7280",
              fontSize: 13,
              textAlign: "center",
            }}
          >
            诊断数据暂未生成
          </div>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="dedupdiag-section">
      <_DiagSectionLoaded {...props} />
    </div>
  );
}

function _DiagSectionLoaded(
  props: PipelineDetailStepDiagFetchProps,
): JSX.Element {
  const { workspaceId, runId, stepIndex, stepStatus, intervalMs, injectFetchClient } = props;
  const { state } = useStepDiag({
    workspaceId,
    runId,
    stepIndex,
    stepStatus,
    intervalMs,
    injectFetchClient,
  });
  const { diag, error, loading } = state;

  let banner: JSX.Element | null = null;
  let diagError: string | null = null;
  let showCards = false;

  if (error) {
    if (error.code === "AUTH_FAILED") {
      banner = (
        <div
          data-testid="diag-banner-auth"
          style={{
            padding: 12,
            background: "#fef2f2",
            borderRadius: 6,
            border: "1px solid #ef4444",
            color: "#991b1b",
            fontSize: 13,
            fontWeight: 600,
            marginBottom: 12,
          }}
        >
          认证失败
        </div>
      );
    } else if (error.code === "FORBIDDEN") {
      banner = (
        <div
          data-testid="diag-banner-forbidden"
          style={{
            padding: 12,
            background: "#fef2f2",
            borderRadius: 6,
            border: "1px solid #ef4444",
            color: "#991b1b",
            fontSize: 13,
            fontWeight: 600,
            marginBottom: 12,
          }}
        >
          鉴权失败
        </div>
      );
    } else if (error.code === "DIAG_NOT_WRITTEN") {
      banner = (
        <div
          data-testid="diag-banner-not-written"
          style={{
            padding: 12,
            background: "#fef9c3",
            borderRadius: 6,
            border: "1px solid #eab308",
            color: "#92400e",
            fontSize: 13,
            fontWeight: 600,
            marginBottom: 12,
          }}
        >
          诊断数据缺失
        </div>
      );
    }
  }

  let content: JSX.Element;
  if (diag) {
    showCards = true;
  } else if (error && error.code === "DIAG_NOT_READY") {
    content = (
      <div
        data-testid="diag-not-ready"
        style={{
          padding: 24,
          background: "#f3f4f6",
          borderRadius: 6,
          border: "1px dashed #9ca3af",
          color: "#6b7280",
          fontSize: 13,
          textAlign: "center",
        }}
      >
        step 诊断尚未写入
      </div>
    );
  }

  return (
    <div
      data-testid="diag-section"
      style={{
        padding: 16,
        background: "#fff",
        borderRadius: 8,
        border: "1px solid #e5e7eb",
        marginBottom: 20,
      }}
    >
      <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>🔬 Step 1 去重诊断</div>
      {banner}
      {showCards && diag ? (
        <DedupDiagCards diag={diag} diagLoading={loading} diagError={diagError} />
      ) : (
        content!
      )}
    </div>
  );
}

export default PipelineDetailStepDiagFetch;
