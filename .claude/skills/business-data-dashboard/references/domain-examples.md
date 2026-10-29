# 도메인별 적용 예시

받는 데이터의 컬럼명을 보고 도메인을 자동 판별하고, 그에 맞게 대시보드 용어와 인사이트 톤을 조정한다.

---

## 1. 주문 데이터 (Order Data)

### 컬럼 신호
`주문ID`, `고객`, `주문일자`, `배송일자`, `상품`, `결제수단`

### DOMAIN 설정
```python
DOMAIN = {
    'sheet_name_data': "주문데이터(클렌징)",
    'title': "주문 데이터 분석 대시보드",
    'kpi_revenue_label': "💰 총 매출액 (완료)",
    'kpi_count_label': "📦 총 주문 건수",
    'kpi_avg_label': "💳 평균 주문액",
    'kpi_cancel_label': "⚠️ 취소율",
    'completed_status': "완료",
    'cancelled_status': "취소",
    'in_progress_status': "배송중",
}
```

### 인사이트 톤 (예시)
- "VIP 고객 누적 200만원 이상..."
- "취소율 N% — 단일 건이지만 금액이 큼"
- "현금 결제 고객의 재구매율..."
- "특정 지역 매출 의존도 위험"

---

## 2. 배송 데이터 (Shipping Data)

### 컬럼 신호
`송장번호`, `수령인`, `출발지`, `도착지`, `기사명`, `배송상태`

### DOMAIN 설정
```python
DOMAIN = {
    'sheet_name_data': "배송데이터(클렌징)",
    'title': "배송 운영 분석 대시보드",
    'kpi_revenue_label': "💰 총 운송 매출",
    'kpi_count_label': "📦 총 배송 건수",
    'kpi_avg_label': "💳 평균 운임",
    'kpi_cancel_label': "⚠️ 반송율",
    'completed_status': "배송완료",
    'cancelled_status': "반송",
    'in_progress_status': "배송중",
}
```

### 컬럼 매핑
- 고객 → 수령인
- 담당자 → 기사
- 지역 → 도착지(권역)
- 결제수단 → 운송수단(택배/직배송/퀵)
- 카테고리 → 화물 분류(일반/냉장/위험물)

### 파생 컬럼 변경
- 'VIP여부' → '주요 거래처 여부' (누적 운임 임계값 기준)
- '지연일수' → 약속일 대비 실제 도착일 차이

### 인사이트 톤
- "기사별 처리 효율..."
- "특정 권역 지연율 N% — 거점 추가 검토"
- "냉장 화물 비중 N% — 콜드체인 인프라 투자 ROI"
- "반송 사유 추적..."

---

## 3. 물류 데이터 (Logistics / Warehouse)

### 컬럼 신호
`입고일`, `출고일`, `창고`, `SKU`, `재고`, `로트`

### DOMAIN 설정
```python
DOMAIN = {
    'sheet_name_data': "물류데이터(클렌징)",
    'title': "물류 운영 분석 대시보드",
    'kpi_revenue_label': "💰 총 출고 금액",
    'kpi_count_label': "📦 총 처리 건수",
    'kpi_avg_label': "💳 평균 처리 단가",
    'kpi_cancel_label': "⚠️ 클레임율",
    'completed_status': "출고완료",
    'cancelled_status': "반품",
    'in_progress_status': "보관중",
}
```

### 컬럼 매핑
- 고객 → 출고처 또는 화주
- 담당자 → 작업자
- 지역 → 창고 코드
- 결제수단 → 입출고 구분

### 파생 컬럼 변경
- 'VIP여부' → '핵심 SKU 여부' (회전율 또는 누적 출고량)
- '지연일수' → 보관일수 (입고일~출고일)

### 인사이트 톤
- "재고 회전율 SKU별 편차..."
- "특정 창고 보관일수 평균 N일 — 데드스톡 의심"
- "핵심 SKU 안전재고 미달..."
- "창고별 처리량 격차 — 인력 재배치 필요"

---

## 4. 구매/발주 데이터 (Procurement)

### 컬럼 신호
`발주번호`, `거래처`, `발주일`, `입고예정일`, `단가`, `납기`

### DOMAIN 설정
```python
DOMAIN = {
    'sheet_name_data': "구매데이터(클렌징)",
    'title': "구매 발주 분석 대시보드",
    'kpi_revenue_label': "💰 총 발주 금액",
    'kpi_count_label': "📦 총 발주 건수",
    'kpi_avg_label': "💳 평균 발주액",
    'kpi_cancel_label': "⚠️ 발주 취소율",
    'completed_status': "입고완료",
    'cancelled_status': "발주취소",
    'in_progress_status': "발주진행",
}
```

### 컬럼 매핑
- 고객 → 거래처
- 담당자 → 구매 담당자
- 지역 → 거래처 소재지
- 결제수단 → 결제 조건(현금/어음/외상)

### 파생 컬럼 변경
- 'VIP여부' → '핵심 거래처 여부' (누적 발주액 임계값)
- '지연일수' → 납기 준수 여부 (예정일~실입고일)

