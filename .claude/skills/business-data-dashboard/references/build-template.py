"""
Business Data Dashboard - Build Template
========================================
새 데이터를 받으면 이 템플릿을 베이스로 다음 부분만 수정한다:

1. raw_data: 사용자 데이터로 교체
2. column_mapping: 도메인에 맞게 컬럼명 조정
3. 시트명·인사이트 본문: 도메인 톤에 맞게 작성

이 템플릿은 14컬럼 거래 데이터를 가정한다 (주문/물류/배송/구매 모두 호환).
컬럼 수가 다르면 헤더 리스트와 데이터 매핑만 조정.
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
# [1] 데이터 입력부 - 사용자 데이터로 교체할 부분
# ============================================================
# 컬럼 순서: ID, 고객/거래처, 연락처, 이메일, 시작일, 종료일,
#            품목, 카테고리, 수량, 단가, 총금액, 결제/방식,
#            지역/거점, 담당자, 상태
raw_data = [
    # 예시 - 실제 데이터로 교체
    # [1001, "고객A", "010-1234-5678", "a@x.com", "2025-03-01", "2025-03-03",
    #  "상품A", "전자", 1, 1200000, 1200000, "카드", "서울", "이정훈", "완료"],
]

# ============================================================
# [2] 도메인 설정 - 데이터 성격에 맞게 변경
# ============================================================
DOMAIN = {
    'sheet_name_data': "주문데이터(클렌징)",  # 또는 "배송데이터(클렌징)" 등
    'title': "한비즈마케팅 주문 데이터 분석 대시보드",
    'period_label': "분석 기간",
    'count_label': "총 주문 건수",
    'kpi_revenue_label': "💰 총 매출액 (완료)",
    'kpi_count_label': "📦 총 주문 건수",
    'kpi_avg_label': "💳 평균 주문액",
    'kpi_cancel_label': "⚠️ 취소율",
    'completed_status': "완료",       # 완료를 의미하는 상태값
    'cancelled_status': "취소",       # 실패/취소를 의미하는 상태값
    'in_progress_status': "배송중",   # 진행중 상태값
    'vip_threshold': 2000000,         # VIP 판정 임계금액
    'high_value_threshold': 1000000,  # 고액 거래 임계금액
    'delay_days': 3,                   # 지연 판정 일수
}

# ============================================================
# [3] 디자인 시스템 (변경 금지)
# ============================================================
NAVY = "1F3864"
BLUE = "2E75B6"
GOLD = "FFC000"
GREEN = "70AD47"
RED = "C00000"
ORANGE = "ED7D31"
BG_GRAY = "F2F2F2"
BG_SOFT = "FFF2CC"
BG_BLUE = "DDEBF7"
BG_GREEN = "E2EFDA"
TEXT_DARK = "262626"
WHITE = "FFFFFF"
BORDER_BLUE = "8FAADC"
FONT_NAME = "맑은 고딕"

def colored_border(color=BORDER_BLUE, weight='thin'):
    side = Side(style=weight, color=color)
    return Border(left=side, right=side, top=side, bottom=side)

def thick_border(color=NAVY):
    side = Side(style='medium', color=color)
    return Border(left=side, right=side, top=side, bottom=side)

def style_title(cell, size=20):
    cell.font = Font(name=FONT_NAME, size=size, bold=True, color=WHITE)
    cell.fill = PatternFill('solid', start_color=NAVY)
    cell.alignment = Alignment(horizontal='center', vertical='center')

def style_section_header(cell, size=12):
    cell.font = Font(name=FONT_NAME, size=size, bold=True, color=WHITE)
    cell.fill = PatternFill('solid', start_color=BLUE)
    cell.alignment = Alignment(horizontal='left', vertical='center', indent=1)

def style_table_header(cell):
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
# [4] 클렌징 함수
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

def fill_manager(manager, region, region_map):
    if manager and str(manager).strip():
        return manager
    return region_map.get(region, "미배정")

# ============================================================
# [5] 클렌징 처리
# ============================================================
def process_data(raw_data, region_map=None):
    if region_map is None:
        # 데이터에서 지역별 주 담당자 자동 추출
        region_map = {}
        from collections import Counter
        for row in raw_data:
            region = row[12]
            manager = row[13]
            if manager and str(manager).strip():
                region_map.setdefault(region, []).append(manager)
        region_map = {k: Counter(v).most_common(1)[0][0] for k, v in region_map.items() if v}
    
    cleaned = []
    for row in raw_data:
        order_id, name, phone, email, start_dt, end_dt, product, category, qty, price, total, pay, region, manager, status = row
        
        phone_clean = clean_phone(phone)
        email_clean = clean_email(email)
        start_dt_clean = clean_date(start_dt)
        end_dt_clean = clean_date(end_dt)
        manager_clean = fill_manager(manager, region, region_map)
        
        flags = []
        if phone != phone_clean: flags.append(f"연락처({phone})")
        if email != email_clean: flags.append(f"이메일({email})")
        if str(start_dt) != (start_dt_clean.strftime("%Y-%m-%d") if start_dt_clean else ""):
            flags.append(f"시작일({start_dt})")
        if not manager or not str(manager).strip(): flags.append("담당자누락")
        if not email_is_valid(email_clean): flags.append("이메일형식이상")
        
        cleaned.append({
            'order_id': order_id, 'name': name,
            'phone_orig': phone, 'phone': phone_clean,
            'email_orig': email, 'email': email_clean,
            'start_dt_orig': str(start_dt), 'start_dt': start_dt_clean,
            'end_dt_orig': str(end_dt) if end_dt else "", 'end_dt': end_dt_clean,
            'product': product, 'category': category, 'qty': qty,
            'price': price, 'total': total, 'pay': pay,
            'region': region, 'manager_orig': manager, 'manager': manager_clean,
            'status': status, 'errors': ", ".join(flags) if flags else "정상",
        })
    return cleaned

# ============================================================
# [6] 메인 빌드 함수 (호출 진입점)
# ============================================================
def build_dashboard(raw_data, output_path, domain_config=None):
    """
    raw_data: 14컬럼 거래 데이터 리스트
    output_path: 저장할 .xlsx 경로
    domain_config: DOMAIN 딕셔너리 (None이면 기본값 사용)
    """
    if domain_config is None:
        domain_config = DOMAIN
    
    cleaned = process_data(raw_data)
    wb = Workbook()
    wb.remove(wb.active)
    
    # 시트 빌드 (각 시트 빌드 함수는 별도 분리해도 됨)
    build_dashboard_sheet(wb, cleaned, domain_config)
    build_data_sheet(wb, cleaned, domain_config)
    build_cleaning_report_sheet(wb, cleaned, domain_config)
    build_insights_sheet(wb, cleaned, domain_config)
    
    # 시트 순서 정렬
    desired_order = ["📊 대시보드", domain_config['sheet_name_data'],
                     "🔍 클렌징 리포트", "💡 인사이트"]
    wb._sheets = [wb[name] for name in desired_order]
    wb.active = 0
    
    wb.save(output_path)
    return output_path


# ============================================================
# [7] 시트별 빌드 함수
# ============================================================
def build_dashboard_sheet(wb, cleaned, cfg):
    """대시보드 시트 - 위→아래 단일 흐름"""
    ws = wb.create_sheet("📊 대시보드")
    ws.sheet_view.showGridLines = False
    sheet_name = cfg['sheet_name_data']
    
    # 타이틀
    ws.merge_cells('B2:I3')
    ws['B2'] = cfg['title']
    style_title(ws['B2'], size=22)
    
    ws.merge_cells('B4:I4')
    ws['B4'] = f"{cfg['period_label']}: 자동 산출   |   {cfg['count_label']}: {len(cleaned)}건   |   작성일: {datetime.now().strftime('%Y-%m-%d')}"
    ws['B4'].font = Font(name=FONT_NAME, size=10, italic=True, color="595959")
    ws['B4'].alignment = Alignment(horizontal='center', vertical='center')
    
    # KPI
    ws.merge_cells('B6:I6')
    ws['B6'] = "🎯 핵심 지표"
    style_section_header(ws['B6'], size=13)
    ws.row_dimensions[6].height = 26
    
    completed = cfg['completed_status']
    cancelled = cfg['cancelled_status']
    
    # KPI 4종
    ws.merge_cells('B7:C7'); ws['B7'] = cfg['kpi_revenue_label']; style_kpi_label(ws['B7'])
    ws.merge_cells('B8:C9')
    ws['B8'] = f'=SUMIFS(\'{sheet_name}\'!K:K,\'{sheet_name}\'!O:O,"{completed}")'
    ws['B8'].number_format = '#,##0"원"'
    style_kpi_value(ws['B8'], NAVY)
    
    ws.merge_cells('D7:E7'); ws['D7'] = cfg['kpi_count_label']; style_kpi_label(ws['D7'])
    ws.merge_cells('D8:E9')
    ws['D8'] = f'=COUNTA(\'{sheet_name}\'!A:A)-2'
    ws['D8'].number_format = '#,##0"건"'
    style_kpi_value(ws['D8'], BLUE)
    
    ws.merge_cells('F7:G7'); ws['F7'] = cfg['kpi_avg_label']; style_kpi_label(ws['F7'])
    ws.merge_cells('F8:G9')
    ws['F8'] = f'=AVERAGEIFS(\'{sheet_name}\'!K:K,\'{sheet_name}\'!O:O,"{completed}")'
    ws['F8'].number_format = '#,##0"원"'
    style_kpi_value(ws['F8'], GREEN)
    
    ws.merge_cells('H7:I7'); ws['H7'] = cfg['kpi_cancel_label']; style_kpi_label(ws['H7'])
    ws.merge_cells('H8:I9')
    ws['H8'] = f'=COUNTIF(\'{sheet_name}\'!O:O,"{cancelled}")/(COUNTA(\'{sheet_name}\'!A:A)-2)'
    ws['H8'].number_format = '0.0%'
    style_kpi_value(ws['H8'], RED)
    
    ws.row_dimensions[7].height = 22
    ws.row_dimensions[8].height = 28
    ws.row_dimensions[9].height = 28
    
    # 컬럼 너비
    ws.column_dimensions['A'].width = 2
    col_widths = {'B': 11, 'C': 13, 'D': 11, 'E': 11, 'F': 11, 'G': 14, 'H': 13, 'I': 16, 'J': 2}
    for col, w in col_widths.items():
        ws.column_dimensions[col].width = w
    
    # NOTE: 지역별/카테고리별/담당자별/결제수단별/TOP5 표는 build_excel_v2.py 참고하여 추가.
    # 본 템플릿은 핵심 골격만 제공.
    return ws


def build_data_sheet(wb, cleaned, cfg):
    """데이터 시트 - 1행 안내, 2행 헤더, 3행부터 데이터"""
    sheet_name = cfg['sheet_name_data']
    ws = wb.create_sheet(sheet_name)
    
    ws.merge_cells('A1:U1')
    ws['A1'] = f"📋 {sheet_name} | 필터·정렬 가능 | ⭐ VIP = {cfg['completed_status']} 상태 누적 {cfg['vip_threshold']:,}원 이상 | ⚠ 지연 = {cfg['delay_days']}일 초과"
    ws['A1'].font = Font(name=FONT_NAME, size=10, italic=True, color="595959")
    ws['A1'].fill = PatternFill('solid', start_color=BG_SOFT)
    ws['A1'].alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[1].height = 24
    
    headers = [
        "ID", "고객/거래처", "연락처", "이메일", "시작일", "종료일",
        "품목", "카테고리", "수량", "단가", "총금액", "결제/방식",
        "지역", "담당자", "상태",
        "금액검증", "구매구간", "VIP여부", "지연일수", "결제그룹", "데이터오류"
    ]
    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=2, column=col_idx, value=h)
        style_table_header(cell)
    ws.row_dimensions[2].height = 36
    
    completed = cfg['completed_status']
    vip_threshold = cfg['vip_threshold']
    high_value = cfg['high_value_threshold']
    delay_days = cfg['delay_days']
    
    for i, c in enumerate(cleaned, start=3):
        striped = (i % 2 == 1)
        ws.cell(row=i, column=1, value=c['order_id'])
        ws.cell(row=i, column=2, value=c['name'])
        ws.cell(row=i, column=3, value=c['phone'])
        ws.cell(row=i, column=4, value=c['email'])
        ws.cell(row=i, column=5, value=c['start_dt'])
        ws.cell(row=i, column=6, value=c['end_dt'])
        ws.cell(row=i, column=7, value=c['product'])
        ws.cell(row=i, column=8, value=c['category'])
        ws.cell(row=i, column=9, value=c['qty'])
        ws.cell(row=i, column=10, value=c['price'])
        ws.cell(row=i, column=11, value=c['total'])
        ws.cell(row=i, column=12, value=c['pay'])
        ws.cell(row=i, column=13, value=c['region'])
        ws.cell(row=i, column=14, value=c['manager'])
        ws.cell(row=i, column=15, value=c['status'])
        
        # 파생 컬럼 (수식)
        ws.cell(row=i, column=16, value=f'=IF(I{i}*J{i}=K{i},"✓ 정상","✗ 불일치")')
        ws.cell(row=i, column=17, value=f'=IF(K{i}>={high_value},"고액","일반")')
        ws.cell(row=i, column=18, value=f'=IF(SUMIFS(K:K,B:B,B{i},O:O,"{completed}")>={vip_threshold},"⭐ VIP","일반")')
        ws.cell(row=i, column=19, value=f'=IF(F{i}="","미발송",IF(F{i}-E{i}>{delay_days},"⚠ "&(F{i}-E{i})&"일",F{i}-E{i}&"일"))')
        ws.cell(row=i, column=20, value=f'=IF(L{i}="카드","카드결제","현금결제")')
        ws.cell(row=i, column=21, value=c['errors'])
        
        for col in range(1, 22):
            cell = ws.cell(row=i, column=col)
            align = 'center'
            if col in [4, 7]:
                align = 'left'
            elif col in [10, 11]:
                align = 'right'
            style_table_data(cell, align=align, striped=striped)
        
        ws.cell(row=i, column=10).number_format = '#,##0"원"'
        ws.cell(row=i, column=11).number_format = '#,##0"원"'
        ws.cell(row=i, column=5).number_format = 'yyyy-mm-dd'
        ws.cell(row=i, column=6).number_format = 'yyyy-mm-dd'
    
    last_row = len(cleaned) + 2
    
    # 조건부 서식
    ws.conditional_formatting.add(f'O3:O{last_row}',
        CellIsRule(operator='equal', formula=[f'"{completed}"'],
            fill=PatternFill('solid', start_color="C6EFCE"),
            font=Font(name=FONT_NAME, size=10, bold=True, color="006100")))
    ws.conditional_formatting.add(f'O3:O{last_row}',
        CellIsRule(operator='equal', formula=[f'"{cfg["cancelled_status"]}"'],
            fill=PatternFill('solid', start_color="FFC7CE"),
            font=Font(name=FONT_NAME, size=10, bold=True, color="9C0006")))
    
    widths = [9, 9, 15, 22, 12, 12, 14, 9, 7, 12, 13, 9, 8, 9, 9, 11, 11, 9, 11, 11, 28]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    
    ws.auto_filter.ref = f"A2:U{last_row}"
    ws.freeze_panes = "C3"
    return ws


def build_cleaning_report_sheet(wb, cleaned, cfg):
    """클렌징 리포트 시트"""
    ws = wb.create_sheet("🔍 클렌징 리포트")
    ws.sheet_view.showGridLines = False
    
    ws.merge_cells('B2:H3')
    ws['B2'] = "데이터 클렌징 Before / After 리포트"
    style_title(ws['B2'], size=20)
    
    # NOTE: 상세 구현은 build_excel_v2.py 참고
    return ws


def build_insights_sheet(wb, cleaned, cfg):
    """인사이트 시트 - 표 형식"""
    ws = wb.create_sheet("💡 인사이트")
    ws.sheet_view.showGridLines = False
    
    ws.merge_cells('B2:H3')
    ws['B2'] = "비즈니스 인사이트 & 액션 플랜"
    style_title(ws['B2'], size=20)
    
    # NOTE: 6개 인사이트 표 구현은 build_excel_v2.py 참고
    # 인사이트 본문은 받은 데이터에서 도출한 실제 수치로 작성
    return ws


# ============================================================
# [8] 검수 헬퍼
# ============================================================
def verify_workbook(output_path):
    """
    빌드 후 반드시 호출.
    1) recalc.py로 수식 오류 체크
    2) data_only=True로 핵심 KPI 검산
    """
    import subprocess
    import json
    from openpyxl import load_workbook
    
    # 1. 수식 재계산
    result = subprocess.run(
        ['python', '/mnt/skills/public/xlsx/scripts/recalc.py', output_path],
        capture_output=True, text=True
    )
    recalc_data = json.loads(result.stdout)
    if recalc_data['status'] != 'success':
        return False, f"수식 오류 발견: {recalc_data['error_summary']}"
    
    # 2. KPI 검산
    wb = load_workbook(output_path, data_only=True)
    ws = wb['📊 대시보드']
    
    issues = []
    if ws['B8'].value is None or ws['B8'].value == 0:
        issues.append("총매출 KPI가 비어있음")
    if ws['D8'].value is None or ws['D8'].value <= 0:
        issues.append("주문건수 KPI 이상")
    
    if issues:
        return False, "; ".join(issues)
    return True, "검수 통과"


# ============================================================
# 사용 예시
# ============================================================
if __name__ == "__main__":
    # raw_data를 채운 뒤
    output_path = '/home/claude/work/output.xlsx'
    build_dashboard(raw_data, output_path)
    ok, msg = verify_workbook(output_path)
    print(f"검수: {msg}")
