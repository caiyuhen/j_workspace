import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import {
  ExtractionTemplateFieldsEditor,
  type ExtractionTemplateField,
  type ExtractionTemplateFieldsEditorProps,
} from "../extraction/ExtractionTemplateFieldsEditor";

function emptyField(): ExtractionTemplateField {
  return { key: "", label: "", type: "text", pico_binding: null, required: false, options: [] };
}

function sampleFields(n: number): ExtractionTemplateField[] {
  const arr: ExtractionTemplateField[] = [];
  for (let i = 0; i < n; i++) {
    arr.push({
      key: `f${i}`,
      label: `Field ${i}`,
      type: "text",
      pico_binding: null,
      required: false,
      options: [],
    });
  }
  return arr;
}

function renderEditor(overrides: Partial<ExtractionTemplateFieldsEditorProps> = {}) {
  const onChange = vi.fn();
  const props: ExtractionTemplateFieldsEditorProps = {
    fields: [],
    onChange,
    locked: false,
    ...overrides,
  };
  const r = render(<ExtractionTemplateFieldsEditor {...props} />);
  return { ...r, onChange };
}

describe("Wave83 T8 ExtractionTemplateFieldsEditor (18)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("A01: initial render 0 fields → btn-add-field exists", () => {
    renderEditor({ fields: [] });
    expect(screen.getByTestId("btn-add-field")).toBeTruthy();
  });

  it("A02: click add field → length becomes 1 + onChange called once", () => {
    const { onChange } = renderEditor({ fields: [] });
    fireEvent.click(screen.getByTestId("btn-add-field"));
    expect(onChange).toHaveBeenCalledTimes(1);
    const newFields = onChange.mock.calls[0][0];
    expect(newFields.length).toBe(1);
  });

  it("A03: 5 add field clicks → fields.length=5", () => {
    let currentFields: ExtractionTemplateField[] = [];
    const onChange = vi.fn((f) => { currentFields = f; });
    const { rerender } = render(<ExtractionTemplateFieldsEditor fields={currentFields} onChange={onChange} />);
    for (let i = 0; i < 5; i++) {
      fireEvent.click(screen.getByTestId("btn-add-field"));
      rerender(<ExtractionTemplateFieldsEditor fields={currentFields} onChange={onChange} />);
    }
    expect(currentFields.length).toBe(5);
  });

  it("A04: click btn-remove-field-2 → length=4 剩下 indexes ordered", () => {
    const initial = sampleFields(5);
    let currentFields = [...initial];
    const onChange = vi.fn((f) => { currentFields = f; });
    const { rerender } = render(<ExtractionTemplateFieldsEditor fields={currentFields} onChange={onChange} />);
    fireEvent.click(screen.getByTestId("btn-remove-field-2"));
    rerender(<ExtractionTemplateFieldsEditor fields={currentFields} onChange={onChange} />);
    expect(currentFields.length).toBe(4);
    expect(currentFields[0].key).toBe("f0");
    expect(currentFields[1].key).toBe("f1");
    expect(currentFields[2].key).toBe("f3");
    expect(currentFields[3].key).toBe("f4");
  });

  it("A05: input-field-key-0 type 字母数字 → onChange newFields[0].key === 值", () => {
    const { onChange } = renderEditor({ fields: [{ ...emptyField() }] });
    const input = screen.getByTestId("input-field-key-0") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "myKey123" } });
    expect(onChange).toHaveBeenCalled();
    const newFields = onChange.mock.calls[onChange.mock.calls.length - 1][0];
    expect(newFields[0].key).toBe("myKey123");
  });

  it("A06: input-field-label-0 中文 label OK", () => {
    const { onChange } = renderEditor({ fields: [{ ...emptyField() }] });
    const input = screen.getByTestId("input-field-label-0") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "人群年龄" } });
    expect(onChange).toHaveBeenCalled();
    const newFields = onChange.mock.calls[onChange.mock.calls.length - 1][0];
    expect(newFields[0].label).toBe("人群年龄");
  });

  it("A07: select-field-type-0 change to 'select' → onChange[0].type==='select'", () => {
    const { onChange } = renderEditor({ fields: [{ ...emptyField() }] });
    const sel = screen.getByTestId("select-field-type-0") as HTMLSelectElement;
    fireEvent.change(sel, { target: { value: "select" } });
    const newFields = onChange.mock.calls[onChange.mock.calls.length - 1][0];
    expect(newFields[0].type).toBe("select");
  });

  it("A08: type=select → btn-add-option-0 appears; type=text → not appears", () => {
    const fields: ExtractionTemplateField[] = [
      { ...emptyField(), type: "text", key: "f1" },
      { ...emptyField(), type: "select", key: "f2", options: [] },
    ];
    renderEditor({ fields });
    expect(screen.queryByTestId("btn-add-option-0")).toBeFalsy();
    expect(screen.getByTestId("btn-add-option-1")).toBeTruthy();
  });

  it("A09: btn-add-option-0 click → input-option-0-0 + input-option-0-1 exists", () => {
    const initial: ExtractionTemplateField[] = [{ ...emptyField(), type: "select", key: "f", options: [] }];
    let currentFields = initial.map(f => ({ ...f, options: [...f.options] }));
    const onChange = vi.fn((f) => { currentFields = f.map((x: ExtractionTemplateField) => ({ ...x, options: [...x.options] })); });
    const { rerender } = render(<ExtractionTemplateFieldsEditor fields={currentFields} onChange={onChange} />);
    fireEvent.click(screen.getByTestId("btn-add-option-0"));
    rerender(<ExtractionTemplateFieldsEditor fields={currentFields} onChange={onChange} />);
    expect(screen.getByTestId("input-option-0-0")).toBeTruthy();
    fireEvent.click(screen.getByTestId("btn-add-option-0"));
    rerender(<ExtractionTemplateFieldsEditor fields={currentFields} onChange={onChange} />);
    expect(screen.getByTestId("input-option-0-1")).toBeTruthy();
  });

  it("A10: select-pico-binding-0 8 选项 exists (P/I/C/O/S/StudyType/OutcomeMeasure/Other)", () => {
    renderEditor({ fields: [{ ...emptyField() }] });
    const sel = screen.getByTestId("select-pico-binding-0") as HTMLSelectElement;
    const values = Array.from(sel.options).map(o => o.value);
    expect(values).toContain("");
    expect(values).toContain("P");
    expect(values).toContain("I");
    expect(values).toContain("C");
    expect(values).toContain("O");
    expect(values).toContain("S");
    expect(values).toContain("StudyType");
    expect(values).toContain("OutcomeMeasure");
    expect(values).toContain("Other");
  });

  it("A11: select P → onChange binding === 'P'", () => {
    const { onChange } = renderEditor({ fields: [{ ...emptyField() }] });
    const sel = screen.getByTestId("select-pico-binding-0") as HTMLSelectElement;
    fireEvent.change(sel, { target: { value: "P" } });
    const newFields = onChange.mock.calls[onChange.mock.calls.length - 1][0];
    expect(newFields[0].pico_binding).toBe("P");
  });

  it("A12: select Other → onChange binding === 'Other'", () => {
    const { onChange } = renderEditor({ fields: [{ ...emptyField() }] });
    const sel = screen.getByTestId("select-pico-binding-0") as HTMLSelectElement;
    fireEvent.change(sel, { target: { value: "Other" } });
    const newFields = onChange.mock.calls[onChange.mock.calls.length - 1][0];
    expect(newFields[0].pico_binding).toBe("Other");
  });

  it("A13: required checkbox toggle", () => {
    const initial: ExtractionTemplateField[] = [{ ...emptyField(), required: false, key: "f" }];
    let currentFields = [...initial];
    const onChange = vi.fn((f) => { currentFields = f; });
    const { rerender } = render(<ExtractionTemplateFieldsEditor fields={currentFields} onChange={onChange} />);
    const cb = screen.getByTestId("checkbox-required-0") as HTMLInputElement;
    fireEvent.click(cb);
    rerender(<ExtractionTemplateFieldsEditor fields={currentFields} onChange={onChange} />);
    const called = onChange.mock.calls[onChange.mock.calls.length - 1][0];
    expect(called[0].required).toBe(true);
  });

  it("A14: locked=True → btn-add-field disabled + remove buttons disabled + 所有 inputs disabled", () => {
    const fields = sampleFields(2);
    renderEditor({ fields, locked: true });
    expect((screen.getByTestId("btn-add-field") as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByTestId("btn-remove-field-0") as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByTestId("btn-remove-field-1") as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByTestId("input-field-key-0") as HTMLInputElement).disabled).toBe(true);
    expect((screen.getByTestId("input-field-label-0") as HTMLInputElement).disabled).toBe(true);
    expect((screen.getByTestId("select-field-type-0") as HTMLSelectElement).disabled).toBe(true);
    expect((screen.getByTestId("select-pico-binding-0") as HTMLSelectElement).disabled).toBe(true);
  });

  it("A15: 两个 fields 改 key → onChange 接收完整 [f0,f1]", () => {
    const initial = sampleFields(2);
    let currentFields = initial.map(f => ({ ...f }));
    const onChange = vi.fn((f) => { currentFields = f; });
    const { rerender } = render(<ExtractionTemplateFieldsEditor fields={currentFields} onChange={onChange} />);
    const k0 = screen.getByTestId("input-field-key-0") as HTMLInputElement;
    fireEvent.change(k0, { target: { value: "newKey0" } });
    rerender(<ExtractionTemplateFieldsEditor fields={currentFields} onChange={onChange} />);
    const k1 = screen.getByTestId("input-field-key-1") as HTMLInputElement;
    fireEvent.change(k1, { target: { value: "newKey1" } });
    rerender(<ExtractionTemplateFieldsEditor fields={currentFields} onChange={onChange} />);
    const last = onChange.mock.calls[onChange.mock.calls.length - 1][0];
    expect(last.length).toBe(2);
    expect(last[0].key).toBe("newKey0");
    expect(last[1].key).toBe("newKey1");
  });

  it("A16: duplicate key (两个字段同 key) → 组件显示 warning testid duplicate-key-warning", () => {
    const f1: ExtractionTemplateField = { ...emptyField(), key: "same" };
    const f2: ExtractionTemplateField = { ...emptyField(), key: "same" };
    renderEditor({ fields: [f1, f2] });
    expect(screen.getByTestId("duplicate-key-warning")).toBeTruthy();
  });

  it("A17: empty key (key == '') → 组件显示 empty-key-warning for that index", () => {
    const f1: ExtractionTemplateField = { ...emptyField(), key: "ok" };
    const f2: ExtractionTemplateField = { ...emptyField(), key: "" };
    renderEditor({ fields: [f1, f2] });
    expect(screen.getByTestId("empty-key-warning-1")).toBeTruthy();
    expect(screen.queryByTestId("empty-key-warning-0")).toBeFalsy();
  });

  it("A18: 保存按钮 (btn-save-fields) → disabled when any field has empty key", () => {
    const fields: ExtractionTemplateField[] = [
      { ...emptyField(), key: "" },
      { ...emptyField(), key: "ok" },
    ];
    const onChange = vi.fn();
    render(<ExtractionTemplateFieldsEditor fields={fields} onChange={onChange} />);
    expect((screen.getByTestId("btn-save-fields") as HTMLButtonElement).disabled).toBe(true);
  });
});