### 인사이트 톤
- "거래처 의존도 — 상위 N곳에 X% 집중"
- "납기 준수율 N% — 특정 거래처 리스크"
- "단가 변동 추이 — 시장가 대비 N%"
- "어음 결제 비중과 자금 운영 영향"

---

## 5. 매출 데이터 (Sales)

### 컬럼 신호
`거래일자`, `영업사원`, `채널`, `고객사`, `매출액`

### DOMAIN 설정
```python
DOMAIN = {
    'sheet_name_data': "매출데이터(클렌징)",
    'title': "매출 분석 대시보드",
    'kpi_revenue_label': "💰 총 매출",
    'kpi_count_label': "📦 거래 건수",
    'kpi_avg_label': "💳 평균 거래액",
    'kpi_cancel_label': "⚠️ 환불율",
    'completed_status': "정산완료",
    'cancelled_status': "환불",
    'in_progress_status': "정산예정",
}
```

### 컬럼 매핑
- 고객 → 고객사
- 담당자 → 영업사원
- 지역 → 채널 (온라인/오프라인/B2B/B2C)
- 결제수단 → 정산 방식

### 인사이트 톤
- "영업사원별 실적 격차..."
- "채널별 매출 비중 — 온라인 N% vs 오프라인"
- "VIP 고객사 재구매 패턴..."
- "월간 매출 변동성 — 특정 시점 집중 의존"

---

## 6. 재고 데이터 (Inventory)

### 컬럼 신호
`품목코드`, `현재고`, `안전재고`, `최근입고일`, `최근출고일`

### DOMAIN 설정
```python
DOMAIN = {
    'sheet_name_data': "재고데이터(클렌징)",
    'title': "재고 현황 분석 대시보드",
    'kpi_revenue_label': "💰 총 재고 가치",
    'kpi_count_label': "📦 총 SKU 수",
    'kpi_avg_label': "💳 평균 재고 가치",
    'kpi_cancel_label': "⚠️ 안전재고 미달율",
    'completed_status': "정상",
    'cancelled_status': "단종",
    'in_progress_status': "주의",
}
```

### 인사이트 톤
- "재고 회전율 카테고리별 편차..."
- "안전재고 미달 SKU N개 — 즉시 발주 필요"
- "데드스톡 의심 N개 — 90일 이상 미출고"
- "ABC 분석 결과 A등급 N% / 매출 N% 기여"

---

## 7. CRM / 영업 파이프라인 데이터

### 컬럼 신호
`리드`, `상담일`, `영업단계`, `예상매출`, `전환`

### DOMAIN 설정
```python
DOMAIN = {
    'sheet_name_data': "CRM데이터(클렌징)",
    'title': "영업 파이프라인 분석 대시보드",
    'kpi_revenue_label': "💰 예상 매출 합계",
    'kpi_count_label': "📦 활성 리드 수",
    'kpi_avg_label': "💳 평균 거래 규모",
    'kpi_cancel_label': "⚠️ 이탈율",
    'completed_status': "성공",
    'cancelled_status': "실패",
    'in_progress_status': "진행중",
}
```

### 인사이트 톤
- "단계별 전환율 — 병목 지점 식별..."
- "영업사원별 클로징율 격차..."
- "리드 소스별 ROI..."
- "체류 기간 긴 딜 — 우선 액션 필요"

---

## 도메인 자동 판별 로직

받은 데이터의 컬럼 헤더를 보고 다음 키워드로 자동 매칭:

```python
def detect_domain(headers):
    headers_str = " ".join(str(h) for h in headers).lower()
    
    if any(k in headers_str for k in ['송장', '수령인', '기사', '운송']):
        return 'shipping'
    if any(k in headers_str for k in ['창고', '입고', '출고', '재고', 'sku']):
        return 'logistics'
    if any(k in headers_str for k in ['발주', '거래처', '입고예정', '납기']):
        return 'procurement'
    if any(k in headers_str for k in ['영업사원', '채널', '거래일자']):
        return 'sales'
    if any(k in headers_str for k in ['리드', '영업단계', '전환', '예상매출']):
        return 'crm'
    if any(k in headers_str for k in ['안전재고', '현재고', '품목코드']):
        return 'inventory'
    # 기본값
    return 'order'
```

매칭 실패 시 `order` 도메인으로 처리하되, 사용자에게 도메인 확인을 요청해도 좋다.

---

## 컬럼 수가 다른 데이터 처리

기본 템플릿은 14컬럼(원본) + 6컬럼(파생) = 21컬럼 기준이다. 받은 데이터가 다르면:

- **컬럼이 적을 때**: 없는 정보(예: 이메일 없음)는 클렌징 단계 건너뛰고, 헤더에서 제거. 파생 컬럼 중 해당 정보 의존하는 것(이메일 형식 검증)도 제거.
- **컬럼이 많을 때**: 핵심 14컬럼만 클렌징/파생 적용하고, 나머지는 데이터 시트에 그대로 보존.

받은 데이터에 핵심 5요소(ID, 거래상대, 일자, 금액, 상태)가 모두 있으면 대시보드는 무조건 만들 수 있다. 없으면 사용자에게 추가 정보 요청.
