from fastapi import FastAPI
from typing import List
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# 팀 최근 10경기 크롤링
def get_recent_games(team_name: str) -> List[str]:
    url = f"http://www.statiz.co.kr/team.php?opt=3&name={team_name}"
    res = requests.get(url)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, "html.parser")

    game_rows = soup.select("table tbody tr")[:10]
    results = []

    for row in game_rows:
        cols = row.find_all("td")
        if len(cols) >= 4:
            date = cols[0].text.strip()
            opponent = cols[1].text.strip()
            score = cols[2].text.strip()
            result = cols[3].text.strip()
            results.append(f"{date} - {opponent}전 결과: {score} ({result})")
    return results

# 오늘 경기 선발투수 (간단 대체 버전 - 네이버 모바일)
def get_today_pitchers():
    url = "https://m.sports.naver.com/kbaseball/record/index"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, "html.parser")

    results = []
    matches = soup.select(".Home_match__item")
    for match in matches:
        try:
            title = match.select_one(".Home_match__title").text.strip()
            info = match.select_one(".Home_match__info").text.strip()
            results.append({"경기": title, "정보": info})
        except:
            continue
    return results

# 투타 통산 상대전적
def get_pitcher_vs_batter(pitcher_name: str, batter_name: str) -> dict:
    url = f"http://www.statiz.co.kr/versus.php?m=player&pitcher={pitcher_name}&batter={batter_name}"
    res = requests.get(url)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')

    table = soup.select_one("table")
    if not table:
        return {"message": "데이터를 찾을 수 없습니다."}

    rows = table.select("tbody tr")
    if not rows:
        return {"message": "통산 상대전적이 없습니다."}

    data = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 8:
            season = cols[0].text.strip()
            ab = cols[2].text.strip()
            hits = cols[3].text.strip()
            hr = cols[6].text.strip()
            avg = cols[7].text.strip()
            data.append({
                "시즌": season,
                "타석": ab,
                "안타": hits,
                "홈런": hr,
                "타율": avg
            })

    return {
        "pitcher": pitcher_name,
        "batter": batter_name,
        "records": data
    }

# 룰 설명용 사전
rule_explanations = {
    "보크": {
        "설명": "보크는 투수가 부정확한 동작으로 주자를 속일 때 선언되는 반칙입니다.",
        "링크": "https://www.youtube.com/watch?v=U6SwH5KxiFg"
    },
    "쓰리피트 아웃": {
        "설명": "주자가 베이스 러닝 라인을 벗어나 야수를 피하면 아웃입니다.",
        "링크": "https://www.youtube.com/watch?v=sjPCk1TO0gQ"
    },
    "인필드플라이": {
        "설명": "내야수가 쉽게 잡는 뜬공일 경우 자동 아웃을 선언합니다.",
        "링크": "https://www.youtube.com/watch?v=3MCP6ZkOJ2k"
    },
    "비디오판독": {
        "설명": "판정을 영상으로 재확인하는 절차입니다.",
        "링크": "https://www.youtube.com/watch?v=JXzHTZcpZxc"
    }
}

@app.get("/recent-games/{team_name}")
def recent_games(team_name: str):
    return {"team": team_name, "recent_games": get_recent_games(team_name)}

@app.get("/today-games")
def today_games():
    return {"today_games": get_today_pitchers()}

@app.get("/vs-record")
def vs_record(pitcher: str, batter: str):
    return get_pitcher_vs_batter(pitcher, batter)

@app.get("/rule/{keyword}")
def explain_rule(keyword: str):
    info = rule_explanations.get(keyword)
    if not info:
        return {"message": "해당 룰 설명을 찾을 수 없습니다."}
    return info
