from flask import Flask, request, jsonify, render_template_string
import pandas as pd
from src.schema import FeatureSchema
from src.inference import (
    load_model_bundle,
    load_transformer_bundle,
    predict_multi_risk,
    predict_transformer_risk,
    risk_level,
)


app = Flask(__name__)
schema = FeatureSchema()
TEST_PAGE_HTML = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>慢病风险 API 测试页面</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; background: #f5f7fb; color: #222; }
    .wrap { max-width: 1200px; margin: 0 auto; }
    .card { background: #fff; border-radius: 10px; padding: 18px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin-bottom: 16px; }
    h1 { margin: 0 0 12px; font-size: 24px; }
    h2 { margin: 0 0 10px; font-size: 18px; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    textarea { width: 100%; min-height: 360px; border: 1px solid #d9dfeb; border-radius: 8px; padding: 12px; font-family: Consolas, monospace; font-size: 13px; }
    button { background: #2866f6; border: none; color: #fff; border-radius: 8px; padding: 10px 16px; cursor: pointer; margin-right: 8px; }
    button.secondary { background: #5f6b7a; }
    .status { margin-top: 10px; font-size: 14px; }
    pre { background: #111827; color: #f3f4f6; border-radius: 8px; padding: 12px; overflow-x: auto; min-height: 340px; }
    .ok { color: #0a7d2c; }
    .err { color: #b91c1c; }
    @media (max-width: 900px) { .row { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>慢病风险 API 测试页面</h1>
      <div>接口：<code>POST /api/predict</code>，健康检查：<code>GET /health</code></div>
    </div>
    <div class="row">
      <div class="card">
        <h2>请求体（可编辑）</h2>
        <textarea id="payload" spellcheck="false"></textarea>
        <div style="margin-top: 10px;">
          <button id="btnDemo">填充示例</button>
          <button id="btnZero">全零/缺省</button>
          <button id="btnThSoft">阈值覆盖-温和</button>
          <button id="btnClear">清空</button>
          <button id="btnSend">发送请求</button>
          <button class="secondary" id="btnHealth">健康检查</button>
        </div>
        <div id="status" class="status"></div>
      </div>
      <div class="card">
        <h2>响应结果</h2>
        <pre id="result"></pre>
      </div>
      <div class="card">
        <h2>请求详情</h2>
        <pre id="requestDetail"></pre>
      </div>
    </div>
  </div>
  <script>
    function fmt(obj) {
      return JSON.stringify(obj, null, 2);
    }
    function dateStr(offset) {
      const d = new Date();
      d.setDate(d.getDate() + offset);
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, "0");
      const day = String(d.getDate()).padStart(2, "0");
      return `${y}-${m}-${day}`;
    }
    function buildRecord(examDate, systolic, glucose, crp) {
      return {
        patient_id: "P_TEST_001",
        exam_date: examDate,
        age: 56,
        gender: 1,
        ethnicity: 1,
        education_years: 12,
        socioeconomic_score: 6,
        atrial_fibrillation: 0,
        previous_stroke: 0,
        previous_tia: 0,
        heart_disease: 0,
        diabetes_years: 3,
        hypertension_years: 5,
        hypertension_controlled: 1,
        chronic_kidney_disease: 0,
        peripheral_artery_disease: 0,
        family_stroke_history: 1,
        family_heart_disease: 1,
        genetic_risk_score: 5,
        carotid_plaque: 0,
        white_matter_lesions: 0,
        systolic_bp: systolic,
        diastolic_bp: 82,
        total_cholesterol: 192,
        hdl_cholesterol: 48,
        ldl_cholesterol: 118,
        triglycerides: 150,
        fasting_glucose: glucose,
        hba1c: 6.1,
        bmi: 26.2,
        waist_circumference: 92,
        waist_hip_ratio: 0.93,
        heart_rate: 74,
        alcohol_units_week: 2,
        physical_activity_days: 4,
        mediterranean_diet_score: 8,
        sleep_hours: 7,
        crp: crp,
        fibrinogen: 320,
        left_ventricular_ejection: 60,
        avg_systolic_bp_24h: 128,
        bp_variability: 9,
        heart_rate_variability: 28,
        daily_steps: 7800,
        sleep_efficiency: 83,
        air_quality: 56,
        season: 1
      };
    }
    function demoPayload() {
      const records = [
        buildRecord(dateStr(-6), 122, 98, 1.2),
        buildRecord(dateStr(-5), 124, 100, 1.1),
        buildRecord(dateStr(-4), 126, 102, 1.3),
        buildRecord(dateStr(-3), 128, 104, 1.4),
        buildRecord(dateStr(-2), 130, 105, 1.6),
        buildRecord(dateStr(-1), 132, 107, 1.7),
        buildRecord(dateStr(0), 134, 108, 1.9)
      ];
      return {
        model_type: "xgb_multi",
        records: records
      };
    }
    function zeroRecord(examDate) {
      return {
        patient_id: "P_ZERO",
        exam_date: examDate,
        age: 0,
        gender: 0,
        ethnicity: 0,
        education_years: 0,
        socioeconomic_score: 0,
        atrial_fibrillation: 0,
        previous_stroke: 0,
        previous_tia: 0,
        heart_disease: 0,
        diabetes_years: 0,
        hypertension_years: 0,
        hypertension_controlled: 0,
        chronic_kidney_disease: 0,
        peripheral_artery_disease: 0,
        family_stroke_history: 0,
        family_heart_disease: 0,
        genetic_risk_score: 0,
        carotid_plaque: 0,
        white_matter_lesions: 0,
        systolic_bp: 0,
        diastolic_bp: 0,
        total_cholesterol: 0,
        hdl_cholesterol: 0,
        ldl_cholesterol: 0,
        triglycerides: 0,
        fasting_glucose: 0,
        hba1c: 0,
        bmi: 0,
        waist_circumference: 0,
        waist_hip_ratio: 0,
        heart_rate: 0,
        alcohol_units_week: 0,
        physical_activity_days: 0,
        mediterranean_diet_score: 0,
        sleep_hours: 0,
        crp: 0,
        fibrinogen: 0,
        left_ventricular_ejection: 0,
        avg_systolic_bp_24h: 0,
        bp_variability: 0,
        heart_rate_variability: 0,
        daily_steps: 0,
        sleep_efficiency: 0,
        air_quality: 0,
        season: 0
      };
    }
    function zeroPayload() {
      return {
        model_type: "xgb_multi",
        records: [ zeroRecord(dateStr(0)) ]
      };
    }
    function thresholdPayloadSoft() {
      const base = demoPayload();
      base.thresholds = {
        stroke: [0.2, 0.4, 0.6],
        depression: [0.2, 0.4, 0.6],
        anxiety: [0.7, 0.85, 0.95],
        diabetes: [0.4, 0.6, 0.8],
        hypertension: [0.4, 0.6, 0.8],
        parkinson: [0.4, 0.6, 0.8],
        arrhythmia: [0.3, 0.5, 0.7],
        kidney_disease: [0.3, 0.5, 0.7],
        alzheimer: [0.3, 0.5, 0.7],
        coronary_heart_disease: [0.3, 0.5, 0.7],
        gout: [0.3, 0.5, 0.7],
        heart_failure: [0.4, 0.6, 0.8],
        asthma: [0.3, 0.5, 0.7],
        bronchiectasis: [0.3, 0.5, 0.7]
      };
      return base;
    }
    async function sendPredict() {
      const status = document.getElementById("status");
      const result = document.getElementById("result");
      const req = document.getElementById("requestDetail");
      try {
        const payload = JSON.parse(document.getElementById("payload").value);
        status.className = "status";
        status.textContent = "请求中...";
        const url = "/api/predict";
        const headers = { "Content-Type": "application/json" };
        const body = JSON.stringify(payload);
        req.textContent = fmt({ method: "POST", url, headers, body: payload });
        const resp = await fetch(url, {
          method: "POST",
          headers,
          body
        });
        const text = await resp.text();
        let data;
        try {
          data = JSON.parse(text);
        } catch (_) {
          data = { success: false, error: "non_json_response", raw: text.slice(0, 1000) };
        }
        result.textContent = fmt(data);
        if (resp.ok) {
          status.className = "status ok";
          status.textContent = "请求成功";
        } else {
          status.className = "status err";
          status.textContent = `请求失败，HTTP ${resp.status}`;
        }
      } catch (e) {
        status.className = "status err";
        status.textContent = `请求异常：${e.message}`;
      }
    }
    async function checkHealth() {
      const status = document.getElementById("status");
      const result = document.getElementById("result");
      try {
        const resp = await fetch("/health");
        const data = await resp.json();
        result.textContent = fmt(data);
        status.className = "status ok";
        status.textContent = "健康检查成功";
      } catch (e) {
        status.className = "status err";
        status.textContent = `健康检查失败：${e.message}`;
      }
    }
    function fillDemo() {
      document.getElementById("payload").value = fmt(demoPayload());
    }
    function fillZero() {
      document.getElementById("payload").value = fmt(zeroPayload());
    }
    function clearPayload() {
      document.getElementById("payload").value = "";
      document.getElementById("requestDetail").textContent = "";
      document.getElementById("result").textContent = "";
      const status = document.getElementById("status");
      status.className = "status";
      status.textContent = "";
    }
    function fillThSoft() {
      document.getElementById("payload").value = fmt(thresholdPayloadSoft());
    }
    document.getElementById("btnSend").addEventListener("click", sendPredict);
    document.getElementById("btnHealth").addEventListener("click", checkHealth);
    document.getElementById("btnDemo").addEventListener("click", fillDemo);
    document.getElementById("btnZero").addEventListener("click", fillZero);
    document.getElementById("btnThSoft").addEventListener("click", fillThSoft);
    document.getElementById("btnClear").addEventListener("click", clearPayload);
    fillDemo();
  </script>
</body>
</html>
"""


def select_model_variant():
    variant = request.headers.get("X-Model-Variant", "A")
    return variant.upper()


@app.route("/", methods=["GET"])
def index():
    return render_template_string(TEST_PAGE_HTML)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})


@app.route("/api/predict", methods=["POST"])
def predict():
    try:
        payload = request.get_json()
        if payload is None or "records" not in payload:
            return jsonify({"success": False, "error": "records_missing"}), 400
        records = payload["records"]

        # 数据类型转换逻辑
        non_numeric_fields = {"patient_id", "exam_date"}
        for i, record in enumerate(records):
            for key, value in record.items():
                # 自动识别需要转换为数字类型的目标字段（排除已知的非数值字段）
                if key not in non_numeric_fields and isinstance(value, str):
                    try:
                        f_val = float(value)
                        # 根据字段数值特点转换为整数或浮点数
                        if f_val.is_integer():
                            record[key] = int(f_val)
                        else:
                            record[key] = f_val
                    except ValueError:
                        # 异常捕获机制，处理无法转换为合法数字的场景并记录错误
                        error_msg = f"字段 '{key}' 的值 '{value}' 无法转换为合法的数字类型。"
                        app.logger.error(f"参数错误: {error_msg}")  # 记录错误日志
                        return jsonify({
                            "success": False, 
                            "error": "invalid_parameter", 
                            "message": error_msg
                        }), 400

        df = pd.DataFrame(records)
        model_type = payload.get("model_type", "xgb_multi")
        requested_thresholds = payload.get("thresholds")
        variant = select_model_variant()
        if model_type == "transformer":
            bundle_7d = load_transformer_bundle(f"models/transformer_7d_{variant}.pt")
            bundle_30d = load_transformer_bundle(f"models/transformer_30d_{variant}.pt")
            bundle_thresholds = bundle_7d.get("thresholds") or schema.risk_thresholds
            preds_7d, top_factors = predict_transformer_risk(df, schema, bundle_7d, 7)
            preds_30d, _ = predict_transformer_risk(df, schema, bundle_30d, 30)
        else:
            bundle_7d = load_model_bundle(f"models/xgb_multi_7d_{variant}.joblib")
            bundle_30d = load_model_bundle(f"models/xgb_multi_30d_{variant}.joblib")
            bundle_thresholds = bundle_7d.get("thresholds") or schema.risk_thresholds
            preds_7d, top_factors = predict_multi_risk(df, schema, bundle_7d, 7, top_k=5)
            preds_30d, _ = predict_multi_risk(df, schema, bundle_30d, 30, top_k=5)
        latest_7d = preds_7d.sort_values(schema.date_col).iloc[-1]
        latest_30d = preds_30d.sort_values(schema.date_col).iloc[-1]
        disease_thresholds = dict(bundle_thresholds)
        if requested_thresholds:
            for disease, thresholds in requested_thresholds.items():
                if thresholds is not None:
                    disease_thresholds[disease] = tuple(thresholds)
        predictions = {}
        for disease in schema.target_cols:
            thresholds = disease_thresholds.get(disease, schema.risk_thresholds.get(disease))
            risk_7d = float(latest_7d.get(f"risk_{disease}_7d", 0.0))
            risk_30d = float(latest_30d.get(f"risk_{disease}_30d", 0.0))
            level_7d = risk_level(risk_7d, thresholds)
            level_30d = risk_level(risk_30d, thresholds)
            recommendations = schema.risk_recommendations.get(disease, {})
            predictions[disease] = {
                "risk_7d": risk_7d,
                "risk_30d": risk_30d,
                "risk_level_7d": level_7d,
                "risk_level_30d": level_30d,
                "thresholds": thresholds,
                "recommendations_7d": recommendations.get(level_7d, []),
                "recommendations_30d": recommendations.get(level_30d, []),
            }
        top_factors_list = [
            {"disease": disease, "factors": top_factors.get(disease, [])}
            for disease in schema.target_cols
        ]
        result = {
            "success": True,
            "predictions": predictions,
            "top_factors": top_factors_list,
            "model_variant": variant,
            "model_type": model_type,
        }
        return jsonify(result)
    except FileNotFoundError as e:
        return jsonify(
            {
                "success": False,
                "error": "model_not_found",
                "message": str(e),
                "hint": "请先训练并导出模型到 models 目录，例如运行 scripts/train.py",
            }
        ), 500
    except Exception as e:
        return jsonify({"success": False, "error": "predict_failed", "message": str(e)}), 500
