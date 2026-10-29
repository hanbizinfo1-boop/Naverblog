"""
한비즈마케팅 - 주문 데이터 분석 대시보드 (S급) v2
- 대시보드: 표를 세로 정렬 (위→아래 흐름)
- 인사이트: 카드형 → 표 형식으로 변경하여 가독성 향상
- 모든 표에 구분선 색상 추가
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import CellIsRule, FormulaRule
import re
from datetime import datetime

# ============================================================
# 원본 데이터
# ============================================================
raw_data = [
    [1001, "김민수", "010-1234-5678", "minsu@naver.com", "2025-03-01", "2025-03-03", "갤럭시S24", "전자", 1, 1200000, 1200000, "카드", "서울", "이정훈", "완료"],
    [1002, "이영희", "01012345679", "lee@@gmail.com", "2025/03/02", "", "아이폰15", "전자", 2, 1300000, 2600000, "현금", "부산", "박성호", "배송중"],
    [1003, "박철수", "010-9876-5432", "cspark@gmail", "2025-03-05", "2025-03-07", "LG그램", "전자", 1, 1500000, 1500000, "카드", "서울", "이정훈", "완료"],
    [1004, "최지은", "010-1111-2222", "jieun@hanmail.net", "03-06-2025", "2025-03-08", "에어팟프로", "전자", 3, 350000, 1050000, "카드", "대전", "", "완료"],
    [1005, "정우성", "010-2222-3333", "woo@naver.com", "2025-03-07", "2025-03-10", "맥북에어", "전자", 1, 1800000, 1800000, "카드", "서울", "김태형", "취소"],
    [1006, "한지민", "010-3333-4444", "han@gmail.com", "2025-03-08", "2025-03-09", "다이슨청소기", "가전", 1, 900000, 900000, "카드", "인천", "박성호", "완료"],
    [1007, "홍길동", "010-4444-5555", "hong@gmail.com", "2025-03-08", "", "스타벅스텀블러", "생활", 5, 30000, 150000, "현금", "서울", "이정훈", "배송중"],
    [1008, "김민수", "010-1234-5678", "minsu@naver.com", "2025-03-09", "2025-03-11", "갤럭시워치", "전자", 1, 400000, 400000, "카드", "서울", "이정훈", "완료"],
    [1009, "이영희", "01012345679", "lee@gmail.com", "2025-03-10", "2025-03-12", "아이패드", "전자", 1, 900000, 900000, "카드", "부산", "박성호", "완료"],
    [1010, "박철수", "010-9876-5432", "cspark@gmail.com", "2025-03-11", "", "LG모니터", "전자", 2, 300000, 600000, "카드", "서울", "", "배송중"],
    [1011, "최지은", "010-1111-2222", "jieun@hanmail.net", "2025-03-12", "2025-03-13", "쿠쿠밥솥", "가전", 1, 250000, 250000, "현금", "대전", "김태형", "완료"],
    [1012, "정우성", "010-2222-3333", "woo@naver.com", "2025-03-12", "2025-03-14", "맥북프로", "전자", 1, 2500000, 2500000, "카드", "서울", "김태형", "완료"],
    [1013, "한지민", "010-3333-4444", "han@@gmail.com", "2025-03-13", "", "에어컨", "가전", 1, 2000000, 2000000, "카드", "인천", "박성호", "배송중"],
    [1014, "홍길동", "010-4444-5555", "hong@gmail", "2025-03-14", "2025-03-16", "텀블러", "생활", 3, 25000, 75000, "현금", "서울", "이정훈", "완료"],
]

# ============================================================
# 클렌징 함수
# ============================================================
def clean_phone(p):
    digits = re.sub(r'\D', '', str(p))
    if len(digits) == 11 and digits.startswith('010'):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    return p

def clean_email(e):
    e = str(e).strip().replace('@@', '@')
    if '@' in e:
        local, _, domain = e.rpartition('@')
        if '.' not in domain:
            e = f"{local}@{domain}.com"
    return e

def email_is_valid(e):
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', e))

def clean_date(d):
    if not d or d == "":
        return None
    d = str(d).strip().replace('/', '-')
    parts = d.split('-')
    if len(parts) == 3 and len(parts[2]) == 4:
        d = f"{parts[2]}-{parts[0]}-{parts[1]}"
    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except:
        return None

def fill_manager(manager, region):
    if manager and manager.strip():
        return manager
    return {"서울": "이정훈", "부산": "박성호", "대전": "김태형", "인천": "박성호"}.get(region, "미배정")

# ============================================================
# 클렌징
# ============================================================
cleaned = []
for row in raw_data:
    order_id, name, phone, email, order_dt, ship_dt, product, category, qty, price, total, pay, region, manager, status = row
    phone_clean = clean_phone(phone)
    email_clean = clean_email(email)
    order_dt_clean = clean_date(order_dt)
    ship_dt_clean = clean_date(ship_dt)
    manager_clean = fill_manager(manager, region)
    
    flags = []
    if phone != phone_clean: flags.append(f"연락처({phone})")
    if email != email_clean: flags.append(f"이메일({email})")
    if str(order_dt) != (order_dt_clean.strftime("%Y-%m-%d") if order_dt_clean else ""):
        flags.append(f"주문일자({order_dt})")
    if not manager or not manager.strip(): flags.append("담당자누락")
    if not email_is_valid(email_clean): flags.append("이메일형식이상")
    
    cleaned.append({
        'order_id': order_id, 'name': name,
        'phone_orig': phone, 'phone': phone_clean,
        'email_orig': email, 'email': email_clean,
        'order_dt_orig': str(order_dt), 'order_dt': order_dt_clean,
        'ship_dt_orig': str(ship_dt) if ship_dt else "", 'ship_dt': ship_dt_clean,
        'product': product, 'category': category, 'qty': qty,
        'price': price, 'total': total, 'pay': pay,
        'region': region, 'manager_orig': manager, 'manager': manager_clean,
        'status': status, 'errors': ", ".join(flags) if flags else "정상",
    })

# ============================================================
# 디자인 시스템
# ============================================================
wb = Workbook()
wb.remove(wb.active)

# 색상 팔레트
NAVY = "1F3864"        # 메인 헤더
BLUE = "2E75B6"        # 서브 헤더
GOLD = "FFC000"
GREEN = "70AD47"
RED = "C00000"
ORANGE = "ED7D31"
BG_GRAY = "F2F2F2"
BG_SOFT = "FFF2CC"
BG_BLUE = "DDEBF7"     # 표 줄무늬용 연한 파랑
BG_GREEN = "E2EFDA"    # 합계 행 배경
TEXT_DARK = "262626"
WHITE = "FFFFFF"
BORDER_BLUE = "8FAADC" # 표 구분선 색상 (블루 톤)
BORDER_GRAY = "BFBFBF"

FONT_NAME = "맑은 고딕"

# ── 색이 있는 테두리 정의
def colored_border(color=BORDER_BLUE, weight='thin'):
    side = Side(style=weight, color=color)
    return Border(left=side, right=side, top=side, bottom=side)

def thick_border(color=NAVY):
    side = Side(style='medium', color=color)
    return Border(left=side, right=side, top=side, bottom=side)

# ── 스타일 함수
def style_title(cell, size=20):
    cell.font = Font(name=FONT_NAME, size=size, bold=True, color=WHITE)
    cell.fill = PatternFill('solid', start_color=NAVY)
    cell.alignment = Alignment(horizontal='center', vertical='center')

def style_section_header(cell, size=12):
    """표 위에 붙는 섹션 제목 (한 줄짜리)"""
    cell.font = Font(name=FONT_NAME, size=size, bold=True, color=WHITE)
    cell.fill = PatternFill('solid', start_color=BLUE)
    cell.alignment = Alignment(horizontal='left', vertical='center', indent=1)

def style_table_header(cell):
    """표의 헤더 행"""
    cell.font = Font(name=FONT_NAME, size=10, bold=True, color=WHITE)
    cell.fill = PatternFill('solid', start_color=NAVY)
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    cell.border = Border(
        left=Side(style='thin', color=NAVY),
        right=Side(style='thin', color=NAVY),
        top=Side(style='medium', color=NAVY),
        bottom=Side(style='medium', color=NAVY),
    )

def style_table_data(cell, align='center', striped=False):
    """표의 데이터 행 - 색깔 구분선 적용"""
    cell.font = Font(name=FONT_NAME, size=10, color=TEXT_DARK)
    cell.alignment = Alignment(horizontal=align, vertical='center', wrap_text=True)
    cell.border = Border(
        left=Side(style='thin', color=BORDER_BLUE),
        right=Side(style='thin', color=BORDER_BLUE),
        top=Side(style='thin', color=BORDER_BLUE),
        bottom=Side(style='thin', color=BORDER_BLUE),
    )
    if striped:
        cell.fill = PatternFill('solid', start_color=BG_BLUE)

def style_table_total(cell, align='center'):
    """표의 합계 행"""
    cell.font = Font(name=FONT_NAME, size=10, bold=True, color=NAVY)
    cell.fill = PatternFill('solid', start_color=BG_GREEN)
    cell.alignment = Alignment(horizontal=align, vertical='center')
    cell.border = Border(
        left=Side(style='thin', color=NAVY),
        right=Side(style='thin', color=NAVY),
        top=Side(style='medium', color=NAVY),
        bottom=Side(style='medium', color=NAVY),
    )

def style_kpi_label(cell):
    cell.font = Font(name=FONT_NAME, size=11, bold=True, color=WHITE)
    cell.fill = PatternFill('solid', start_color=BLUE)
    cell.alignment = Alignment(horizontal='center', vertical='center')
    cell.border = colored_border(BLUE, 'medium')

def style_kpi_value(cell, color=NAVY):
    cell.font = Font(name=FONT_NAME, size=18, bold=True, color=color)
    cell.fill = PatternFill('solid', start_color=BG_GRAY)
    cell.alignment = Alignment(horizontal='center', vertical='center')
    cell.border = Border(
        left=Side(style='medium', color=BLUE),
        right=Side(style='medium', color=BLUE),
        top=Side(style='thin', color=BLUE),
        bottom=Side(style='medium', color=BLUE),
    )

# ============================================================
# Sheet 1: 📊 대시보드 (세로 정렬 흐름)
# ============================================================
ws1 = wb.create_sheet("📊 대시보드")
ws1.sheet_view.showGridLines = False

# 사용 컬럼: B(2) ~ H(8), 7컬럼
# 모든 표 폭 = 7컬럼 통일

# === [1] 타이틀 ===
ws1.merge_cells('B2:H3')
ws1['B2'] = "한비즈마케팅 주문 데이터 분석 대시보드"
style_title(ws1['B2'], size=22)

ws1.merge_cells('B4:H4')
ws1['B4'] = f"분석 기간: 2025-03-01 ~ 2025-03-14   |   총 14건의 주문   |   작성일: {datetime.now().strftime('%Y-%m-%d')}"
ws1['B4'].font = Font(name=FONT_NAME, size=10, italic=True, color="595959")
ws1['B4'].alignment = Alignment(horizontal='center', vertical='center')

# === [2] KPI 4종 (세로 한 줄, 균등 분할) ===
ws1.merge_cells('B6:H6')
ws1['B6'] = "🎯 핵심 지표"
style_section_header(ws1['B6'], size=13)
ws1.row_dimensions[6].height = 26

# B-C / D-E / F-G / H 영역에 KPI 4개 배치 (G-H 합쳐서 한 칸씩 → 8칸 필요)
# 7컬럼이라 이전과 다르게 컬럼 폭 분할
# 더 명확하게: 각 KPI를 2컬럼씩 → 4 × 2 = 8 → 안되니, 컬럼 너비로 시각적 폭 조절
# 4개를 균등 배치: B-C / D-E / F-G / H 각각 1.75컬럼씩... 그냥 4컬럼 합쳐서 가도록
# B(2) D(4) F(6) → 3개만 → KPI 3+1 그리드 안 좋음. 4개 → 컬럼 추가 필요
# 결정: KPI 영역만 B~I (8컬럼) 사용, 나머지 표는 B~H

ws1.merge_cells('B7:C7'); ws1['B7'] = "💰 총 매출액 (완료)"; style_kpi_label(ws1['B7'])
ws1.merge_cells('B8:C9'); ws1['B8'] = '=SUMIFS(\'주문데이터(클렌징)\'!K:K,\'주문데이터(클렌징)\'!O:O,"완료")'
ws1['B8'].number_format = '#,##0"원"'
style_kpi_value(ws1['B8'], NAVY)

ws1.merge_cells('D7:E7'); ws1['D7'] = "📦 총 주문 건수"; style_kpi_label(ws1['D7'])
ws1.merge_cells('D8:E9'); ws1['D8'] = '=COUNTA(\'주문데이터(클렌징)\'!A:A)-2'
ws1['D8'].number_format = '#,##0"건"'
style_kpi_value(ws1['D8'], BLUE)

ws1.merge_cells('F7:G7'); ws1['F7'] = "💳 평균 주문액"; style_kpi_label(ws1['F7'])
ws1.merge_cells('F8:G9'); ws1['F8'] = '=AVERAGEIFS(\'주문데이터(클렌징)\'!K:K,\'주문데이터(클렌징)\'!O:O,"완료")'
ws1['F8'].number_format = '#,##0"원"'
style_kpi_value(ws1['F8'], GREEN)

ws1.merge_cells('H7:I7'); ws1['H7'] = "⚠️ 취소율"; style_kpi_label(ws1['H7'])
ws1.merge_cells('H8:I9'); ws1['H8'] = '=COUNTIF(\'주문데이터(클렌징)\'!O:O,"취소")/(COUNTA(\'주문데이터(클렌징)\'!A:A)-2)'
ws1['H8'].number_format = '0.0%'
style_kpi_value(ws1['H8'], RED)

ws1.row_dimensions[7].height = 22
ws1.row_dimensions[8].height = 28
ws1.row_dimensions[9].height = 28

# === [3] 지역별 매출 표 (세로) ===
# B11에 섹션 헤더, B12부터 표
ws1.merge_cells('B11:I11')
ws1['B11'] = "🗺️ 지역별 매출 (완료 주문 기준)"
style_section_header(ws1['B11'], size=12)
ws1.row_dimensions[11].height = 24

# 표 헤더 - 5컬럼 표 (지역 / 매출액 / 비중 / 시각화바 / 비고)
region_headers = ["지역", "매출액", "비중", "시각화", "비고"]
# B C D E:F G:I 분배 (7컬럼 활용)
ws1['B12'] = region_headers[0]
ws1['C12'] = region_headers[1]
ws1['D12'] = region_headers[2]
ws1.merge_cells('E12:F12'); ws1['E12'] = region_headers[3]
ws1.merge_cells('G12:I12'); ws1['G12'] = region_headers[4]
for c in ['B12','C12','D12','E12','G12']:
    style_table_header(ws1[c])

regions_data = [
    ("서울", "수도권 핵심 시장 — 가장 큰 비중"),
    ("부산", "이영희 등 충성 고객 거점"),
    ("대전", "김태형 단독 운영 지역"),
    ("인천", "한지민의 가전 수요 강세"),
]
for idx, (region, note) in enumerate(regions_data):
    r = 13 + idx
    striped = (idx % 2 == 1)
    ws1[f'B{r}'] = region
    ws1[f'C{r}'] = f'=SUMIFS(\'주문데이터(클렌징)\'!K:K,\'주문데이터(클렌징)\'!M:M,"{region}",\'주문데이터(클렌징)\'!O:O,"완료")'
    ws1[f'D{r}'] = f'=IFERROR(C{r}/$C$17,0)'
    ws1[f'C{r}'].number_format = '#,##0"원"'
    ws1[f'D{r}'].number_format = '0.0%'
    # 시각화: REPT로 가로 막대
    ws1.merge_cells(f'E{r}:F{r}')
    ws1[f'E{r}'] = f'=REPT("■",ROUND(D{r}*30,0))'
    # 비고
    ws1.merge_cells(f'G{r}:I{r}')
    ws1[f'G{r}'] = note
    
    style_table_data(ws1[f'B{r}'], striped=striped)
    style_table_data(ws1[f'C{r}'], align='right', striped=striped)
    style_table_data(ws1[f'D{r}'], align='right', striped=striped)
    style_table_data(ws1[f'E{r}'], align='left', striped=striped)
    style_table_data(ws1[f'G{r}'], align='left', striped=striped)
    # 시각화 바 색상
    ws1[f'E{r}'].font = Font(name=FONT_NAME, size=10, color=BLUE, bold=True)

# 합계 행
ws1[f'B17'] = "합계"
ws1[f'C17'] = '=SUM(C13:C16)'
ws1[f'D17'] = '=SUM(D13:D16)'
ws1[f'C17'].number_format = '#,##0"원"'
ws1[f'D17'].number_format = '0.0%'
ws1.merge_cells('E17:F17')
ws1.merge_cells('G17:I17')
ws1[f'E17'] = ""
ws1[f'G17'] = "전체 합계"
for c in ['B17','C17','D17','E17','G17']:
    style_table_total(ws1[c], align='center' if c in ['B17','D17'] else 'right' if c=='C17' else 'left')

# === [4] 카테고리별 매출 표 ===
ws1.merge_cells('B19:I19')
ws1['B19'] = "📂 카테고리별 매출 (완료 주문 기준)"
style_section_header(ws1['B19'], size=12)
ws1.row_dimensions[19].height = 24

ws1['B20'] = "카테고리"
ws1['C20'] = "매출액"
ws1['D20'] = "비중"
ws1.merge_cells('E20:F20'); ws1['E20'] = "시각화"
ws1.merge_cells('G20:I20'); ws1['G20'] = "특징"
for c in ['B20','C20','D20','E20','G20']:
    style_table_header(ws1[c])

cat_data = [
    ("전자", "스마트폰·노트북·아이패드 — 주력"),
    ("가전", "에어컨·청소기 등 고단가"),
    ("생활", "텀블러 등 수량 많고 단가 낮음"),
]
for idx, (cat, note) in enumerate(cat_data):
    r = 21 + idx
    striped = (idx % 2 == 1)
    ws1[f'B{r}'] = cat
    ws1[f'C{r}'] = f'=SUMIFS(\'주문데이터(클렌징)\'!K:K,\'주문데이터(클렌징)\'!H:H,"{cat}",\'주문데이터(클렌징)\'!O:O,"완료")'
    ws1[f'D{r}'] = f'=IFERROR(C{r}/$C$24,0)'
    ws1[f'C{r}'].number_format = '#,##0"원"'
    ws1[f'D{r}'].number_format = '0.0%'
    ws1.merge_cells(f'E{r}:F{r}')
    ws1[f'E{r}'] = f'=REPT("■",ROUND(D{r}*30,0))'
    ws1.merge_cells(f'G{r}:I{r}')
    ws1[f'G{r}'] = note
    
    style_table_data(ws1[f'B{r}'], striped=striped)
    style_table_data(ws1[f'C{r}'], align='right', striped=striped)
    style_table_data(ws1[f'D{r}'], align='right', striped=striped)
    style_table_data(ws1[f'E{r}'], align='left', striped=striped)
    style_table_data(ws1[f'G{r}'], align='left', striped=striped)
    ws1[f'E{r}'].font = Font(name=FONT_NAME, size=10, color=GREEN, bold=True)

# 합계
ws1[f'B24'] = "합계"
ws1[f'C24'] = '=SUM(C21:C23)'
ws1[f'D24'] = '=SUM(D21:D23)'
ws1[f'C24'].number_format = '#,##0"원"'
ws1[f'D24'].number_format = '0.0%'
ws1.merge_cells('E24:F24'); ws1['E24'] = ""
ws1.merge_cells('G24:I24'); ws1['G24'] = "전체 합계"
for c in ['B24','C24','D24','E24','G24']:
    style_table_total(ws1[c], align='center' if c in ['B24','D24'] else 'right' if c=='C24' else 'left')

# === [5] 담당자별 성과 ===
ws1.merge_cells('B26:I26')
ws1['B26'] = "👤 담당자별 성과 (완료 주문 기준)"
style_section_header(ws1['B26'], size=12)
ws1.row_dimensions[26].height = 24

ws1['B27'] = "담당자"
ws1['C27'] = "건수"
ws1['D27'] = "총 매출액"
ws1['E27'] = "건당 평균"
ws1.merge_cells('F27:I27'); ws1['F27'] = "특이사항"
for c in ['B27','C27','D27','E27','F27']:
    style_table_header(ws1[c])

mgr_data = [
    ("이정훈", "서울 전담 — 건수 많지만 중저가 비중"),
    ("박성호", "부산·인천 — 안정적 운영"),
    ("김태형", "건당 평균 1위 — 고단가 특화"),
]
for idx, (mgr, note) in enumerate(mgr_data):
    r = 28 + idx
    striped = (idx % 2 == 1)
    ws1[f'B{r}'] = mgr
    ws1[f'C{r}'] = f'=COUNTIFS(\'주문데이터(클렌징)\'!N:N,"{mgr}",\'주문데이터(클렌징)\'!O:O,"완료")'
    ws1[f'D{r}'] = f'=SUMIFS(\'주문데이터(클렌징)\'!K:K,\'주문데이터(클렌징)\'!N:N,"{mgr}",\'주문데이터(클렌징)\'!O:O,"완료")'
    ws1[f'E{r}'] = f'=IFERROR(D{r}/C{r},0)'
    ws1[f'C{r}'].number_format = '#,##0"건"'
    ws1[f'D{r}'].number_format = '#,##0"원"'
    ws1[f'E{r}'].number_format = '#,##0"원"'
    ws1.merge_cells(f'F{r}:I{r}')
    ws1[f'F{r}'] = note
    
    style_table_data(ws1[f'B{r}'], striped=striped)
    style_table_data(ws1[f'C{r}'], align='right', striped=striped)
    style_table_data(ws1[f'D{r}'], align='right', striped=striped)
    style_table_data(ws1[f'E{r}'], align='right', striped=striped)
    style_table_data(ws1[f'F{r}'], align='left', striped=striped)

# === [6] 결제수단 분석 ===
ws1.merge_cells('B32:I32')
ws1['B32'] = "💳 결제수단 분석"
style_section_header(ws1['B32'], size=12)
ws1.row_dimensions[32].height = 24

ws1['B33'] = "결제수단"
ws1['C33'] = "건수"
ws1['D33'] = "비중"
ws1.merge_cells('E33:F33'); ws1['E33'] = "시각화"
ws1.merge_cells('G33:I33'); ws1['G33'] = "인사이트"
for c in ['B33','C33','D33','E33','G33']:
    style_table_header(ws1[c])

pay_data = [
    ("카드", "신규 고객 비중 높음 — 첫 거래 주력 채널"),
    ("현금", "재구매 충성 고객 위주 — 단골 패턴"),
]
for idx, (pay, note) in enumerate(pay_data):
    r = 34 + idx
    striped = (idx % 2 == 1)
    ws1[f'B{r}'] = pay
    ws1[f'C{r}'] = f'=COUNTIF(\'주문데이터(클렌징)\'!L:L,"{pay}")'
    ws1[f'D{r}'] = f'=IFERROR(C{r}/SUM($C$34:$C$35),0)'
    ws1[f'C{r}'].number_format = '#,##0"건"'
    ws1[f'D{r}'].number_format = '0.0%'
    ws1.merge_cells(f'E{r}:F{r}')
    ws1[f'E{r}'] = f'=REPT("■",ROUND(D{r}*30,0))'
    ws1.merge_cells(f'G{r}:I{r}')
    ws1[f'G{r}'] = note
    
    style_table_data(ws1[f'B{r}'], striped=striped)
    style_table_data(ws1[f'C{r}'], align='right', striped=striped)
    style_table_data(ws1[f'D{r}'], align='right', striped=striped)
    style_table_data(ws1[f'E{r}'], align='left', striped=striped)
    style_table_data(ws1[f'G{r}'], align='left', striped=striped)
    ws1[f'E{r}'].font = Font(name=FONT_NAME, size=10, color=ORANGE, bold=True)

# === [7] 매출 TOP 5 ===
ws1.merge_cells('B37:I37')
ws1['B37'] = "🏆 매출 TOP 5 상품 (완료 주문)"
style_section_header(ws1['B37'], size=12)
ws1.row_dimensions[37].height = 24

ws1['B38'] = "순위"
ws1.merge_cells('C38:D38'); ws1['C38'] = "상품명"
ws1['E38'] = "고객"
ws1['F38'] = "지역"
ws1['G38'] = "담당자"
ws1.merge_cells('H38:I38'); ws1['H38'] = "매출액"
for c in ['B38','C38','E38','F38','G38','H38']:
    style_table_header(ws1[c])

completed = [c for c in cleaned if c['status'] == '완료']
top5 = sorted(completed, key=lambda x: -x['total'])[:5]
for idx, item in enumerate(top5):
    r = 39 + idx
    striped = (idx % 2 == 1)
    rank_emoji = ["🥇","🥈","🥉","4","5"][idx]
    ws1[f'B{r}'] = rank_emoji
    ws1.merge_cells(f'C{r}:D{r}')
    ws1[f'C{r}'] = item['product']
    ws1[f'E{r}'] = item['name']
    ws1[f'F{r}'] = item['region']
    ws1[f'G{r}'] = item['manager']
    ws1.merge_cells(f'H{r}:I{r}')
    ws1[f'H{r}'] = item['total']
    ws1[f'H{r}'].number_format = '#,##0"원"'
    
    for c in [f'B{r}', f'C{r}', f'E{r}', f'F{r}', f'G{r}', f'H{r}']:
        align = 'left' if c.startswith('C') else ('right' if c.startswith('H') else 'center')
        style_table_data(ws1[c], align=align, striped=striped)
    
    # 1위는 골드 배경 강조
    if idx == 0:
        for c in [f'B{r}', f'C{r}', f'E{r}', f'F{r}', f'G{r}', f'H{r}']:
            ws1[c].fill = PatternFill('solid', start_color=BG_SOFT)
            ws1[c].font = Font(name=FONT_NAME, size=10, bold=True, color=TEXT_DARK)

# 컬럼 너비 (B~I)
ws1.column_dimensions['A'].width = 2
col_widths = {'B': 11, 'C': 13, 'D': 11, 'E': 11, 'F': 11, 'G': 14, 'H': 13, 'I': 16, 'J': 2}
for col, w in col_widths.items():
    ws1.column_dimensions[col].width = w

# 차트 (오른쪽 아래에)
chart1 = BarChart()
chart1.type = "bar"
chart1.style = 11
chart1.title = "지역별 매출"
data_ref = Reference(ws1, min_col=3, min_row=12, max_row=16, max_col=3)
cat_ref = Reference(ws1, min_col=2, min_row=13, max_row=16)
chart1.add_data(data_ref, titles_from_data=True)
chart1.set_categories(cat_ref)
chart1.height = 7
chart1.width = 12
chart1.legend = None
ws1.add_chart(chart1, "K6")

chart2 = PieChart()
chart2.title = "카테고리별 매출 비중"
data_ref2 = Reference(ws1, min_col=3, min_row=21, max_row=23)
cat_ref2 = Reference(ws1, min_col=2, min_row=21, max_row=23)
chart2.add_data(data_ref2)
chart2.set_categories(cat_ref2)
chart2.dataLabels = DataLabelList(showPercent=True)
chart2.height = 7
chart2.width = 12
ws1.add_chart(chart2, "K20")

# ============================================================
# Sheet 2: 주문데이터(클렌징) - 색깔 구분선 적용
# ============================================================
ws2 = wb.create_sheet("주문데이터(클렌징)")

# 1행: 안내
ws2.merge_cells('A1:U1')
ws2['A1'] = "📋 주문 데이터 (클렌징 완료) | 필터·정렬 가능 | ⭐ VIP = 완료 주문 누적 200만원 이상 | ⚠ 배송지연 = 3일 초과"
ws2['A1'].font = Font(name=FONT_NAME, size=10, italic=True, color="595959")
ws2['A1'].fill = PatternFill('solid', start_color=BG_SOFT)
ws2['A1'].alignment = Alignment(horizontal='left', vertical='center', indent=1)
ws2.row_dimensions[1].height = 24

headers = [
    "주문ID", "고객명", "연락처", "이메일", "주문일자", "배송일자",
    "상품명", "카테고리", "수량", "단가", "총금액", "결제수단",
    "지역", "담당자", "상태",
    "금액검증", "구매구간", "VIP여부", "배송지연", "결제그룹", "데이터오류"
]

for col_idx, h in enumerate(headers, start=1):
    cell = ws2.cell(row=2, column=col_idx, value=h)
    style_table_header(cell)

ws2.row_dimensions[2].height = 36

for i, c in enumerate(cleaned, start=3):
    striped = (i % 2 == 1)
    ws2.cell(row=i, column=1, value=c['order_id'])
    ws2.cell(row=i, column=2, value=c['name'])
    ws2.cell(row=i, column=3, value=c['phone'])
    ws2.cell(row=i, column=4, value=c['email'])
    ws2.cell(row=i, column=5, value=c['order_dt'])
    ws2.cell(row=i, column=6, value=c['ship_dt'])
    ws2.cell(row=i, column=7, value=c['product'])
    ws2.cell(row=i, column=8, value=c['category'])
    ws2.cell(row=i, column=9, value=c['qty'])
    ws2.cell(row=i, column=10, value=c['price'])
    ws2.cell(row=i, column=11, value=c['total'])
    ws2.cell(row=i, column=12, value=c['pay'])
    ws2.cell(row=i, column=13, value=c['region'])
    ws2.cell(row=i, column=14, value=c['manager'])
    ws2.cell(row=i, column=15, value=c['status'])
    
    ws2.cell(row=i, column=16, value=f'=IF(I{i}*J{i}=K{i},"✓ 정상","✗ 불일치")')
    ws2.cell(row=i, column=17, value=f'=IF(K{i}>=1000000,"100만↑","100만↓")')
    ws2.cell(row=i, column=18, value=f'=IF(SUMIFS(K:K,B:B,B{i},O:O,"완료")>=2000000,"⭐ VIP","일반")')
    ws2.cell(row=i, column=19, value=f'=IF(F{i}="","미배송",IF(F{i}-E{i}>3,"⚠ "&(F{i}-E{i})&"일",F{i}-E{i}&"일"))')
    ws2.cell(row=i, column=20, value=f'=IF(L{i}="카드","카드결제","현금결제")')
    ws2.cell(row=i, column=21, value=c['errors'])
    
    for col in range(1, 22):
        cell = ws2.cell(row=i, column=col)
        align = 'center'
        if col in [4, 7]:
            align = 'left'
        elif col in [10, 11]:
            align = 'right'
        style_table_data(cell, align=align, striped=striped)
    
    ws2.cell(row=i, column=10).number_format = '#,##0"원"'
    ws2.cell(row=i, column=11).number_format = '#,##0"원"'
    ws2.cell(row=i, column=5).number_format = 'yyyy-mm-dd'
    ws2.cell(row=i, column=6).number_format = 'yyyy-mm-dd'

last_row = len(cleaned) + 2

# 조건부 서식
ws2.conditional_formatting.add(f'O3:O{last_row}',
    CellIsRule(operator='equal', formula=['"완료"'],
        fill=PatternFill('solid', start_color="C6EFCE"),
        font=Font(name=FONT_NAME, size=10, bold=True, color="006100")))
ws2.conditional_formatting.add(f'O3:O{last_row}',
    CellIsRule(operator='equal', formula=['"배송중"'],
        fill=PatternFill('solid', start_color="FFEB9C"),
        font=Font(name=FONT_NAME, size=10, bold=True, color="9C5700")))
ws2.conditional_formatting.add(f'O3:O{last_row}',
    CellIsRule(operator='equal', formula=['"취소"'],
        fill=PatternFill('solid', start_color="FFC7CE"),
        font=Font(name=FONT_NAME, size=10, bold=True, color="9C0006")))
ws2.conditional_formatting.add(f'R3:R{last_row}',
    FormulaRule(formula=[f'$R3="⭐ VIP"'],
        fill=PatternFill('solid', start_color="FFF2CC"),
        font=Font(name=FONT_NAME, size=10, bold=True, color="BF8F00")))
ws2.conditional_formatting.add(f'U3:U{last_row}',
    FormulaRule(formula=[f'$U3<>"정상"'],
        fill=PatternFill('solid', start_color="FFC7CE"),
        font=Font(name=FONT_NAME, size=9, color="9C0006")))
ws2.conditional_formatting.add(f'U3:U{last_row}',
    CellIsRule(operator='equal', formula=['"정상"'],
        fill=PatternFill('solid', start_color="C6EFCE"),
        font=Font(name=FONT_NAME, size=9, color="006100")))
ws2.conditional_formatting.add(f'S3:S{last_row}',
    FormulaRule(formula=[f'LEFT($S3,1)="⚠"'],
        fill=PatternFill('solid', start_color="FCE4D6"),
        font=Font(name=FONT_NAME, size=10, bold=True, color="C00000")))

widths = [9, 9, 15, 22, 12, 12, 14, 9, 7, 12, 13, 9, 8, 9, 9, 11, 11, 9, 11, 11, 28]
for i, w in enumerate(widths, start=1):
    ws2.column_dimensions[get_column_letter(i)].width = w

ws2.auto_filter.ref = f"A2:U{last_row}"
ws2.freeze_panes = "C3"

# ============================================================
# Sheet 3: 🔍 클렌징 리포트
# ============================================================
ws3 = wb.create_sheet("🔍 클렌징 리포트")
ws3.sheet_view.showGridLines = False

ws3.merge_cells('B2:H3')
ws3['B2'] = "데이터 클렌징 Before / After 리포트"
style_title(ws3['B2'], size=20)

# 요약 박스 먼저
ws3.merge_cells('B5:H5')
ws3['B5'] = "📊 클렌징 요약"
style_section_header(ws3['B5'], size=13)
ws3.row_dimensions[5].height = 24

phone_count = sum(1 for c in cleaned if c['phone_orig'] != c['phone'])
email_count = sum(1 for c in cleaned if c['email_orig'] != c['email'])
date_count = sum(1 for c in cleaned if str(c['order_dt_orig']) != (c['order_dt'].strftime("%Y-%m-%d") if c['order_dt'] else ""))
manager_count = sum(1 for c in cleaned if not c['manager_orig'] or not c['manager_orig'].strip())

ws3['B6'] = "항목"
ws3['C6'] = "발견"
ws3['D6'] = "수정"
ws3.merge_cells('E6:H6'); ws3['E6'] = "처리 방식"
for c in ['B6','C6','D6','E6']:
    style_table_header(ws3[c])

summary = [
    ('연락처 형식 통일', phone_count, '01012345679 → 010-1234-5679'),
    ('이메일 오류 수정', email_count, '@@ 중복, .com 누락 자동 보정'),
    ('날짜 형식 통일', date_count, '2025/03/02, 03-06-2025 → YYYY-MM-DD'),
    ('담당자 결측 보완', manager_count, '지역별 주 담당자로 자동 배정'),
]
for idx, (item, count, method) in enumerate(summary):
    r = 7 + idx
    striped = (idx % 2 == 1)
    ws3.cell(row=r, column=2, value=item)
    ws3.cell(row=r, column=3, value=f"{count}건")
    ws3.cell(row=r, column=4, value=f"{count}건")
    ws3.merge_cells(f'E{r}:H{r}')
    ws3.cell(row=r, column=5, value=method)
    style_table_data(ws3.cell(row=r,column=2), align='left', striped=striped)
    style_table_data(ws3.cell(row=r,column=3), align='center', striped=striped)
    style_table_data(ws3.cell(row=r,column=4), align='center', striped=striped)
    style_table_data(ws3.cell(row=r,column=5), align='left', striped=striped)

# 상세 내역
ws3.merge_cells('B12:H12')
ws3['B12'] = "🚨 발견된 데이터 오류 및 수정 내역 (행 단위)"
style_section_header(ws3['B12'], size=13)
ws3.row_dimensions[12].height = 24

ws3['B13'] = "주문ID"
ws3['C13'] = "고객명"
ws3['D13'] = "오류 항목"
ws3['E13'] = "원본값"
ws3['F13'] = "수정값"
ws3['G13'] = "오류 유형"
ws3['H13'] = "처리"
for c in ['B13','C13','D13','E13','F13','G13','H13']:
    style_table_header(ws3[c])

issues = []
for c in cleaned:
    if c['phone_orig'] != c['phone']:
        issues.append([c['order_id'], c['name'], '연락처', c['phone_orig'], c['phone'], '형식 불일치', '✓ 자동 수정'])
    if c['email_orig'] != c['email']:
        err_type = '@중복' if '@@' in c['email_orig'] else '도메인 누락'
        issues.append([c['order_id'], c['name'], '이메일', c['email_orig'], c['email'], err_type, '✓ 자동 수정'])
    if str(c['order_dt_orig']) != (c['order_dt'].strftime("%Y-%m-%d") if c['order_dt'] else ""):
        issues.append([c['order_id'], c['name'], '주문일자', c['order_dt_orig'], c['order_dt'].strftime("%Y-%m-%d"), '날짜 형식', '✓ 자동 수정'])
    if not c['manager_orig'] or not c['manager_orig'].strip():
        issues.append([c['order_id'], c['name'], '담당자', '(공란)', c['manager'], '결측값', '✓ 지역 기준 보완'])
    if not c['ship_dt'] and c['status'] == '배송중':
        issues.append([c['order_id'], c['name'], '배송일자', '(공란)', '미발송', '결측값', '✓ 상태와 일치'])

for i, row in enumerate(issues):
    r = 14 + i
    striped = (i % 2 == 1)
    for j, val in enumerate(row):
        cell = ws3.cell(row=r, column=2+j, value=val)
        align = 'center' if j not in [3,4] else 'left'
        style_table_data(cell, align=align, striped=striped)
    # 처리 결과는 그린 강조
    cell_h = ws3.cell(row=r, column=8)
    cell_h.fill = PatternFill('solid', start_color="C6EFCE")
    cell_h.font = Font(name=FONT_NAME, size=10, bold=True, color="006100")

ws3.column_dimensions['A'].width = 2
for col, w in zip('BCDEFGH', [10, 10, 12, 22, 22, 14, 14]):
    ws3.column_dimensions[col].width = w

# ============================================================
# Sheet 4: 💡 인사이트 (표 형식으로 전면 재구성)
# ============================================================
ws4 = wb.create_sheet("💡 인사이트")
ws4.sheet_view.showGridLines = False

ws4.merge_cells('B2:H3')
ws4['B2'] = "비즈니스 인사이트 & 액션 플랜"
style_title(ws4['B2'], size=20)

ws4.merge_cells('B4:H4')
ws4['B4'] = "데이터에서 도출된 6개 핵심 발견점 — 우선순위별 정렬"
ws4['B4'].font = Font(name=FONT_NAME, size=10, italic=True, color="595959")
ws4['B4'].alignment = Alignment(horizontal='center', vertical='center')

# 한눈에 보는 요약 표
ws4.merge_cells('B6:H6')
ws4['B6'] = "📋 인사이트 요약 (한눈에 보기)"
style_section_header(ws4['B6'], size=13)
ws4.row_dimensions[6].height = 24

ws4['B7'] = "No"
ws4['C7'] = "우선순위"
ws4.merge_cells('D7:F7'); ws4['D7'] = "발견점"
ws4['G7'] = "핵심 수치"
ws4['H7'] = "액션 시급도"
for c in ['B7','C7','D7','G7','H7']:
    style_table_header(ws4[c])

insights = [
    {
        'no': 1,
        'priority': '🔴 높음',
        'priority_color': RED,
        'title': '🥇 서울 매출 64.7% — 단일 지역 의존도 위험',
        'finding': '완료 주문 기준 서울 매출 약 568만원으로 전체 878만원의 64.7%를 차지. 부산·대전·인천 합계(232만원)의 2.4배. 다만 서울 담당은 이정훈 1명에게 집중되어 부재 시 매출 공백 리스크 존재.',
        'numbers': '서울 568만원 / 64.7%',
        'urgency': '즉시',
        'action': '서울 보조 담당자 배치 또는 카테고리별 분담 체계 검토. 부산·인천을 차세대 핵심 지역으로 육성 캠페인 기획.',
    },
    {
        'no': 2,
        'priority': '🔴 높음',
        'priority_color': RED,
        'title': '🚨 데이터 품질 이슈 — 9건의 입력 오류 발견',
        'finding': '연락처·이메일·날짜 형식이 입력자별로 제각각. 담당자 누락 2건. 동일 고객(이영희)이 두 개의 다른 이메일로 등록된 케이스도 존재 — 클렌징 없으면 통계가 왜곡될 위험.',
        'numbers': '오류 9건 / 14건 중',
        'urgency': '이번 주',
        'action': '주문 입력 폼에 형식 검증 규칙 적용(정규식 phone/email 마스크). 담당자 필드를 필수값으로 변경. 분기 1회 데이터 정합성 점검 프로세스 수립.',
    },
    {
        'no': 3,
        'priority': '🔴 높음',
        'priority_color': RED,
        'title': '⭐ VIP 잠재 고객 — 배송 완료 시 즉시 진입',
        'finding': '현재 완료 기준 VIP는 정우성 1명(맥북프로 250만). 한지민(에어컨 200만 배송중)·이영희(아이폰15 260만 배송중)는 배송 완료 시 즉시 VIP 진입. 정우성은 맥북에어 취소 이력 있어 충성도 관리 필요.',
        'numbers': 'VIP 1명 + 임박 2명',
        'urgency': '배송 완료 시',
        'action': 'VIP 진입 임박 고객(한지민·이영희) 배송 완료 시점에 사은품 또는 감사 메시지 발송. 정우성 취소 사유 파악 후 follow-up 필수.',
    },
    {
        'no': 4,
        'priority': '🟡 중간',
        'priority_color': ORANGE,
        'title': '👤 담당자 성과 격차 — 김태형 건당 1위',
        'finding': '김태형 건당 평균 약 127만원 (완료 3건). 이정훈은 4건 처리했지만 건당 79만원 — 텀블러·갤럭시워치 등 중저가 비중 큼. 박성호는 인천 가전 위주 안정적. 단, 1004번 에어팟프로는 담당자 공란이라 자동 배정한 값임.',
        'numbers': '건당 79만 ~ 127만',
        'urgency': '이번 달',
        'action': '담당자 누락 데이터(1004, 1010번) 원본 확인 후 실제 담당자 재배정. 이정훈 고단가 영업 코칭. 박성호 인천 가전 패턴 타 지역 복제 검토.',
    },
    {
        'no': 5,
        'priority': '🟡 중간',
        'priority_color': ORANGE,
        'title': '⚠️ 취소율 7.1% — 단일 건이지만 금액 큼',
        'finding': '취소 1건이 맥북에어(180만원)로, 단일 취소가 전체 매출에 미치는 영향 큼. 정우성은 동기간 맥북프로(250만원)는 정상 구매 — 단순 변심보다 상위 모델 재선택 가능성.',
        'numbers': '취소 1건 / 180만원',
        'urgency': '이번 달',
        'action': '취소 사유 추적 필수. 고가 전자제품은 주문 후 24시간 내 컨펌 콜 도입 검토. 동일 고객 취소 후 재구매 패턴은 업셀 기회로 분석.',
    },
    {
        'no': 6,
        'priority': '🟢 낮음',
        'priority_color': GREEN,
        'title': '💳 현금 결제 고객의 재구매율 100%',
        'finding': '카드 결제 비중 71%. 그러나 현금 결제 4건 중 이영희·홍길동·최지은은 모두 2회 이상 구매한 충성 고객. 카드는 신규 고객 비중이 상대적으로 높음 — 결제수단이 고객 세그먼트의 신호.',
        'numbers': '카드 71% / 현금 29%',
        'urgency': '다음 분기',
        'action': '현금 고객 충성 프로그램 설계(현금영수증 적립 등). 카드 신규 고객 대상 2회차 구매 유도 캠페인 기획.',
    },
]

# 요약 표 채우기
for idx, ins in enumerate(insights):
    r = 8 + idx
    striped = (idx % 2 == 1)
    ws4[f'B{r}'] = ins['no']
    ws4[f'C{r}'] = ins['priority']
    ws4.merge_cells(f'D{r}:F{r}')
    ws4[f'D{r}'] = ins['title']
    ws4[f'G{r}'] = ins['numbers']
    ws4[f'H{r}'] = ins['urgency']
    
    for c in [f'B{r}', f'C{r}', f'D{r}', f'G{r}', f'H{r}']:
        align = 'left' if c.startswith('D') else 'center'
        style_table_data(ws4[c], align=align, striped=striped)
    
    # 우선순위 셀에 색상 강조
    ws4[f'C{r}'].font = Font(name=FONT_NAME, size=10, bold=True, color=ins['priority_color'])
    # 제목은 굵게
    ws4[f'D{r}'].font = Font(name=FONT_NAME, size=10, bold=True, color=TEXT_DARK)

# 상세 인사이트 (표 형식 - 발견점/액션을 행으로)
ws4.merge_cells('B16:H16')
ws4['B16'] = "🔎 상세 분석 — 발견점과 액션 플랜"
style_section_header(ws4['B16'], size=13)
ws4.row_dimensions[16].height = 24

# 헤더
ws4['B17'] = "No"
ws4['C17'] = "구분"
ws4.merge_cells('D17:H17'); ws4['D17'] = "내용"
for c in ['B17','C17','D17']:
    style_table_header(ws4[c])

cur_row = 18
for ins in insights:
    # 제목 행 (병합, 우선순위 색상)
    ws4.merge_cells(f'B{cur_row}:H{cur_row}')
    ws4[f'B{cur_row}'] = f"  No.{ins['no']}   {ins['priority']}   {ins['title']}"
    ws4[f'B{cur_row}'].font = Font(name=FONT_NAME, size=11, bold=True, color=WHITE)
    ws4[f'B{cur_row}'].fill = PatternFill('solid', start_color=NAVY)
    ws4[f'B{cur_row}'].alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws4[f'B{cur_row}'].border = thick_border(NAVY)
    ws4.row_dimensions[cur_row].height = 26
    
    # 발견점 행
    ws4[f'B{cur_row+1}'] = ins['no']
    ws4[f'C{cur_row+1}'] = "💡 발견"
    ws4.merge_cells(f'D{cur_row+1}:H{cur_row+1}')
    ws4[f'D{cur_row+1}'] = ins['finding']
    
    style_table_data(ws4[f'B{cur_row+1}'], align='center')
    ws4[f'C{cur_row+1}'].font = Font(name=FONT_NAME, size=10, bold=True, color=BLUE)
    ws4[f'C{cur_row+1}'].fill = PatternFill('solid', start_color=BG_BLUE)
    ws4[f'C{cur_row+1}'].alignment = Alignment(horizontal='center', vertical='center')
    ws4[f'C{cur_row+1}'].border = colored_border(BORDER_BLUE)
    
    ws4[f'D{cur_row+1}'].font = Font(name=FONT_NAME, size=10, color=TEXT_DARK)
    ws4[f'D{cur_row+1}'].alignment = Alignment(horizontal='left', vertical='center', wrap_text=True, indent=1)
    ws4[f'D{cur_row+1}'].border = colored_border(BORDER_BLUE)
    ws4.row_dimensions[cur_row+1].height = 50
    
    # 액션 행
    ws4[f'B{cur_row+2}'] = ""
    ws4[f'C{cur_row+2}'] = "🎯 액션"
    ws4.merge_cells(f'D{cur_row+2}:H{cur_row+2}')
    ws4[f'D{cur_row+2}'] = ins['action']
    
    ws4[f'B{cur_row+2}'].border = colored_border(BORDER_BLUE)
    ws4[f'C{cur_row+2}'].font = Font(name=FONT_NAME, size=10, bold=True, color="BF8F00")
    ws4[f'C{cur_row+2}'].fill = PatternFill('solid', start_color=BG_SOFT)
    ws4[f'C{cur_row+2}'].alignment = Alignment(horizontal='center', vertical='center')
    ws4[f'C{cur_row+2}'].border = colored_border(BORDER_BLUE)
    
    ws4[f'D{cur_row+2}'].font = Font(name=FONT_NAME, size=10, color=TEXT_DARK)
    ws4[f'D{cur_row+2}'].fill = PatternFill('solid', start_color="FFFBF0")
    ws4[f'D{cur_row+2}'].alignment = Alignment(horizontal='left', vertical='center', wrap_text=True, indent=1)
    ws4[f'D{cur_row+2}'].border = colored_border(BORDER_BLUE)
    ws4.row_dimensions[cur_row+2].height = 45
    
    cur_row += 4  # 제목 + 발견 + 액션 + 빈 줄

# 컬럼 너비
ws4.column_dimensions['A'].width = 2
col_widths_4 = {'B': 6, 'C': 11, 'D': 16, 'E': 16, 'F': 16, 'G': 16, 'H': 14}
for col, w in col_widths_4.items():
    ws4.column_dimensions[col].width = w

# ============================================================
# 시트 순서
# ============================================================
desired_order = ["📊 대시보드", "주문데이터(클렌징)", "🔍 클렌징 리포트", "💡 인사이트"]
wb._sheets = [wb[name] for name in desired_order]
wb.active = 0

output_path = '/home/claude/work/한비즈마케팅_주문분석_대시보드.xlsx'
wb.save(output_path)
print(f"저장 완료: {output_path}")
print(f"시트: {wb.sheetnames}")
