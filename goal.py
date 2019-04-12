import csv
import time
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


def cleaning(info, team, data):

    result = []

    for trs in data:

        temp = [i.get_text(strip=True) for i in trs.select('th, td')]

        # 時間の分を除去後、延長時間を計算
        temp[0] = eval(temp[0].rstrip('分'))

        # 選手名のPKを削除
        temp[2] = temp[2].replace('(PK)', '').strip()

        result.append(info + [team] + temp)

    return result


def scraping(n, url):

    r = requests.get(url)

    if r.status_code == requests.codes.ok:

        soup = BeautifulSoup(r.content, 'html5lib')

        # シーズン・節
        score_season = soup.select_one(
            'div.score-header > h2.score-meta > span.score-season').get_text(
                strip=True)

        # 節
        score_season = score_season.strip('第節')

        # print(score_season)

        # 日時
        score_date = soup.select_one(
            'div.score-header > h2.score-meta > span.score-date').get_text(
                strip=True).split()

        # print(score_date)

        # チーム名
        score_table = soup.select_one('table.score-table')

        home_team = score_table.select_one('th.score-team1').get_text(
            strip=True)
        away_team = score_table.select_one('th.score-team2').get_text(
            strip=True)

        # print(home_team, away_team)

        # 試合情報
        game_info = [n, score_season] + score_date + [home_team, away_team]

        # 得点
        for i in soup.select('div.section > h3'):

            # 得点のテーブルか確認
            if i.text == '得　点':

                table = [
                    trs for trs in i.parent.select(
                        'div.score-frame > div.score-left > table > tbody > tr'
                    )
                ]
                home_data = cleaning(game_info, home_team, table)

                table = [
                    trs for trs in i.parent.select(
                        'div.score-frame > div.score-right > table > tbody > tr'
                    )
                ]
                away_data = cleaning(game_info, away_team, table)

                score_data = home_data + away_data

                return (score_data)

        return None


if __name__ == "__main__":

    url = 'http://www.jfl.or.jp/jfl-pc/view/s.php?a=1411&f=2019A001_spc.html'

    r = requests.get(url)

    if r.status_code == requests.codes.ok:

        soup = BeautifulSoup(r.content, 'html5lib')

        with open('result.csv', 'w') as fw:
            writer = csv.writer(fw, dialect='excel', lineterminator='\n')

            # ヘッダー
            writer.writerow([
                '試合', '節', '日付', '時刻', 'ホーム', 'アウェイ', 'チーム名', '時間', '背番号',
                '選手名'
            ])

            n = 0

            for link in soup.select('td.detail-link > a'):

                # 詳細のリンクか確認
                if link.text == '詳細':

                    n += 1

                    spc_url = urljoin(url, link.get('href'))

                    # 詳細をスクレイピング
                    score_data = scraping(n, spc_url)

                    # CSVに保存
                    if score_data:
                        writer.writerows(score_data)

                    # 3秒待機
                    time.sleep(3)

        df = pd.read_csv('result.csv')

        df['得点'] = 1

        # ゴール数ランキング
        pv_goal = df.pivot_table(
            values='得点',
            index=['選手名', 'チーム名', '背番号'],
            aggfunc=sum,
            fill_value=0)

        pv_goal = pv_goal.reset_index()

        # オウンゴールを削除
        pv_goal.drop(pv_goal.index[pv_goal['選手名'] == 'オウンゴール'], inplace=True)
        pv_goal['背番号'] = pv_goal['背番号'].astype(int)

        # ランキング
        pv_goal['順位'] = pv_goal['得点'].rank(
            ascending=False, method='min').astype(int)

        # チーム
        jfl_2019 = [
            'Ｈｏｎｄａ ＦＣ', 'ＦＣ大阪', 'ソニー仙台ＦＣ', 'ＦＣ今治', '東京武蔵野シティＦＣ', 'ＭＩＯびわこ滋賀',
            '奈良クラブ', 'ヴェルスパ大分', 'ラインメール青森', 'ヴィアティン三重', 'テゲバジャーロ宮崎',
            'ＦＣマルヤス岡崎', 'ホンダロックＳＣ', '流経大ドラゴンズ龍ケ崎', '松江シティＦＣ', '鈴鹿アンリミテッド'
        ]

        team = {name: i for i, name in enumerate(jfl_2019, 1)}

        pv_goal['チームID'] = pv_goal['チーム名'].map(team)

        # 順位・チーム名・選手名で昇順
        pv_goal.sort_values(
            ['順位', 'チームID', '背番号'], ascending=[True, True, True], inplace=True)

        pv_goal.drop(['チームID', '背番号'], axis=1, inplace=True)

        pv_goal.set_index('順位', inplace=True)

        pv_goal.to_excel('2019_goal.xlsx', sheet_name='ランキング')
