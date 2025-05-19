import requests
import sys
import shlex
from functools import lru_cache

def fetch_data(url, headers):
    """Запрос данных с сервера с обработкой ошибок."""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ошибка запроса: {e}")

def get_player_name(player_data):
    """Формирование полного имени игрока."""
    name = player_data.get('name', '').strip()
    surname = player_data.get('surname', '').strip()
    full_name = f"{name} {surname}".strip()
    return full_name if full_name else f"Unnamed Player {player_data['id']}"

def main():
    token = "cc3fa7b16889cb00bd32ecb2ca5dfad74b9b26fdafdbfa794b93a6b9437667e9"
    headers = {'Authorization': token}
    base_url = "https://lksh-enter.ru"

    try:
        # Загрузка данных
        teams = fetch_data(f"{base_url}/teams", headers)
        matches = fetch_data(f"{base_url}/matches", headers)
        team_by_name = {team['name']: team for team in teams}
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

    # Сбор уникальных игроков
    player_cache = {}
    all_players = set()

    for team in teams:
        for player_id in team['players']:
            if player_id not in player_cache:
                try:
                    player = fetch_data(f"{base_url}/players/{player_id}", headers)
                    player_cache[player_id] = get_player_name(player)
                except:
                    continue
            all_players.add(player_cache[player_id])

    # Вывод отсортированного списка
    for name in sorted(all_players, key=lambda x: x.lower()):
        print(name)

    # Обработка запросов
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        if line.startswith('stats? '):
            try:
                parts = shlex.split(line[len('stats? '):])
                team_name = parts[0]
                team = team_by_name.get(team_name)
            except:
                print("0 0 0")
                continue

            if not team:
                print("0 0 0")
                continue

            wins = losses = goals_scored = goals_conceded = 0
            for match in matches:
                if match['team1'] == team['id']:
                    goals_scored += match['team1_score']
                    goals_conceded += match['team2_score']
                    if match['team1_score'] > match['team2_score']:
                        wins += 1
                    elif match['team1_score'] < match['team2_score']:
                        losses += 1
                elif match['team2'] == team['id']:
                    goals_scored += match['team2_score']
                    goals_conceded += match['team1_score']
                    if match['team2_score'] > match['team1_score']:
                        wins += 1
                    elif match['team2_score'] < match['team1_score']:
                        losses += 1

            print(f"{wins} {losses} {goals_scored - goals_conceded:+}")

        elif line.startswith('versus? '):
            parts = line[len('versus? '):].split()
            if len(parts) != 2:
                print(0)
                continue

            try:
                p1, p2 = map(int, parts)
                p1_teams = {t['id'] for t in teams if p1 in t['players']}
                p2_teams = {t['id'] for t in teams if p2 in t['players']}
            except:
                print(0)
                continue

            if not p1_teams or not p2_teams:
                print(0)
                continue

            count = 0
            for match in matches:
                t1, t2 = match['team1'], match['team2']
                if (t1 in p1_teams and t2 in p2_teams) or (t2 in p1_teams and t1 in p2_teams):
                    count += 1
            print(count)

        else:
            print("Неизвестный запрос")

if __name__ == "__main__":
    main()