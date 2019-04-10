import pandas as pd

url = 'http://www.jfl.or.jp/jfl-pc/view/s.php?a=1411&f=2019A001_spc.html'
dfs = pd.read_html(url, skiprows=1, na_values='-')

len(dfs)

df = pd.concat(
    dfs, keys=[i for i in range(1,
                                len(dfs) + 1)], names=['節', '番号'])
df.columns = ['日にち', '時間', 'ホーム', 'スコア', 'アウェイ', 'スタジアム', '備考']
df.drop('備考', axis=1, inplace=True)
df.head(10)

# 欠損値確認
df[df.isnull().any(axis=1)]

# スコアがないものを除去
df1 = df.dropna(subset=['スコア'])

# スコアを分割、スコアを削除、結合
df2 = pd.concat(
    [df1, df1['スコア'].str.split('-', expand=True)], axis=1).drop(
        'スコア', axis=1)

# 名前をホーム得点、アウェイ得点に変更
df2.rename(columns={0: 'ホーム得点', 1: 'アウェイ得点'}, inplace=True)

# ホーム得点、アウェイ得点を文字から整数に変更
df2['ホーム得点'] = df2['ホーム得点'].astype(int)
df2['アウェイ得点'] = df2['アウェイ得点'].astype(int)
df2.dtypes

# ホームの結果のみ
df_home = df2.loc[:, ['ホーム', 'ホーム得点', 'アウェイ得点']].reindex()
df_home.columns = ['チーム名', '得点', '失点']
df_home['戦'] = 'ホーム'
df_home.head()

# アウェイの結果のみ
df_away = df2.loc[:, ['アウェイ', 'アウェイ得点', 'ホーム得点']]
df_away.columns = ['チーム名', '得点', '失点']
df_away['戦'] = 'アウェイ'
df_away.head()

# ホームとアウェイを結合
df_total = pd.concat([df_home, df_away])

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
pv_wl = df_total.pivot_table(
    values='カウント',
    index='チーム名',
    columns=['戦', '勝敗'],
    aggfunc=sum,
    fill_value=0)
pv_wl

# 列名変更
pv_wl.columns = ['勝利A', '引分A', '敗戦A', '勝利H', '引分H', '敗戦H']

# 合計追加
pv_wl['勝利'] = pv_wl['勝利H'] + pv_wl['勝利A']
pv_wl['引分'] = pv_wl['引分H'] + pv_wl['引分A']
pv_wl['敗戦'] = pv_wl['敗戦H'] + pv_wl['敗戦A']

# 試合数追加
pv_wl['試合数'] = pv_wl['勝利'] + pv_wl['引分'] + pv_wl['敗戦']

# 確認
pv_wl

df3 = df_total.pivot_table(
    values='勝点', index='チーム名', columns='節', aggfunc=sum, fill_value=0)
df3

df_wp = df3.apply(lambda d: d.cumsum(), axis=1)
df_wp

df4 = df_total.copy()

# 評価値を作成
df4['評価値'] = (df4['勝点'] * 10000) + (df4['得失点'] * 100) + df4['得点']
df4

# 評価値集計
df5 = df4.pivot_table(
    values='評価値', index='チーム名', columns='節', aggfunc=sum, fill_value=0)
df5

# 累計評価値
df_eval = df5.apply(lambda d: d.cumsum(), axis=1)
df_eval

# 累計評価値をランキングに変換
df_chart = df_eval.rank(ascending=False, method='min').astype(int)
df_chart

# 前ランキングとの差分
df6 = df_chart.copy()
df_diff = df6.diff(axis=1).fillna(0)


def arrow_up(x):
    if x > 0:
        return '▼'
    elif x < 0:
        return '▲'
    else:
        return '－'


s1 = df_diff.iloc[:, -1].apply(lambda x: arrow_up(x))
s1.name = '前節'

df7 = pd.concat([pv_score, pv_wl], axis=1).join(s1)

# 評価値を作成
df7['評価値'] = (df7['勝点'] * 10000) + (df7['得失点'] * 100) + df7['得点']

# ランキング
df7['順位'] = df7['評価値'].rank(ascending=False, method='min').astype(int)

# 順位で昇順
df7.sort_values(['順位'], inplace=True)

df7

# チーム名をインデックスから解除
df8 = df7.reset_index()
df_rank = df8.loc[:, [
    '前節', '順位', 'チーム名', '勝点', '試合数', '勝利', '勝利H', '勝利A', '引分', '引分H', '引分A',
    '敗戦', '敗戦H', '敗戦A', '得失点', '得点', '失点'
]]

df_rank

df_rank.to_excel('2019_ranking.xlsx', sheet_name='ランキング', index=False)
