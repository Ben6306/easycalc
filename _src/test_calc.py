#!/usr/bin/env python3
"""EasyCalc 계산 공식 자동 검산 / formula tests.

사용법: python3 _src/test_calc.py   (build.py가 빌드 전에 자동 실행)
- calc.html 안의 실제 계산 함수(JS)를 node로 실행하고,
  파이썬(Decimal)으로 따로 만든 공식 결과와 원 단위까지 비교합니다.
- 요율·간이세액표를 바꾸면 아래 '고정 검산값'도 공식 자료로 다시 확인해서 고치세요.
종료 코드: 0 통과 / 1 실패 / 2 node 없음(건너뜀)
"""
import json, os, re, shutil, subprocess, sys
from datetime import date, timedelta
from decimal import Decimal as Dc, ROUND_FLOOR, ROUND_HALF_UP

SRC = os.path.dirname(os.path.abspath(__file__))
calc = open(os.path.join(SRC, 'calc.html'), encoding='utf-8').read()

# ---------- 고정 검산값 (공식 자료로 직접 확인한 값) ----------
# 연봉 5,000만, 본인 1명, 자녀 0, 식대 20만, 퇴직금 별도, 원천징수 100% (간이세액표 2026.3.1 시행판)
GOLDEN_SALARY = [((50_000_000, 200_000, 1, 0, 0, 100), {'itax': 190_620, 'ltax': 19_060, 'net': 3_571_587})]
# 4대보험 근로자 요율 (2026.7~): 국민연금 4.75%(기준소득월액 41만~659만), 건강 3.595%, 장기요양 13.14%, 고용 0.9%
PENSION, P_LO, P_HI, HEALTH, CARE, EMP = Dc('0.0475'), 410_000, 6_590_000, Dc('0.03595'), Dc('0.1314'), Dc('0.009')


# ---------- calc.html에서 함수 꺼내기 ----------
def js_function(name):
    i = calc.index(f'function {name}(')
    j = calc.index('{', i)
    depth = 0
    for k in range(j, len(calc)):
        depth += {'{': 1, '}': -1}.get(calc[k], 0)
        if depth == 0:
            return calc[i:k + 1]
    raise ValueError(name)


def js_const(name):
    m = re.search(rf'^const {name}=.*$', calc, re.M)
    if not m:
        raise ValueError(name)
    return m.group(0)


wh = re.search(r'^window\.WH_TABLE=.*$', calc, re.M).group(0)
JS = 'const window={};' + wh + '\n' + '\n'.join(
    [js_const(n) for n in ['fl10', 'pad', 'D', 'addM', 'fullMonths', 'leaveDays']] +
    [js_function(n) for n in ['whBase', 'withholding', 'netPay', 'schedule', 'savCalc', 'severance']]) + r'''
const C=JSON.parse(require('fs').readFileSync(0,'utf8')),R={};
R.salary=C.salary.map(a=>netPay(...a));
R.loan=C.loan.map(a=>{const s=schedule(...a);return{ti:s.ti,total:s.total,first:s.rows[0][1],last:s.rows[s.rows.length-1][1],bal:s.rows[s.rows.length-1][4]}});
R.saving=C.saving.map(a=>savCalc(...a));
R.sev=C.sev.map(([s,e,p,b,l])=>severance(D(s),D(e),p,b,l));
R.leave=C.leave.map(([s,b])=>{const m=fullMonths(D(s),D(b)),y=Math.floor(m/12);return y<1?Math.min(11,m):leaveDays(y)});
process.stdout.write(JSON.stringify(R));'''


# ---------- 파이썬으로 따로 만든 공식 ----------
def fl10(x):
    return int((Dc(x) / 10).to_integral_value(ROUND_FLOOR)) * 10


