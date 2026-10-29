# Design System Reference

대시보드 빌드 시 사용하는 색상·스타일·테두리 정의.

## 색상 팔레트

```python
NAVY = "1F3864"        # 메인 헤더 (제목·표 헤더)
BLUE = "2E75B6"        # 서브 헤더 (섹션 제목)
GOLD = "FFC000"        # 강조 (액션 라벨)
GREEN = "70AD47"       # 정상 / 성공
RED = "C00000"         # 위험 / 취소
ORANGE = "ED7D31"      # 주의 / 경고
BG_GRAY = "F2F2F2"     # KPI 값 배경
BG_SOFT = "FFF2CC"     # 안내 박스, 1위 강조
BG_BLUE = "DDEBF7"     # 줄무늬 짝수 행 배경
BG_GREEN = "E2EFDA"    # 합계 행 배경
TEXT_DARK = "262626"   # 본문 텍스트
WHITE = "FFFFFF"       # 헤더 텍스트
BORDER_BLUE = "8FAADC" # 표 데이터 행 구분선
BORDER_GRAY = "BFBFBF" # 회색 보조 테두리

FONT_NAME = "맑은 고딕"  # 전체 통일
```

## 테두리 정의

```python
from openpyxl.styles import Border, Side

def colored_border(color="8FAADC", weight='thin'):
    side = Side(style=weight, color=color)
    return Border(left=side, right=side, top=side, bottom=side)

def thick_border(color="1F3864"):
    side = Side(style='medium', color=color)
    return Border(left=side, right=side, top=side, bottom=side)
```

## 스타일 함수 (그대로 복사해 사용)

### 타이틀 (시트 최상단)
```python
def style_title(cell, size=20):
    cell.font = Font(name=FONT_NAME, size=size, bold=True, color=WHITE)
    cell.fill = PatternFill('solid', start_color=NAVY)
    cell.alignment = Alignment(horizontal='center', vertical='center')
```

### 섹션 헤더 (각 표 위 한 줄)
```python
def style_section_header(cell, size=12):
    cell.font = Font(name=FONT_NAME, size=size, bold=True, color=WHITE)
    cell.fill = PatternFill('solid', start_color=BLUE)
    cell.alignment = Alignment(horizontal='left', vertical='center', indent=1)
```

### 표 헤더 (열 제목 행)
```python
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
```

### 표 데이터 셀 (줄무늬 옵션 포함)
```python
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
```

### 합계 행
```python
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
```

### KPI 카드
```python
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
```

## 시각화 막대 (REPT 패턴)

```python
# 비중 셀 옆에 가로 막대 배치
ws[f'E{r}'] = f'=REPT("■", ROUND(D{r}*30, 0))'

# 표마다 다른 색상 부여
# 지역 표 → BLUE
# 카테고리 표 → GREEN
# 결제수단 표 → ORANGE
ws[f'E{r}'].font = Font(name=FONT_NAME, size=10, color=BLUE, bold=True)
```

## 줄무늬 적용 패턴

```python
for idx, row_data in enumerate(data_rows):
    r = start_row + idx
    striped = (idx % 2 == 1)  # 짝수 인덱스(0,2,4..)는 흰색, 홀수(1,3,5..)는 파란 배경
    style_table_data(ws[f'B{r}'], striped=striped)
```

## 컬럼 너비 가이드

대시보드 시트 (B~I 8컬럼 사용):
```python
ws.column_dimensions['A'].width = 2  # 좌측 여백
col_widths = {'B': 11, 'C': 13, 'D': 11, 'E': 11, 'F': 11, 'G': 14, 'H': 13, 'I': 16, 'J': 2}
for col, w in col_widths.items():
    ws.column_dimensions[col].width = w
```

데이터 시트 (21컬럼):
```python
widths = [9, 9, 15, 22, 12, 12, 14, 9, 7, 12, 13, 9, 8, 9, 9, 11, 11, 9, 11, 11, 28]
for i, w in enumerate(widths, start=1):
    ws.column_dimensions[get_column_letter(i)].width = w
```

## 행 높이 가이드

| 용도 | 높이 |
|---|---|
| 안내 메시지 행 | 24 |
| 표 헤더 행 | 36 |
| 일반 데이터 행 | 기본값 |
| KPI 라벨 | 22 |
| KPI 값 | 28 |
| 섹션 헤더 | 24-26 |
| 인사이트 발견점 행 | 50 |
| 인사이트 액션 행 | 45 |

## 그리드라인 / 필터 / 틀고정

```python
# 대시보드·인사이트 시트는 그리드 숨김
ws.sheet_view.showGridLines = False

# 데이터 시트는 필터 + 틀고정
ws.auto_filter.ref = f"A2:U{last_row}"  # 헤더가 2행이면 A2부터
ws.freeze_panes = "C3"  # 고객명까지 고정
```

## 조건부 서식 패턴

```python
from openpyxl.formatting.rule import CellIsRule, FormulaRule

# 상태별 색상 (완료=그린, 진행중=노랑, 취소=레드)
ws.conditional_formatting.add(f'O3:O{last_row}',
    CellIsRule(operator='equal', formula=['"완료"'],
        fill=PatternFill('solid', start_color="C6EFCE"),
        font=Font(name=FONT_NAME, size=10, bold=True, color="006100")))

# VIP 강조
ws.conditional_formatting.add(f'R3:R{last_row}',
    FormulaRule(formula=[f'$R3="⭐ VIP"'],
        fill=PatternFill('solid', start_color="FFF2CC"),
        font=Font(name=FONT_NAME, size=10, bold=True, color="BF8F00")))

# 지연 강조
ws.conditional_formatting.add(f'S3:S{last_row}',
    FormulaRule(formula=[f'LEFT($S3,1)="⚠"'],
        fill=PatternFill('solid', start_color="FCE4D6"),
        font=Font(name=FONT_NAME, size=10, bold=True, color="C00000")))
```
