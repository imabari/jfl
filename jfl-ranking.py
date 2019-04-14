# -*- coding: utf-8 -*-

import pandas as pd

url = 'http://www.jfl.or.jp/jfl-pc/view/s.php?a=1411&f=2019A001_spc.html'

dfs = pd.read_html(url, skiprows=1, na_values='-')

len(dfs)

df = pd.concat(
    dfs, keys=[i for i in range(1,
                                len(dfs) + 1)], names=['節', '番号'])

# 列名を設定
df.columns = ['日にち', '時間', 'ホーム', 'スコア', 'アウェイ', 'スタジアム', '備考']

# 備考を除去
df.drop('備考', axis=1, inplace=True)

# スコアがないものを除去
df.dropna(subset=['スコア'], inplace=True)
df

# スコアを分割
df2 = df['スコア'].str.split('-', expand=True)
df2 = df2.astype(int)
df2.columns = ['ホーム得点', 'アウェイ得点']

# スコアを削除
df1 = df.drop('スコア', axis=1)

# スコアを分割、スコアを削除、結合
df = pd.concat([df, df2], axis=1)
df

df_home = df.loc[:, ['ホーム', 'アウェイ', 'ホーム得点', 'アウェイ得点']].reindex()
df_home.columns = ['チーム名', '対戦相手', '得点', '失点']
df_home['戦'] = 'H'
df_home.head()

df_away = df.loc[:, ['アウェイ', 'ホーム', 'アウェイ得点', 'ホーム得点']]
df_away.columns = ['チーム名', '対戦相手', '得点', '失点']
df_away['戦'] = 'A'
df_away.head()

df_total = pd.concat([df_home, df_away])

df_total

# 得失点を計算
df_total['得失点'] = df_total['得点'] - df_total['失点']
df_total.head()


# 勝敗を追加
def win_or_loss(x):
    if x['得点'] > x['失点']:
        return '勝利'
    elif x['得点'] < x['失点']:
        return '敗戦'
    else:
        return '引分'


df_total['勝敗'] = df_total.apply(lambda x: win_or_loss(x), axis=1)

df_total.head()


# 勝点を追加
def win_point(x):
    if x['得点'] > x['失点']:
        return 3
    elif x['得点'] < x['失点']:
        return 0
    else:
        return 1


df_total['勝点'] = df_total.apply(lambda x: win_point(x), axis=1)
df_total.head()

# 得点・失点・得失点・勝点　集計
pv_score = df_total.pivot_table(
    values=['得点', '失点', '得失点', '勝点'], index='チーム名', aggfunc=sum)
pv_score.head()

# 集計用にカウント追加
df_total['カウント'] = 1

# 得点・失点・得失点・勝点　集計
pv_wlcnt = df_total.pivot_table(
    values='カウント',
    index='チーム名',
    columns=['戦', '勝敗'],
    aggfunc=sum,
    fill_value=0)
pv_wlcnt

# 列名変更
pv_wlcnt.columns = ['勝利A', '引分A', '敗戦A', '勝利H', '引分H', '敗戦H']

# 合計追加
pv_wlcnt['勝利'] = pv_wlcnt['勝利H'] + pv_wlcnt['勝利A']
pv_wlcnt['引分'] = pv_wlcnt['引分H'] + pv_wlcnt['引分A']
pv_wlcnt['敗戦'] = pv_wlcnt['敗戦H'] + pv_wlcnt['敗戦A']

# 試合数追加
pv_wlcnt['試合数'] = pv_wlcnt['勝利'] + pv_wlcnt['引分'] + pv_wlcnt['敗戦']

# 確認
pv_wlcnt

df3 = df_total.copy()

# 評価値を作成
df3['評価値'] = (df3['勝点'] * 10000) + (df3['得失点'] * 100) + df3['得点']
df3

# 評価値集計
pv_eval = df3.pivot_table(
    values='評価値', index='チーム名', columns='節', aggfunc=sum, fill_value=0)
pv_eval

# 累計評価値
pvc_eval = pv_eval.apply(lambda d: d.cumsum(), axis=1)
pvc_eval

# 累計評価値をランキングに変換
df_rank = pvc_eval.rank(ascending=False, method='min').astype(int)
df_rank

# 前ランキングとの差分
df4 = df_rank.copy()
df_diff = df4.diff(axis=1).fillna(0)


# 差分を三角に変換
def arrow_up(x):
    if x > 0:
        return '▼'
    elif x < 0:
        return '▲'
    else:
        return '－'


s1 = df_diff.iloc[:, -1].apply(lambda x: arrow_up(x))
s1.name = '前節'
s1

df5 = pd.concat([pv_score, pv_wlcnt], axis=1).join(s1)
df5

# 評価値を作成
df5['評価値'] = (df5['勝点'] * 10000) + (df5['得失点'] * 100) + df5['得点']

# ランキング
df5['順位'] = df5['評価値'].rank(ascending=False, method='min').astype(int)

# 順位で昇順
df5.sort_values(['順位'], inplace=True)

df5

# チーム名をインデックスから解除
df6 = df5.reset_index()
jfl_rank = df6.loc[:, [
    '前節', '順位', 'チーム名', '勝点', '試合数', '勝利', '勝利H', '勝利A', '引分', '引分H', '引分A',
    '敗戦', '敗戦H', '敗戦A', '得失点', '得点', '失点'
]]

jfl_rank


# 結果を追加
def match_result(x):
    if x['得点'] > x['失点']:
        return '{}○{}'.format(x['得点'], x['失点'])
    elif x['得点'] < x['失点']:
        return '{}●{}'.format(x['得点'], x['失点'])
    else:
        return '{}△{}'.format(x['得点'], x['失点'])


df_total['結果'] = df_total.apply(lambda x: match_result(x), axis=1)
df_total

# 戦績表　集計
pv_senseki = df_total.pivot_table(
    values='結果',
    index=['チーム名', '戦'],
    columns='対戦相手',
    aggfunc=sum,
    fill_value='')

pv_senseki

jfl_team = [
    'Ｈｏｎｄａ ＦＣ', 'ＦＣ大阪', 'ソニー仙台ＦＣ', 'ＦＣ今治', '東京武蔵野シティＦＣ', 'ＭＩＯびわこ滋賀', '奈良クラブ',
    'ヴェルスパ大分', 'ラインメール青森', 'ヴィアティン三重', 'テゲバジャーロ宮崎', 'ＦＣマルヤス岡崎', 'ホンダロックＳＣ',
    '流経大ドラゴンズ龍ケ崎', '松江シティＦＣ', '鈴鹿アンリミテッド'
]

new_idx = pd.MultiIndex.from_product(
    [jfl_team, ['H', 'A']], names=pv_senseki.index.names)

jfl_senseki = pv_senseki.reindex(new_idx, columns=jfl_team)
jfl_senseki.fillna('', inplace=True)
jfl_senseki

with pd.ExcelWriter('2019_jfl.xlsx') as writer:
    jfl_rank.to_excel(writer, sheet_name='ランキング', index=False)
    jfl_senseki.to_excel(writer, sheet_name='戦績表')
