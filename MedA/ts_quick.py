import pathlib, re, sys
p = pathlib.Path(r'd:\workspace\MedA\T11_TS_FULL.txt')
if not p.exists():
    print('TS FULL FILE NOT FOUND', flush=True)
    sys.exit(1)
txt = p.read_text(encoding='utf-8', errors='ignore')
print('TS FILE SIZE:', len(txt), flush=True)
print('LAST 500 CHARS:', repr(txt[-500:]), flush=True)
m_passed = re.search(r'Tests\s+(\d+)\s+passed', txt)
m_failed = re.search(r'Tests\s+(?:\d+\s+passed,\s+)?(\d+)\s+failed', txt)
m_tf_passed = re.search(r'Test Files\s+(\d+)\s+passed', txt)
m_tf_failed = re.search(r'Test Files\s+(?:\d+\s+passed,\s+)?(\d+)\s+failed', txt)
passed = int(m_passed.group(1)) if m_passed else None
failed = int(m_failed.group(1)) if m_failed else None
tf_p = int(m_tf_passed.group(1)) if m_tf_passed else None
tf_f = int(m_tf_failed.group(1)) if m_tf_failed else None
print(f'TS Tests passed: {passed}')
print(f'TS Tests failed: {failed}')
print(f'TS Test Files passed: {tf_p}')
print(f'TS Test Files failed: {tf_f}')
with open(r'd:\workspace\MedA\TS_QUICK.txt', 'w') as f:
    f.write(f'TS Tests passed: {passed}\n')
    f.write(f'TS Tests failed: {failed}\n')
    f.write(f'TS Test Files passed: {tf_p}\n')
    f.write(f'TS Test Files failed: {tf_f}\n')