def py_insurance(annual, free, sev):
    # 보험료는 원 단위 과세 급여(원 미만 버림)에 요율을 곱함 (실제 급여 계산과 같게)
    monthly = Dc(annual) / (13 if sev else 12)
    taxable = Dc(int(max(Dc(0), monthly - free)))
    base = min(P_HI, max(P_LO, int(taxable // 1000) * 1000))
    pension = fl10(base * PENSION) if taxable else 0
    health = fl10(taxable * HEALTH)
    care = fl10(health * CARE)
    emp = fl10(taxable * EMP)
    return monthly, pension, health, care, emp


def py_loan(P, rate, n, m):
    r = Dc(str(rate)) / 100 / 12
    half = lambda x: int(Dc(x).quantize(Dc(1), ROUND_HALF_UP))
    pmt = Dc(P) / n if r == 0 else Dc(P) * r * (1 + r) ** n / ((1 + r) ** n - 1)
    bal, ti, rows = P, 0, []
    for i in range(1, n + 1):
        it = half(bal * r)
        if i == n:
            pr = bal
        elif m == 'annuity':
            pr = min(bal, half(pmt) - it)
        elif m == 'principal':
            pr = half(Dc(P) / n)
        else:
            pr = 0
        bal -= pr; ti += it; rows.append((pr + it, max(0, bal)))
    return {'ti': ti, 'total': P + ti, 'first': rows[0][0], 'last': rows[-1][0], 'bal': rows[-1][1]}


def py_saving(kind, amt, rate, n, comp, tax):
    i = Dc(str(rate)) / 1200
    principal = amt * n if kind == 'saving' else amt
    if kind == 'deposit':
        g = amt * ((1 + i) ** n - 1) if comp == 'compound' else amt * i * n
    else:
        g = (amt * ((1 + i) ** n - 1) / i * (1 + i) - principal if i else 0) if comp == 'compound' else amt * i * n * (n + 1) / 2
    g = int(Dc(g).to_integral_value(ROUND_FLOOR))
    t = int((Dc(g) * Dc(str(tax)) / 100).to_integral_value(ROUND_FLOOR))
    return {'principal': principal, 'gross': g, 'tax': t, 'net': g - t, 'maturity': principal + g - t}


def add_months(d, n):
    y, m = divmod(d.month - 1 + n, 12)
    y += d.year; m += 1
    last = (date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)).day
    return date(y, m, min(d.day, last))


def py_sev(s, e, pay, bonus, lpay):
    S, E = date.fromisoformat(s), date.fromisoformat(e)
    R = E + timedelta(days=1)
    days = (R - S).days
    pdays = (R - add_months(R, -3)).days
    wages = Dc(pay) * 3 + Dc(bonus) * 3 / 12 + Dc(lpay) * 3 / 12
    avg = wages / pdays
    return {'days': days, 'pDays': pdays, 'avg': avg, 'eligible': add_months(S, 12) <= R, 'amount': avg * 30 * days / 365}


def py_leave(s, b):
    S, B = date.fromisoformat(s), date.fromisoformat(b)
    m = 0
    while add_months(S, m + 1) <= B:
        m += 1
    y = m // 12
    return min(11, m) if y < 1 else min(25, 15 + (y - 1) // 2)  # 근로기준법 제60조


# ---------- 검산 조합 ----------
CASES = {
    'salary': [list(a) for a, _ in GOLDEN_SALARY] + [[a, f, fam, k, sv, w] for a in (24_000_000, 36_000_000, 50_000_000, 72_000_000, 100_000_000, 150_000_000, 300_000_000)
                                                     for f, fam, k, sv, w in ((200_000, 1, 0, 0, 100), (0, 3, 1, 1, 80), (200_000, 4, 2, 0, 120))],
    'loan': [[P, r, n, m] for P, r, n in ((300_000_000, 4.2, 360), (10_000_000, 5.5, 12), (50_000_000, 0, 60), (123_456_789, 3.85, 240))
             for m in ('annuity', 'principal', 'bullet')],
    'saving': [[k, a, r, n, c, t] for k, a in (('deposit', 10_000_000), ('saving', 500_000)) for r, n in ((3.5, 12), (4.1, 36), (0, 12))
               for c in ('simple', 'compound') for t in (15.4, 0)],
    'sev': [['2021-03-02', '2026-10-18', 3_500_000, 3_000_000, 0], ['2025-11-01', '2026-10-31', 2_500_000, 0, 0],
            ['2025-11-01', '2026-10-30', 2_500_000, 0, 0], ['2016-01-01', '2026-02-28', 5_000_000, 6_000_000, 400_000]],
    'leave': [['2023-03-02', '2026-10-18'], ['2026-01-15', '2026-10-18'], ['2025-10-18', '2026-10-18'], ['2025-10-19', '2026-10-18'],
              ['2024-10-18', '2026-10-18'], ['2003-05-01', '2026-10-18'], ['2024-01-31', '2024-02-29']],
}


def main():
    if not shutil.which('node'):
        print('test_calc: node 없음 → 건너뜀')
        return 2
    # 임시 파일 없이 표준입력으로 node에 전달
    p = subprocess.run(['node', '-'], input=JS.replace('JSON.parse(require(\'fs\').readFileSync(0,\'utf8\'))', json.dumps(CASES)), capture_output=True, text=True)
    if p.returncode:
        print(p.stderr); return 1
    R = json.loads(p.stdout)
    fails, n = [], 0

    def check(label, got, want, tol=0):
        nonlocal n
        n += 1
        if (abs(float(got) - float(want)) > tol) if tol else (got != want):
            fails.append(f'{label}: JS={got} / 기대값={want}')

    for (a, want) in GOLDEN_SALARY:
        r = R['salary'][0]
        for k, v in want.items():
            check(f'연봉 고정값 {a} {k}', round(r[k]), v)
    for a, r in zip(CASES['salary'], R['salary']):
        monthly, pension, health, care, emp = py_insurance(a[0], a[1], a[4])
        check(f'연봉 {a} 국민연금', r['pension'], pension); check(f'연봉 {a} 건강', r['health'], health)
        check(f'연봉 {a} 장기요양', r['care'], care); check(f'연봉 {a} 고용', r['emp'], emp)
        check(f'연봉 {a} 지방소득세', r['ltax'], fl10(r['itax'] * Dc('0.1')))
        check(f'연봉 {a} 실수령 합계', r['net'], float(monthly) - (pension + health + care + emp + r['itax'] + r['ltax']), 1e-6)
        check(f'연봉 {a} 소득세 10원 단위', r['itax'] % 10, 0)
    # 소득세는 월급이 오르면 줄지 않고, 가족이 늘면 늘지 않아야 함
    it = [r['itax'] for a, r in list(zip(CASES['salary'], R['salary']))[len(GOLDEN_SALARY):] if a[1:] == [200_000, 1, 0, 0, 100]]
    check('소득세 단조 증가(연봉↑)', it == sorted(it), True)
    for a, r in zip(CASES['loan'], R['loan']):
        w = py_loan(*a)
        for k in w:
            check(f'대출 {a} {k}', r[k], w[k])
    for a, r in zip(CASES['saving'], R['saving']):
        w = py_saving(*a)
        for k in w:
            check(f'예적금 {a} {k}', r[k], w[k])
    for a, r in zip(CASES['sev'], R['sev']):
        w = py_sev(*a)
        check(f'퇴직금 {a} 재직일수', r['days'], w['days']); check(f'퇴직금 {a} 3개월 일수', r['pDays'], w['pDays'])
        check(f'퇴직금 {a} 지급 대상', r['eligible'], w['eligible'])
        check(f'퇴직금 {a} 금액', r['amount'], w['amount'], 1e-4)
    for a, r in zip(CASES['leave'], R['leave']):
        check(f'연차 {a}', r, py_leave(*a))

    if fails:
        print(f'test_calc: {len(fails)}건 실패 / 전체 {n}건'); print('\n'.join('  ✗ ' + f for f in fails[:40]))
        return 1
    print(f'test_calc: {n}건 모두 통과 ✓')
    return 0


if __name__ == '__main__':
    sys.exit(main())
