# 소재 코드와 이름 정보를 담은 상수 리스트
STOCK_ITEMS = [
    {"code": 9, "name": "Aluminum 7075-T6"},
    {"code": 13, "name": "Aluminum 356.0-T6"},
    {"code": 36, "name": "AISI P20 Mold Steel"},
    {"code": 45, "name": "Aluminum 6061-T6"},
    {"code": 52, "name": "Aluminum 7550-T74"},
    {"code": 62, "name": "AISI 4340 Steel"},
    {"code": 75, "name": "Aluminum 7050-T7451 Low Speed V<200 m/min"},
    {"code": 234, "name": "Aluminum 7050-T7451"},
    {"code": 247, "name": "Titanium Alloy Ti6Al4v (orth to Oblq)"},
    {"code": 2174, "name": "AISI P20 Steel - Ballend mill calibrated with"},
    {"code": 2192, "name": "NRC - MDF"},
    {"code": 2266, "name": "Cast Iron C450"},
    {"code": 2315, "name": "Gray cast iron"},
    {"code": 2330, "name": "AISI P20 Steel – Ballend mill a=0.065 in"},
    {"code": 2341, "name": "Inconel 718"},
    {"code": 2359, "name": "Inconel 625"},
    {"code": 2370, "name": "Niobium"},
    {"code": 2383, "name": "Thermo-Span Superalloy"},
    {"code": 2406, "name": "Waspaloy"},
    {"code": 2456, "name": "AISI 630 Steel"},
    {"code": 2480, "name": "AISI 1050 Steel"},
    {"code": 2492, "name": "Aluminum 319.0-T6"},
    {"code": 2504, "name": "Alumec 89"},
]


def get_stock_code_by_name(name: str) -> int | None:
    """
    소재 이름(name)을 입력하면 해당하는 소재 코드(code)를 반환한다.
    일치하는 소재가 없으면 None 반환.
    """
    for item in STOCK_ITEMS:
        if item["name"] == name:
            return item["code"]
    return None
